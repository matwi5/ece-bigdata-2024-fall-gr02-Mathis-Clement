import happybase
import random
from typing import List, Dict, Any
from datetime import datetime
from colorama import Fore, Style, init
import json

# Initialize colorama for colored output
init()

class F1DataReader:
    def __init__(self, host='localhost', port=9090):
        """Initialize the F1 data reader with HBase connection parameters."""
        self.connection = happybase.Connection(host=host, port=port)
        self.table = self.connection.table('f1_data')
        
    def print_section_header(self, title: str):
        """Print a formatted section header."""
        print(f"\n{Fore.CYAN}{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}{Style.RESET_ALL}\n")
    
    def format_data(self, data: Dict[str, bytes]) -> Dict[str, Any]:
        """Format binary HBase data into a readable dictionary."""
        return {
            k.decode().split(':')[1]: v.decode()
            for k, v in data.items()
        }
    
    def print_formatted_data(self, data: Dict[str, Any], indent: int = 2):
        """Print dictionary data in a formatted way."""
        for key, value in data.items():
            print(f"{' ' * indent}{Fore.GREEN}{key}{Style.RESET_ALL}: {value}")
    
    def get_first_meeting(self) -> Dict[str, Any]:
        """Retrieve and display information about the first meeting."""
        self.print_section_header("First Meeting Information")
        
        # Scan the table for the first meeting record
        for key, data in self.table.scan(columns=['meeting']):
            meeting_data = self.format_data(data)
            self.print_formatted_data(meeting_data)
            return {
                'meeting_key': meeting_data['meeting_key'],
                'year': key.decode().split('#')[0]
            }
            
    def get_first_session(self, year: str, meeting_key: str) -> Dict[str, Any]:
        """Retrieve and display information about the first session of a meeting."""
        self.print_section_header("First Session Information")
        
        prefix = f"{year}#{meeting_key}".encode()
        for key, data in self.table.scan(row_prefix=prefix, columns=['session']):
            session_data = self.format_data(data)
            self.print_formatted_data(session_data)
            return {'session_key': session_data['session_key']}
            
    def get_drivers(self, session_key: str):
        """Retrieve and display driver information for a session."""
        self.print_section_header("Drivers Information")
        
        for key, data in self.table.scan(columns=['driver']):
            if session_key in key.decode():
                driver_data = self.format_data(data)
                self.print_formatted_data(driver_data)
                
    def get_random_records(self, session_key: str, column_family: str, count: int = 10):
        """Retrieve and display random records for a specific column family."""
        self.print_section_header(f"Random {column_family} Records")
        
        records = []
        for key, data in self.table.scan(columns=[column_family]):
            if session_key in key.decode():
                records.append((key, data))
                
        if records:
            selected = random.sample(records, min(count, len(records)))
            for key, data in selected:
                print(f"\n{Fore.YELLOW}Record Key:{Style.RESET_ALL} {key.decode()}")
                self.print_formatted_data(self.format_data(data))
                
    def get_driver_data(self, session_key: str, driver_number: int = 1):
        """Retrieve and display various data types for a specific driver."""
        column_families = ['car', 'interval', 'laps', 'location', 'pit', 
                         'position', 'stints', 'teamradio']
        
        for cf in column_families:
            self.print_section_header(f"Driver {driver_number} - {cf} Data")
            self.get_random_records(f"{session_key}#{driver_number}", cf)

def main():
    try:
        # Initialize reader
        reader = F1DataReader()
        
        # Get first meeting info
        meeting_info = reader.get_first_meeting()
        if not meeting_info:
            print(f"{Fore.RED}No meeting data found!{Style.RESET_ALL}")
            return
            
        # Get first session info
        session_info = reader.get_first_session(
            meeting_info['year'], 
            meeting_info['meeting_key']
        )
        if not session_info:
            print(f"{Fore.RED}No session data found!{Style.RESET_ALL}")
            return
            
        # Get drivers info
        reader.get_drivers(session_info['session_key'])
        
        # Get random race control and weather data
        reader.get_random_records(session_info['session_key'], 'racecontrol')
        reader.get_random_records(session_info['session_key'], 'weather')
        
        # Get driver specific data
        reader.get_driver_data(session_info['session_key'])
        
    except Exception as e:
        print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
    finally:
        reader.connection.close()

if __name__ == "__main__":
    main()