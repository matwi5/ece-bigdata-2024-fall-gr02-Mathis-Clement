# HBase Configuration and Usage

## Setup SSH Tunnel
To connect to HBase from your local machine, you need to create an SSH tunnel:

```bash
ssh -i "PolePredict Cluster.pem" -N -L 9090:localhost:9090 hadoop@<master-node-public-dns>
```

## Python Requirements
Install required Python packages:
```bash
pip install happybase
```

## Test Connection
Use this script to test HBase connection:

```python
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
```

## Basic Operations
Example script for basic HBase operations:

```python
import happybase
import logging
import time

# Configuration
HBASE_HOST = 'localhost'
TABLE_NAME = 'f1_test'

def test_hbase_operations():
    connection = happybase.Connection(HBASE_HOST)
    
    # Create table
    connection.create_table(
        TABLE_NAME,
        {'driver': dict(), 'car': dict()}
    )
    
    # Get table
    table = connection.table(TABLE_NAME)
    
    # Insert data
    row_key = '2024#1#VER'
    table.put(row_key.encode(), {
        b'driver:name': b'Max Verstappen',
        b'driver:number': b'33',
        b'car:team': b'Red Bull Racing'
    })
    
    # Read data
    row = table.row(row_key.encode())
    print("\nRetrieved data:")
    for key, value in row.items():
        print(f"{key.decode()}: {value.decode()}")
```

## HDFS Replication Configuration
By default, HDFS is configured with a replication factor of 3. However, with only 2 core nodes, we need to adjust this:

1. Check current replication factor:
```bash
hdfs getconf -confKey dfs.replication
```

2. Modify HDFS configuration:
```bash
sudo vim /etc/hadoop/conf/hdfs-site.xml
```
Add or modify:
```xml
<property>
  <name>dfs.replication</name>
  <value>2</value>
</property>
```

3. Modify HBase configuration:
```bash
sudo vim /etc/hbase/conf/hbase-site.xml
```
Add:
```xml
<property>
  <name>dfs.replication</name>
  <value>2</value>
</property>
```

4. Apply changes:
```bash
# Restart services
sudo systemctl restart hadoop-hdfs-namenode
sudo systemctl start hbase-master

# Set replication for existing files
hdfs dfs -setrep -w 2 -R /user/hbase
```

5. Verify configuration:
```bash
# Check HDFS replication factor
hdfs getconf -confKey dfs.replication

# Check HDFS status
hdfs dfsadmin -report

# Check blocks status
hdfs fsck /user/hbase -files -blocks
```

## HBase Data Model
- **Row Key Structure**: `YEAR#RACE#DRIVER`
- **Column Families**:
  - `driver`: Driver-related information
  - `car`: Car and team information

## Best Practices
1. Always use SSH tunnel for remote connections
2. Encode strings when working with HBase (use `.encode()`)
3. Close connections after use
4. Use meaningful row keys for efficient data retrieval
5. Monitor replication status regularly
6. Ensure replication factor matches available DataNodes

## Common Issues and Solutions
1. Connection refused:
   - Verify SSH tunnel is active
   - Check if HBase is running on the master node
   - Verify port 9090 is open in security group

2. Table not found:
   - Check table name exists
   - Ensure proper encoding of table names

3. Data retrieval issues:
   - Verify row key format
   - Check column family and qualifier names
   - Ensure proper encoding of values

4. Replication issues:
   - Verify number of active DataNodes
   - Check disk space on DataNodes
   - Monitor under-replicated blocks
   - Ensure replication factor doesn't exceed DataNode count