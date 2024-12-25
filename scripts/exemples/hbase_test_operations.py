import happybase
import logging
import time

# Configuration
HBASE_HOST = 'localhost'
TABLE_NAME = 'f1_test'

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

def test_hbase_operations():
    try:
        # Create connection
        logging.info("Connecting to HBase...")
        connection = happybase.Connection(HBASE_HOST)
        
        # Create table if not exists
        if TABLE_NAME.encode() not in connection.tables():
            logging.info(f"Creating table {TABLE_NAME}")
            connection.create_table(
                TABLE_NAME,
                {'driver': dict(), 'car': dict()}  # Two column families
            )
            time.sleep(2)  # Wait for table creation
        
        # Get table
        table = connection.table(TABLE_NAME)
        
        # Insert some test data
        logging.info("Inserting test data...")
        row_key = '2024#1#VER'  # Year#RaceNumber#DriverCode
        table.put(row_key.encode(), {
            b'driver:name': b'Max Verstappen',
            b'driver:number': b'33',
            b'car:team': b'Red Bull Racing'
        })
        
        # Read the data back
        logging.info("Reading test data...")
        row = table.row(row_key.encode())
        print("\nRetrieved data:")
        for key, value in row.items():
            print(f"{key.decode()}: {value.decode()}")
            
        connection.close()
        logging.info("Test completed successfully!")
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    test_hbase_operations()