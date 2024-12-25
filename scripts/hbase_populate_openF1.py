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

# Initialize colorama
init()

logging.basicConfig(filename='populate.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
CONFIG = {
    "max_retries": 3,
    "retry_delay": 5,
    "request_timeout": 60,
    "delay_between_requests": 1,
    "max_concurrent_requests": 10,
    "time_interval": 900  # 15 minutes in seconds
}

# API Configuration
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
# Endpoint Classifications
TIME_SERIES_ENDPOINTS = ['car_data', 'location']
DRIVER_SPECIFIC_ENDPOINTS = ['car_data', 'intervals', 'laps', 'location', 'pit', 'position', 'stints', 'team_radio']
GLOBAL_ENDPOINTS = ['drivers', 'race_control', 'weather']

@dataclass
class Stats:
    meetings_processed: int = 0
    sessions_processed: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    start_time: float = 0
    endpoint_stats: Dict[str, Dict[str, int]] = None

    def __post_init__(self):
        if self.endpoint_stats is None:
            self.endpoint_stats = {
                endpoint: {"success": 0, "failed": 0}
                for endpoint in ENDPOINTS.keys()
            }

class Logger:
    @staticmethod
    def info(message: str):
        logging.info(message)
        print(f"{Fore.BLUE}ℹ️ INFO: {message}{Style.RESET_ALL}")

    @staticmethod
    def success(message: str):
        logging.info(message)
        print(f"{Fore.GREEN}✅ SUCCESS: {message}{Style.RESET_ALL}")

    @staticmethod
    def error(message: str):
        logging.error(message)
        print(f"{Fore.RED}❌ ERROR: {message}{Style.RESET_ALL}")

    @staticmethod
    def warning(message: str):
        logging.warning(message)
        print(f"{Fore.YELLOW}⚠️ WARNING: {message}{Style.RESET_ALL}")

    @staticmethod
    def progress(message: str):
        logging.info(message)
        print(f"{Fore.CYAN}🔄 PROGRESS: {message}{Style.RESET_ALL}")

    @staticmethod
    def stats(message: str):
        logging.info(message)
        print(f"{Fore.MAGENTA}📊 STATS: {message}{Style.RESET_ALL}")

    @staticmethod
    def separator():
        logging.info("━" * 50)
        print(f"{Fore.WHITE}{'━' * 50}{Style.RESET_ALL}")

class RequestQueue:
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.semaphore = asyncio.Semaphore(CONFIG['max_concurrent_requests'])
        self.stats = Stats()

    async def initialize(self):
        timeout = aiohttp.ClientTimeout(total=CONFIG['request_timeout'])
        self.session = aiohttp.ClientSession(timeout=timeout)

    async def close(self):
        if self.session:
            await self.session.close()

    async def make_request(self, url: str) -> Dict[str, Any]:
        endpoint = url.split('/v1')[1].split('?')[0].split('/')[1]

        async with self.semaphore:
            for attempt in range(CONFIG['max_retries']):
                try:
                    Logger.info(f"Making request (attempt {attempt + 1}/{CONFIG['max_retries']}): {url}")
                    async with self.session.get(url) as response:
                        if response.status == 429:  # Too Many Requests
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

                except asyncio.TimeoutError:
                    Logger.warning(f"Request timeout (attempt {attempt + 1}/{CONFIG['max_retries']}) for {url}")
                except aiohttp.ClientConnectionError as e:
                    Logger.error(f"Connection error (attempt {attempt + 1}/{CONFIG['max_retries']}) for {url}: {e}")
                except aiohttp.ClientError as e:
                    Logger.error(f"Aiohttp client error (attempt {attempt + 1}/{CONFIG['max_retries']}) for {url}: {e}")
                except Exception as e:
                    Logger.error(f"Request error (attempt {attempt + 1}/{CONFIG['max_retries']}) for {url}: {str(e)}")

                if attempt < CONFIG['max_retries'] - 1:
                    await asyncio.sleep(CONFIG['retry_delay'])

            self.stats.failed_requests += 1
            Logger.error(f"Failed after {CONFIG['max_retries']} attempts for {url}")
            raise Exception(f"Failed after {CONFIG['max_retries']} attempts")

class HBaseConnector:
    def __init__(self, host='localhost', port=9090, initialize_tables=False):
        self.connection = happybase.Connection(host=host, port=port)
        if initialize_tables:
            self.initialize_tables()

    def initialize_tables(self):
        """Initialize HBase tables with correct column families"""
        try:
            existing_tables = self.connection.tables()
            if b'f1_data' in existing_tables:
                self.connection.delete_table('f1_data', disable=True)
            if b'f1_reports' in existing_tables:
                self.connection.delete_table('f1_reports', disable=True)

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
        try:
            table_obj = self.connection.table(table)
            column_family = column_family.replace('_', '').lower()
            columns = {
                f"{column_family}:{key}".encode(): str(value).encode()
                for key, value in data.items()
            }

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
    def __init__(self, hbase_host='localhost', hbase_port=9090, initialize_tables=False):
        self.stats = Stats()
        self.queue = RequestQueue()
        self.hbase = HBaseConnector(hbase_host, hbase_port, initialize_tables)
        self.stats.start_time = time.time()

    def generate_row_key(self, *components) -> str:
        return "#".join(map(str, components))

    async def fetch_time_series_data(self, year: int, meeting_key: int, session_key: int,
                                   driver_number: int, endpoint: str) -> None:
        try:
            session_info = await self.queue.make_request(f"{BASE_URL}/sessions?session_key={session_key}")
            if not session_info:
                return

            session_start = datetime.fromisoformat(session_info[0]['date_start'].replace('Z', '+00:00'))
            session_end = datetime.fromisoformat(session_info[0]['date_end'].replace('Z', '+00:00'))

            current_time = session_start
            chunk_count = 0

            while current_time < session_end:
                next_time = min(current_time + timedelta(seconds=CONFIG['time_interval']), session_end)

                url = (f"{BASE_URL}{ENDPOINTS[endpoint]}?"
                      f"session_key={session_key}&"
                      f"driver_number={driver_number}&"
                      f"date>={current_time.isoformat()}&"
                      f"date<{next_time.isoformat()}")

                try:
                    data = await self.queue.make_request(url)
                    if data:
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
        try:
            session_key = session['session_key']
            Logger.progress(f"Processing session {session['session_name']}")

            row_key = self.generate_row_key(year, meeting_key, session_key)
            self.hbase.store_data('f1_data', row_key, session, 'session')

            drivers = await self.queue.make_request(f"{BASE_URL}/drivers?session_key={session_key}")

            for endpoint in GLOBAL_ENDPOINTS:
                if endpoint != 'drivers':
                    data = await self.queue.make_request(f"{BASE_URL}{ENDPOINTS[endpoint]}?session_key={session_key}")
                    if data:
                        endpoint_key = self.generate_row_key(year, meeting_key, session_key, endpoint)
                        self.hbase.store_data('f1_data', endpoint_key, {'data': data}, endpoint.replace('_', ''))
                    await asyncio.sleep(CONFIG['delay_between_requests'])

            for driver in drivers:
                driver_number = driver['driver_number']
                Logger.progress(f"Processing driver {driver_number}")

                for endpoint in TIME_SERIES_ENDPOINTS:
                    await self.fetch_time_series_data(
                        year, meeting_key, session_key, driver_number, endpoint
                    )
                    await asyncio.sleep(CONFIG['delay_between_requests'])

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
                                    year, meeting_key, session_key, driver_number, item.get('lap_number') or item.get('time')
                                )
                                self.hbase.store_data('f1_data', row_key, item, column_family)
                        await asyncio.sleep(CONFIG['delay_between_requests'])

            self.stats.sessions_processed += 1

        except Exception as e:
            Logger.error(f"Error processing session: {str(e)}")
            raise

    async def fetch_meetings(self, year: int) -> List[Dict[str, Any]]:
        url = f"{BASE_URL}/meetings?year={year}"
        Logger.info(f"Fetching meetings for year: {year} from URL: {url}")
        try:
            meetings = await self.queue.make_request(url)

            for meeting in meetings:
                row_key = self.generate_row_key(year, meeting['meeting_key'])
                self.hbase.store_data(
                    'f1_data',
                    row_key,
                    meeting,
                    'meeting',
                    {'fetched_at': datetime.now().isoformat()}
                )

            Logger.success(f"Fetched and stored {len(meetings)} meetings for {year}")
            return meetings

        except Exception as e:
            Logger.error(f"Error fetching meetings for year {year}: {str(e)}")
            raise

    async def process_meeting(self, year: int, meeting: Dict[str, Any]):
        try:
            meeting_key = meeting['meeting_key']
            Logger.separator()
            Logger.progress(f"Processing meeting: {meeting['meeting_name']}")

            sessions_url = f"{BASE_URL}/sessions?meeting_key={meeting_key}"
            sessions = await self.queue.make_request(sessions_url)

            for session in sessions:
                await self.process_session(year, meeting_key, session)
                await asyncio.sleep(CONFIG['delay_between_requests'])

            self.stats.meetings_processed += 1

        except Exception as e:
            Logger.error(f"Error processing meeting: {str(e)}")
            raise

def process_meeting_sync(year: int, meeting: Dict[str, Any], hbase_host: str, hbase_port: int) -> Dict[str, Any]:
    """
    Version synchrone du traitement d'un meeting pour la parallélisation
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    collector = F1DataCollector(hbase_host, hbase_port, initialize_tables=False)
    
    try:
        loop.run_until_complete(collector.queue.initialize())
        loop.run_until_complete(collector.process_meeting(year, meeting))
        
        return {
            "meetings_processed": 1,
            "sessions_processed": collector.stats.sessions_processed,
            "total_requests": collector.stats.total_requests,
            "failed_requests": collector.stats.failed_requests,
            "endpoint_stats": collector.stats.endpoint_stats
        }
        
    finally:
        loop.run_until_complete(collector.queue.close())
        loop.close()

class ParallelF1DataCollector:
    def __init__(self, hbase_host='localhost', hbase_port=9090, num_processes=None):
        self.stats = Stats()
        self.hbase_host = hbase_host
        self.hbase_port = hbase_port
        self.num_processes = num_processes or multiprocessing.cpu_count()
        self.stats.start_time = time.time()

        # Initialize HBase tables in the main process only
        self.main_collector = F1DataCollector(hbase_host, hbase_port, initialize_tables=True)

    def display_stats(self):
        """Display current execution statistics."""
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
        temp_collector = F1DataCollector(self.hbase_host, self.hbase_port, initialize_tables=False)
        await temp_collector.queue.initialize()
        
        try:
            meetings = await temp_collector.fetch_meetings(year)
            
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
        """Main execution method."""
        try:
            Logger.info(f"Initializing parallel F1 data collection with {self.num_processes} processes")
            
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
    """Entry point of the script."""
    collector = None
    try:
        collector = ParallelF1DataCollector(num_processes=10)  # Pour votre cluster de 3 machines
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
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        Logger.error(f"Error in main loop: {str(e)}")
        sys.exit(1)
    finally:
        loop.close()