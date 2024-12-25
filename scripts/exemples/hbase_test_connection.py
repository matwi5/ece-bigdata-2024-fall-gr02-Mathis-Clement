import happybase
import logging

# Configuration
HBASE_HOST = 'localhost'  # When using SSH tunnel
TEST_TABLE = 'test_connection'

logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s')

def test_hbase_connection():
    try:
        connection = happybase.Connection(HBASE_HOST)
        existing_tables = connection.tables()
        print(f"Existing tables: {existing_tables}")
        connection.close()
    except Exception as e:
        logging.error(f"Error: {str(e)}")

if __name__ == "__main__":
    test_hbase_connection()