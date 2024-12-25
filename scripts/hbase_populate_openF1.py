# Import necessary libraries
import multiprocessing
import concurrent.futures
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
import asyncio
import aiohttp
import happybase
import time
from datetime import datetime, timedelta
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import sys
import traceback
from colorama import Fore, Style, init
import logging
from functools import partial

# Initialize colorama for colored console output
init()

# Configure logging to write to a file
logging.basicConfig(
    filename='populate.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Global configuration settings
CONFIG = {
    "max_retries": 3,          # Maximum number of retry attempts for failed requests
    "retry_delay": 5,          # Delay between retries in seconds
    "request_timeout": 60,     # Request timeout in seconds
    "delay_between_requests": 1,  # Delay between consecutive requests
    "max_concurrent_requests": 10,  # Maximum number of concurrent requests
    "time_interval": 900       # Time interval for data collection (15 minutes)
}

# API configuration
BASE_URL = 'https://api.openf1.org/v1'
ENDPOINTS = {
    'meetings': '/meetings',
    'sessions': '/sessions',
    'drivers': '/drivers',
    'car_data': '/car_data',
    'laps': '/laps',
    'intervals': '/intervals',
    'position': '/position',
    'race_control': '/race_control',
    'stints': '/stints',
    'team_radio': '/team_radio',
    'weather': '/weather',
    'pit': '/pit',
    'location': '/location'
}

# Endpoint classifications for different data types
TIME_SERIES_ENDPOINTS = ['car_data', 'location']
DRIVER_SPECIFIC_ENDPOINTS = ['car_data', 'intervals', 'laps', 'location', 'pit', 'position', 'stints', 'team_radio']
GLOBAL_ENDPOINTS = ['drivers', 'race_control', 'weather']

@dataclass
class Stats:
    """Class for tracking statistics during data collection"""
    meetings_processed: int = 0
    sessions_processed: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    start_time: float = 0
    endpoint_stats: Dict[str, Dict[str, int]] = None

    def __post_init__(self):
        """Initialize endpoint statistics after class initialization"""
        if self.endpoint_stats is None:
            self.endpoint_stats = {
                endpoint: {"success": 0, "failed": 0}
                for endpoint in ENDPOINTS.keys()
            }

class Logger:
    """Custom logger class for formatted console output"""
    
    @staticmethod
    def info(message: str):
        """Log information messages"""
        logging.info(message)
        print(f"{Fore.BLUE}ℹ️ INFO: {message}{Style.RESET_ALL}")

    @staticmethod
    def success(message: str):
        """Log success messages"""
        logging.info(message)
        print(f"{Fore.GREEN}✅ SUCCESS: {message}{Style.RESET_ALL}")

    @staticmethod
    def error(message: str):
        """Log error messages"""
        logging.error(message)
        print(f"{Fore.RED}❌ ERROR: {message}{Style.RESET_ALL}")

    @staticmethod
    def warning(message: str):
        """Log warning messages"""
        logging.warning(message)
        print(f"{Fore.YELLOW}⚠️ WARNING: {message}{Style.RESET_ALL}")

    @staticmethod
    def progress(message: str):
        """Log progress messages"""
        logging.info(message)
        print(f"{Fore.CYAN}🔄 PROGRESS: {message}{Style.RESET_ALL}")

    @staticmethod
    def stats(message: str):
        """Log statistics messages"""
        logging.info(message)
        print(f"{Fore.MAGENTA}📊 STATS: {message}{Style.RESET_ALL}")

    @staticmethod
    def separator():
        """Print a separator line"""
        logging.info("━" * 50)
        print(f"{Fore.WHITE}{'━' * 50}{Style.RESET_ALL}")

class RequestQueue:
    """Handles async HTTP requests with rate limiting and retries"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(CONFIG['max_concurrent_requests'])
        self.stats = Stats()

    async def initialize(self):
        """Initialize aiohttp session"""
        timeout = aiohttp.ClientTimeout(total=CONFIG['request_timeout'])
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()

    async def make_request(self, url: str) -> Dict[str, Any]:
        """Make HTTP request with retry logic and rate limiting"""
        endpoint = url.split('/v1')[1].split('?')[0].split('/')[1]

        async with self.semaphore:
            for attempt in range(CONFIG['max_retries']):
                try:
                    Logger.info(f"Making request (attempt {attempt + 1}/{CONFIG['max_retries']}): {url}")
                    async with self.session.get(url) as response:
                        # Handle rate limiting
                        if response.status == 429:
                            retry_after = int(response.headers.get('Retry-After', CONFIG['retry_delay']))
                            Logger.warning(f"Rate limit hit. Waiting {retry_after} seconds...")
                            await asyncio.sleep(retry_after)
                            continue

                        response.raise_for_status()
                        data = await response.json()
                        self.stats.total_requests += 1
                        self.stats.endpoint_stats[endpoint]['success'] += 1
                        Logger.success(f"Received data: {len(data) if isinstance(data, list) else 1} items")
                        return data

                except (asyncio.TimeoutError, aiohttp.ClientConnectionError, aiohttp.ClientError) as e:
                    Logger.error(f"Request error (attempt {attempt + 1}/{CONFIG['max_retries']}) for {url}: {str(e)}")

                if attempt < CONFIG['max_retries'] - 1:
                    await asyncio.sleep(CONFIG['retry_delay'])

            self.stats.failed_requests += 1
            Logger.error(f"Failed after {CONFIG['max_retries']} attempts for {url}")
            raise Exception(f"Failed after {CONFIG['max_retries']} attempts")


class HBaseConnector:
    """Handles connections and operations with HBase database"""
    
    def __init__(self, host='localhost', port=9090, initialize_tables=False):
        """
        Initialize HBase connection
        
        Args:
            host (str): HBase host address
            port (int): HBase port number
            initialize_tables (bool): Whether to initialize database tables
        """
        self.connection = happybase.Connection(host=host, port=port)
        if initialize_tables:
            self.initialize_tables()

    def initialize_tables(self):
        """
        Initialize HBase tables with appropriate column families.
        Creates two tables:
        - f1_data: Stores all F1 racing data
        - f1_reports: Stores metadata, statistics and error reports
        """
        try:
            # Remove existing tables if they exist
            existing_tables = self.connection.tables()
            if b'f1_data' in existing_tables:
                self.connection.delete_table('f1_data', disable=True)
            if b'f1_reports' in existing_tables:
                self.connection.delete_table('f1_reports', disable=True)

            # Create main data table with column families
            self.connection.create_table(
                'f1_data',
                {
                    'car': dict(),
                    'driver': dict(),
                    'intervals': dict(),
                    'laps': dict(),
                    'location': dict(),
                    'meeting': dict(),
                    'pit': dict(),
                    'position': dict(),
                    'racecontrol': dict(),
                    'session': dict(),
                    'stints': dict(),
                    'teamradio': dict(),
                    'weather': dict()
                }
            )

            # Create reports table
            self.connection.create_table(
                'f1_reports',
                {
                    'meta': dict(),
                    'stats': dict(),
                    'errors': dict()
                }
            )

            Logger.success("HBase tables initialized successfully")
        except Exception as e:
            Logger.error(f"Error initializing tables: {str(e)}")
            raise

    def store_data(self, table: str, row_key: str, data: Dict[str, Any],
                   column_family: str, metadata: Optional[Dict] = None):
        """
        Store data in HBase table
        
        Args:
            table (str): Table name
            row_key (str): Unique row identifier
            data (Dict): Data to store
            column_family (str): Column family name
            metadata (Dict, optional): Additional metadata to store
        """
        try:
            table_obj = self.connection.table(table)
            column_family = column_family.replace('_', '').lower()
            
            # Convert data values to string and encode
            columns = {
                f"{column_family}:{key}".encode(): str(value).encode()
                for key, value in data.items()
            }

            # Add metadata if provided
            if metadata:
                columns.update({
                    f"{column_family}:_meta_{key}".encode(): str(value).encode()
                    for key, value in metadata.items()
                })

            table_obj.put(row_key.encode(), columns)

        except Exception as e:
            Logger.error(f"Error storing data in HBase: {str(e)}")
            raise

class F1DataCollector:
    """Main class for collecting F1 racing data"""
    
    def __init__(self, hbase_host='localhost', hbase_port=9090, initialize_tables=False):
        """
        Initialize data collector with HBase connection
        
        Args:
            hbase_host (str): HBase host address
            hbase_port (int): HBase port number
            initialize_tables (bool): Whether to initialize database tables
        """
        self.stats = Stats()
        self.queue = RequestQueue()
        self.hbase = HBaseConnector(hbase_host, hbase_port, initialize_tables)
        self.stats.start_time = time.time()

    def generate_row_key(self, *components) -> str:
        """Generate unique row key by joining components with '#'"""
        return "#".join(map(str, components))

    async def fetch_time_series_data(self, year: int, meeting_key: int, session_key: int,
                                   driver_number: int, endpoint: str) -> None:
        """
        Fetch time series data for a specific driver and session
        
        Args:
            year (int): Racing year
            meeting_key (int): Meeting identifier
            session_key (int): Session identifier
            driver_number (int): Driver's number
            endpoint (str): API endpoint name
        """
        try:
            # Get session timing information
            session_info = await self.queue.make_request(f"{BASE_URL}/sessions?session_key={session_key}")
            if not session_info:
                return

            # Parse session start and end times
            session_start = datetime.fromisoformat(session_info[0]['date_start'].replace('Z', '+00:00'))
            session_end = datetime.fromisoformat(session_info[0]['date_end'].replace('Z', '+00:00'))

            current_time = session_start
            chunk_count = 0

            # Collect data in time intervals
            while current_time < session_end:
                next_time = min(current_time + timedelta(seconds=CONFIG['time_interval']), session_end)

                # Construct API URL with time window
                url = (f"{BASE_URL}{ENDPOINTS[endpoint]}?"
                      f"session_key={session_key}&"
                      f"driver_number={driver_number}&"
                      f"date>={current_time.isoformat()}&"
                      f"date<{next_time.isoformat()}")

                try:
                    data = await self.queue.make_request(url)
                    if data:
                        # Store each data point
                        for item in data:
                            row_key = self.generate_row_key(
                                year, meeting_key, session_key,
                                driver_number, item['date']
                            )
                            self.hbase.store_data(
                                'f1_data',
                                row_key,
                                item,
                                'car' if endpoint == 'car_data' else endpoint.replace('_', ''),
                                {
                                    'chunk_index': chunk_count,
                                    'time_window_start': current_time.isoformat(),
                                    'time_window_end': next_time.isoformat()
                                }
                            )

                        chunk_count += 1

                except Exception as e:
                    Logger.error(f"Error processing {endpoint} chunk: {str(e)}")

                current_time = next_time
                await asyncio.sleep(CONFIG['delay_between_requests'])

        except Exception as e:
            Logger.error(f"Error fetching time series data: {str(e)}")
            raise

    async def process_session(self, year: int, meeting_key: int, session: Dict[str, Any]):
        """
        Process a single racing session
        
        Args:
            year (int): Racing year
            meeting_key (int): Meeting identifier
            session (Dict): Session data
        """
        try:
            session_key = session['session_key']
            Logger.progress(f"Processing session {session['session_name']}")

            # Store session data
            row_key = self.generate_row_key(year, meeting_key, session_key)
            self.hbase.store_data('f1_data', row_key, session, 'session')

            # Get list of drivers in the session
            drivers = await self.queue.make_request(f"{BASE_URL}/drivers?session_key={session_key}")

            # Process global endpoints (not driver-specific)
            for endpoint in GLOBAL_ENDPOINTS:
                if endpoint != 'drivers':
                    data = await self.queue.make_request(f"{BASE_URL}{ENDPOINTS[endpoint]}?session_key={session_key}")
                    if data:
                        endpoint_key = self.generate_row_key(year, meeting_key, session_key, endpoint)
                        self.hbase.store_data('f1_data', endpoint_key, {'data': data}, endpoint.replace('_', ''))
                    await asyncio.sleep(CONFIG['delay_between_requests'])

            # Process driver-specific data
            for driver in drivers:
                driver_number = driver['driver_number']
                Logger.progress(f"Processing driver {driver_number}")

                # Handle time series data
                for endpoint in TIME_SERIES_ENDPOINTS:
                    await self.fetch_time_series_data(
                        year, meeting_key, session_key, driver_number, endpoint
                    )
                    await asyncio.sleep(CONFIG['delay_between_requests'])

                # Handle other driver-specific endpoints
                for endpoint in DRIVER_SPECIFIC_ENDPOINTS:
                    if endpoint not in TIME_SERIES_ENDPOINTS:
                        data = await self.queue.make_request(
                            f"{BASE_URL}{ENDPOINTS[endpoint]}?"
                            f"session_key={session_key}&driver_number={driver_number}"
                        )
                        if data:
                            column_family = endpoint.replace('_', '')
                            for item in data:
                                row_key = self.generate_row_key(
                                    year, meeting_key, session_key, driver_number, 
                                    item.get('lap_number') or item.get('time')
                                )
                                self.hbase.store_data('f1_data', row_key, item, column_family)
                        await asyncio.sleep(CONFIG['delay_between_requests'])

            self.stats.sessions_processed += 1

        except Exception as e:
            Logger.error(f"Error processing session: {str(e)}")
            raise

class ParallelF1DataCollector:
    """Handles parallel processing of F1 data collection"""
    
    def __init__(self, hbase_host='localhost', hbase_port=9090, num_processes=None):
        """
        Initialize parallel collector
        
        Args:
            hbase_host (str): HBase host address
            hbase_port (int): HBase port number
            num_processes (int, optional): Number of parallel processes
        """
        self.stats = Stats()
        self.hbase_host = hbase_host
        self.hbase_port = hbase_port
        self.num_processes = num_processes or multiprocessing.cpu_count()
        self.stats.start_time = time.time()
        
        # Initialize HBase tables in main process
        self.main_collector = F1DataCollector(hbase_host, hbase_port, initialize_tables=True)

    def display_stats(self):
        """Display current execution statistics"""
        elapsed_time = time.time() - self.stats.start_time
        hours, remainder = divmod(int(elapsed_time), 3600)
        minutes, seconds = divmod(remainder, 60)

        Logger.separator()
        Logger.stats(f"Time elapsed: {hours}h {minutes}m {seconds}s")
        Logger.stats(f"Meetings processed: {self.stats.meetings_processed}")
        Logger.stats(f"Sessions processed: {self.stats.sessions_processed}")
        Logger.stats(f"Total requests: {self.stats.total_requests}")
        Logger.stats(f"Failed requests: {self.stats.failed_requests}")
        Logger.stats(f"Number of processes: {self.num_processes}")

        Logger.stats("\nEndpoint statistics:")
        for endpoint, stats in self.stats.endpoint_stats.items():
            print(f"{Fore.MAGENTA}  {endpoint}:")
            print(f"    Success: {stats['success']}")
            print(f"    Failed: {stats['failed']}{Style.RESET_ALL}")

    async def process_year_parallel(self, year: int):
        """
        Process a complete racing year in parallel
        
        Args:
            year (int): Racing year to process
        """
        temp_collector = F1DataCollector(self.hbase_host, self.hbase_port, initialize_tables=False)
        await temp_collector.queue.initialize()
        
        try:
            meetings = await temp_collector.fetch_meetings(year)
            
            # Process meetings in parallel using ProcessPoolExecutor
            with ProcessPoolExecutor(max_workers=self.num_processes) as executor:
                futures = []
                for meeting in meetings:
                    future = executor.submit(
                        process_meeting_sync,
                        year,
                        meeting,
                        self.hbase_host,
                        self.hbase_port
                    )
                    futures.append(future)
                
                # Collect results and update statistics
                for future in concurrent.futures.as_completed(futures):
                    try:
                        stats = future.result()
                        self.stats.meetings_processed += stats["meetings_processed"]
                        self.stats.sessions_processed += stats["sessions_processed"]
                        self.stats.total_requests += stats["total_requests"]
                        self.stats.failed_requests += stats["failed_requests"]
                        
                        for endpoint, values in stats["endpoint_stats"].items():
                            self.stats.endpoint_stats[endpoint]["success"] += values["success"]
                            self.stats.endpoint_stats[endpoint]["failed"] += values["failed"]
                    
                    except Exception as e:
                        Logger.error(f"Error processing meeting: {str(e)}")
            
        finally:
            await temp_collector.queue.close()

    async def run(self):
        """Main execution method"""
        try:
            Logger.info(f"Initializing parallel F1 data collection with {self.num_processes} processes")
            
            # Process multiple years
            years = [2023, 2024]
            for year in years:
                await self.process_year_parallel(year)
                if year != years[-1]:
                    Logger.info("Waiting 5 seconds before processing next year...")
                    await asyncio.sleep(5)
            
            Logger.success("Data collection completed successfully!")
            self.display_stats()
            
        except Exception as e:
            Logger.error(f"Critical error during execution: {str(e)}")
            Logger.error(traceback.format_exc())
            raise

async def main():
    """Entry point of the script"""
    collector = None
    try:
        # Initialize and run parallel collector
        collector = ParallelF1DataCollector(num_processes=10)
        await collector.run()

    except KeyboardInterrupt:
        Logger.warning("\nUser interruption detected!")
        if collector:
            collector.display_stats()

    except Exception as e:
        Logger.error(f"Unhandled error: {str(e)}")
        Logger.error(traceback.format_exc())
        if collector:
            collector.display_stats()
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Run main async function
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        Logger.error(f"Error in main loop: {str(e)}")
        sys.exit(1)
    finally:
        loop.close()