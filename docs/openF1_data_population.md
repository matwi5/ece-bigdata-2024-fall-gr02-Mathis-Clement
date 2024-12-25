# OpenF1 Data Population Script Documentation

## Overview
The `hbase_populate_openF1.py` script is designed to fetch Formula 1 data from the OpenF1 API and store it in a distributed HBase database running on an EMR cluster. This script has been optimized for parallel processing and implements robust error handling.

## Technical Architecture

### Components

#### 1. RequestQueue
- Manages asynchronous HTTP requests to the OpenF1 API
- Implements rate limiting with `max_concurrent_requests`
- Handles retries and backoff strategy
- Maintains request statistics

#### 2. HBaseConnector
- Manages connection to HBase
- Handles table creation and data storage operations
- Implements efficient batch operations
- Supports column family management

#### 3. ParallelF1DataCollector
- Implements parallel processing of F1 data
- Manages multiprocessing pool for meeting processing
- Coordinates data collection across years and sessions
- Maintains global statistics

### Data Model

#### HBase Tables

1. `f1_data`
   - Column Families:
     - `car`: Car telemetry data
     - `driver`: Driver information
     - `intervals`: Time intervals
     - `laps`: Lap timing
     - `location`: GPS coordinates
     - `meeting`: Race meeting details
     - `pit`: Pit stop information
     - `position`: Track position
     - `racecontrol`: Race control messages
     - `session`: Session details
     - `stints`: Stint information
     - `teamradio`: Team radio communications
     - `weather`: Weather data

2. `f1_reports`
   - Column Families:
     - `meta`: Metadata information
     - `stats`: Processing statistics
     - `errors`: Error logging

### Row Key Design

The script uses composite row keys following these patterns:

1. Time Series Data (car_data, location):
   ```
   {year}#{meeting_key}#{session_key}#{driver_number}#{timestamp}
   ```

2. Lap Data:
   ```
   {year}#{meeting_key}#{session_key}#{driver_number}#{lap_number}
   ```

3. Meeting/Session Data:
   ```
   {year}#{meeting_key}#{session_key}
   ```

## Implementation Details

### Parallel Processing
- Uses Python's `multiprocessing` for parallel meeting processing
- Implements process pool executor for controlled concurrency
- Each meeting is processed in a separate process
- Configured with 10 parallel processes for optimal performance

### Error Handling
1. **Request Level**
   - Automatic retry for failed requests
   - Configurable retry count and delay
   - Rate limit handling with exponential backoff

2. **Process Level**
   - Process pool recovery from crashes
   - Graceful shutdown on interruption
   - Comprehensive error logging

### Configuration Parameters
```python
CONFIG = {
    "max_retries": 3,
    "retry_delay": 5,
    "request_timeout": 60,
    "delay_between_requests": 1,
    "max_concurrent_requests": 10,
    "time_interval": 900  # 15 minutes chunk size
}
```

### Logging System
- Implements colored console output
- Maintains detailed log file
- Different log levels (INFO, SUCCESS, ERROR, WARNING)
- Progress tracking and statistics

## Usage

### Prerequisites
```bash
pip install requests==2.31.0
pip install happybase==1.2.0
pip install aiohttp
pip install colorama
```

### Running the Script
```bash
python hbase_populate_openF1.py
```

### Monitoring
The script provides real-time progress updates:
- Meeting/Session processing status
- Request statistics
- Error reporting
- Performance metrics

Here's an example of the script's API request logs showing successful data fetching:

![API Requests Logs](screenshots/api_requests_logs.png)

As shown in the logs, the script successfully:
- Makes requests to the OpenF1 API with proper rate limiting
- Receives varying amounts of data items (e.g., 3384, 3330, 1407 items)
- Handles different session keys and time windows
- Processes multiple drivers' data concurrently

### Data Ingestion Verification

The following screenshot shows successful data ingestion into HBase, with over 3.8 million records stored:

![HBase Data Ingestion](screenshots/hbase_data_ingestion.png)

Key observations from the data ingestion:
- Consistent row key format (year#meeting#driver#timestamp)
- Sequential count increments showing reliable data storage
- Timestamp progression indicating proper time-series data organization
- Stable ingestion rate with regular count increments

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

## Performance Considerations

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
- Memory: ~100MB per process
- Network: Rate-limited API requests
- CPU: Multi-process utilization
- Storage: Efficient HBase writes

### Optimization Techniques
1. Chunked Processing
   - Splits time series data into 15-minute chunks
   - Prevents memory overflow
   - Enables parallel processing

2. Connection Management
   - Reuses HBase connections
   - Implements connection pooling
   - Manages async HTTP sessions

3. Data Batching
   - Groups related operations
   - Reduces network overhead
   - Optimizes HBase writes