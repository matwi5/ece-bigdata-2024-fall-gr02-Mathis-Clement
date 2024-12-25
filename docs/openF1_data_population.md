# OpenF1 Data Population Script Documentation

## Overview
The `hbase_populate_openF1.py` script is designed to fetch Formula 1 data from the OpenF1 API and store it in a distributed HBase database running on an EMR cluster. The script fetches data for the 2023 and 2024 racing seasons.

## Technical Architecture

### HBase Tables Structure

1. **f1_data Table**
   - Main table storing all F1-related data
   - Column Families:
     - `car`: Car telemetry data
       - Attributes: speed, rpm, gear, throttle, brake, drs
       - High-frequency data (4Hz)
     - `driver`: Driver information
       - Basic: name, number, team
       - Session-specific: status, position
     - `interval`: Time intervals data
       - Gap to leader
       - Gap to car ahead
       - Interval types
     - `lap`: Lap timing data
       - Lap times
       - Sector times
       - Lap status (valid/invalid)
     - `location`: Car GPS data
       - Coordinates (x, y, z)
       - Track status
       - High-frequency data (4Hz)
     - `meeting`: Race meeting information
       - Circuit details
       - Country
       - Meeting type
     - `pit`: Pit stop data
       - Entry/exit times
       - Duration
       - Tire information
     - `position`: Track position data
       - Track position
       - Status
     - `race_control`: Race control messages
       - Message content
       - Category
       - Flag status
     - `session`: Session information
       - Type (Practice/Qualifying/Race)
       - Start/End times
       - Weather conditions
     - `stint`: Stint data
       - Tire compound
       - Lap count
       - Stint number
     - `team_radio`: Team radio communications
       - Message content
       - Timestamp
       - Category

2. **report Table**
   - Monitoring table for data ingestion process
   - Column Family `info`:
     - `status`: Success/Failed/Skipped
     - `data_transferred`: Count of records
     - `start_time`: Operation start timestamp
     - `end_time`: Operation end timestamp
     - `error_message`: Details if failed

### Row Key Design Strategy

Detailed breakdown of row key patterns and their rationale:

1. **Car Data & Location Data**:
   ```
   {year}#{meeting_key}#{session_key}#{driver_number}#{date_str}
   ```
   - Enables efficient time-series queries
   - Natural grouping by year and event
   - Fast lookups for specific driver data

2. **Lap Data**:
   ```
   {year}#{meeting_key}#{session_key}#{driver_number}#{lap_number}
   ```
   - Optimized for lap-by-lap analysis
   - Easy retrieval of specific lap information
   - Maintains chronological order

3. **Meeting Data**:
   ```
   {year}#{meeting_key}
   ```
   - Simple key for race weekend information
   - Year prefix for historical queries

4. **Session Data**:
   ```
   {year}#{session_key}
   ```
   - Unique identifier for each session
   - Enables session-specific queries

5. **Report Data**:
   ```
   {year}#{meeting_key}#{session_key}#{endpoint}#{timestamp}
   ```
   - Comprehensive key for monitoring
   - Enables tracking of specific data ingestion tasks

## Data Flow and Processing

### API Integration Details
Base URL: https://api.openf1.org/v1

Endpoints and Their Characteristics:
1. **High-Frequency Endpoints** (4Hz):
   - `/car_data`: Telemetry data
     - Parameters: date>, date<, meeting_key, session_key
   - `/location`: GPS positioning
     - Parameters: date>, date<, meeting_key, session_key

2. **Standard Endpoints**:
   - `/drivers`: Driver information
   - `/intervals`: Gap timing data
   - `/laps`: Lap timing information
   - `/pit`: Pit stop details
   - `/position`: Track positioning
   - `/race_control`: Official messages
   - `/stints`: Tire usage data
   - `/team_radio`: Team communications

3. **Metadata Endpoints**:
   - `/meetings`: Race weekend information
   - `/sessions`: Session details

### Data Processing Pipeline Details

1. **Initialization Phase**
   ```mermaid
   graph TD
       A[Start] --> B[Create HBase Connection]
       B --> C[Verify/Create Tables]
       C --> D[Configure Logging]
       D --> E[Initialize Thread Pool]
   ```

2. **Main Processing Flow**
   ```mermaid
   graph TD
       A[Start Year Loop] --> B[Fetch Meetings]
       B --> C[Process Each Meeting]
       C --> D[Fetch Sessions]
       D --> E[Process Each Session]
       E --> F[Fetch Endpoint Data]
       F --> G[Process High-Frequency Data]
       G --> H[Store in HBase]
       H --> I[Update Report Table]
   ```

3. **High-Frequency Data Processing**
   ```mermaid
   graph TD
       A[Get Session Time Window] --> B[Split into 15-min Chunks]
       B --> C[Create Thread Pool]
       C --> D[Process Chunks Concurrently]
       D --> E[Merge Results]
       E --> F[Store in HBase]
   ```

### Error Handling and Recovery

1. **Error Categories**:
   - Network errors (API timeouts, connection issues)
   - HBase errors (connection loss, timeout)
   - Data validation errors
   - Resource exhaustion

2. **Recovery Strategies**:
   - Automatic retry for transient errors
   - Graceful degradation for missing data
   - Session continuation after partial failures
   - Transaction rollback capabilities

## Monitoring and Operations

### Real-time Monitoring
1. **Console Output**:
   ```
   [INFO] 2024-01-15 10:30:15 - Starting data fetch for meeting_key: 1234
   [SUCCESS] 2024-01-15 10:30:16 - Successfully processed car_data
   [WARNING] 2024-01-15 10:30:17 - Retrying failed request
   [ERROR] 2024-01-15 10:30:18 - Failed to process data: timeout
   ```

2. **HBase Monitoring Commands**:
   ```bash
   # Check table status
   echo "status 'f1_data'" | hbase shell

   # Count records
   echo "count 'f1_data'" | hbase shell

   # Check data distribution
   echo "scan 'report'" | hbase shell
   ```

3. **Performance Metrics**:
   - Records processed per second
   - API latency
   - HBase write latency
   - Thread pool utilization

### Operational Procedures

1. **Pre-execution Checklist**:
   ```bash
   # 1. Verify HBase connection
   python hbase_test_connection.py

   # 2. Check available disk space
   df -h

   # 3. Verify AWS EMR cluster status
   aws emr describe-cluster --cluster-id <your-cluster-id>

   # 4. Test API access
   curl https://api.openf1.org/v1/meetings?year=2024
   ```

2. **Execution Command**:
   ```bash
   nohup python hbase_populate_openF1.py > populate.log 2>&1 &
   ```

3. **Monitoring During Execution**:
   ```bash
   # Follow log output
   tail -f populate.log

   # Check process status
   ps aux | grep hbase_populate_openF1.py

   # Monitor system resources
   top -u hadoop
   ```

4. **Post-execution Verification**:
   ```bash
   # Check for errors in log
   grep ERROR populate.log

   # Verify data in HBase
   echo "count 'f1_data'" | hbase shell

   # Check report table for completion status
   echo "scan 'report'" | hbase shell
   ```

## Performance Tuning

### Configuration Parameters
1. **Thread Pool Settings**:
   - MAX_CONCURRENT_REQUESTS = 5
   - Optimal for balancing throughput and resource usage

2. **Time Window Settings**:
   - Chunk size: 15 minutes
   - Prevents memory overflow
   - Balances processing speed and stability

3. **HBase Client Settings**:
   ```python
   connection = happybase.Connection(
       HBASE_HOST,
       timeout=20000,  # 20 seconds
       transport='framed',
       protocol='compact'
   )
   ```

### Resource Requirements
1. **Memory Usage**:
   - Base: ~500MB
   - Per thread: ~100MB
   - Maximum: ~1GB total

2. **Network Usage**:
   - API calls: ~100 requests/minute
   - Data transfer: ~10MB/minute

3. **Storage Requirements**:
   - Estimated per race: ~500MB
   - Annual total: ~15GB

## Dependencies and Setup
1. **Python Packages**:
   ```bash
   pip install requests==2.31.0
   pip install happybase==1.2.0
   ```

2. **System Requirements**:
   - Python 3.8+
   - HBase 2.5.10+
   - Sufficient disk space (~20GB minimum)
   - Network access to OpenF1 API

3. **Environment Setup**:
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/script/directory"
   export HBASE_THRIFT_HOST=your-emr-master-dns
   export HBASE_THRIFT_PORT=9090
   ```