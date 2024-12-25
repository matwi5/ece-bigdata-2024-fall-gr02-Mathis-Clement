# EMR F1 Data Analytics Platform

## Project Overview
This project implements a distributed data processing platform for Formula 1 race analysis using Amazon EMR (Elastic MapReduce). The system leverages HBase for data storage and Spark for data processing, designed to handle telemetry data, race statistics, and performance metrics from Formula 1 races.

## Architecture
The platform is built on a 3-node Amazon EMR cluster:

### Infrastructure
- **Master Node**: m7g.xlarge (4 vCPU, 16 GB RAM)
  - Cluster management services
  - HBase Master
  - Spark Driver
- **Core Nodes**: 2x r7i.xlarge (4 vCPU, 32 GB RAM each)
  - Data storage and processing
  - HBase RegionServers
  - HDFS DataNodes

### Software Stack
- EMR Version: 7.5.0
- Operating System: Amazon Linux 2023
- Components:
  - Apache Hadoop 3.4.0
  - Apache HBase 2.5.10
  - Apache Spark 3.5.2
  - Apache ZooKeeper 3.9.2
  - JupyterHub 1.5.0
  - Apache Livy 0.8.0

## Project Structure
```
ECE-BIGDATA-2024-FALL
├── config/
│   ├── hbase-site.xml
│   └── spark-defaults.conf
├── docs/
│   ├── architecture.md
│   ├── F1_data_analysis.md
│   ├── hbase_test_and_read.md
│   ├── hbase.md
│   ├── installation.md
│   ├── openF1_data_population.md
│   ├── problems.md
│   └── spark.md
├── scripts/
│   ├── examples/
│   │   ├── hbase_read.py
│   │   ├── hbase_test_connection.py
│   │   └── hbase_test_operations.py
│   ├── create_cluster.sh
│   ├── hbase_populate_openF1.py
│   ├── populate.log
│   └── spark_process.py
├── PolePredict Cluster.pem
├── PolePredict Cluster.ppk
└── README.md
```

## Setup and Installation

### Prerequisites
- AWS CLI installed and configured with appropriate permissions
- SSH key pair "PolePredict Cluster" created in eu-west-3 region
- IAM roles configured:
  - Service Role: AmazonEMR-ServiceRole-20241219T204718
  - Instance Profile: AmazonEMR-InstanceProfile-20241219T204701
- VPC (vpc-063a9ec520f6871a7) and subnet (subnet-08ea540a579532ef6) configured in eu-west-3 region

### AWS Environment Setup
1. Install AWS CLI:
   ```bash
   sudo apt-get update
   sudo apt-get install awscli
   ```

2. Configure AWS credentials:
   ```bash
   aws configure
   # Enter your AWS Access Key ID
   # Enter your AWS Secret Access Key
   # Default region: eu-west-3
   # Default output format: json
   ```

3. Verify infrastructure:
   ```bash
   # Check VPC configuration
   aws ec2 describe-vpcs

   # Check available subnets
   aws ec2 describe-subnets

   # Verify EMR IAM roles
   aws iam list-roles | grep -E "EMR|emr"
   ```

### Cluster Creation
1. Clone the repository:
   ```bash
   git clone [repository-url]
   cd ECE-BIGDATA-2024-FALL
   ```

2. Set up SSH key:
   ```bash
   # For WSL users
   cp "PolePredict Cluster.pem" ~/
   cd ~
   chmod 400 "PolePredict Cluster.pem"

   # For non-WSL users
   chmod 400 "PolePredict Cluster.pem"
   ```

3. Create and configure the cluster:
   ```bash
   cd scripts
   chmod +x create_cluster.sh
   ./create_cluster.sh
   ```

4. Verify cluster creation:
   ```bash
   # Get cluster status
   aws emr describe-cluster --cluster-id <your-cluster-id>

   # List active clusters
   aws emr list-clusters --active
   ```

### Security Group Configuration
1. Get security group ID:
   ```bash
   aws emr describe-cluster --cluster-id <cluster-id> \
       --query 'Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup'
   ```

2. Configure SSH access:
   ```bash
   aws ec2 authorize-security-group-ingress \
       --group-id <security-group-id> \
       --protocol tcp \
       --port 22 \
       --cidr 0.0.0.0/0
   ```

### Access Configuration
- SSH access using the provided key pair
- Web interfaces available through the master node's public DNS:
  - JupyterHub: https://master-node-dns:9443
  - HBase UI: http://master-node-dns:16010
  - Spark History Server: http://master-node-dns:18080

## Data Processing Pipeline

### Data Collection and Ingestion
#### OpenF1 API Integration
- Data sourced from OpenF1 API using asynchronous requests
- Rate-limited API calls with exponential backoff
- Implementation in `hbase_populate_openF1.py`
- Handles multiple data types:
  - Telemetry data (4Hz frequency)
  - Timing information
  - Race control messages
  - Driver information
  - Weather data

#### Data Validation and Preprocessing
- Schema validation for incoming data
- Data type conversion and normalization
- Missing value handling
- Timestamp standardization
- Duplicate detection and removal

### Storage Layer (HBase)
#### Table Design
- Optimized row key design: `{year}#{meeting_key}#{session_key}#{driver_number}#{timestamp}`
- Multiple column families for different data types:
  ```
  - car: Car telemetry data
  - driver: Driver information
  - intervals: Time intervals
  - laps: Lap timing
  - location: GPS coordinates
  - meeting: Race meeting details
  - pit: Pit stop information
  - position: Track position
  - racecontrol: Race control messages
  - session: Session details
  - stints: Stint information
  - teamradio: Team radio communications
  - weather: Weather data
  ```

#### Performance Optimization
- Region server configuration for balanced load
- Proper data distribution using salted row keys
- Compression enabled for storage efficiency
- Block cache configuration for frequent access patterns
- Write buffer size optimization

### Processing Layer (Spark)
#### Performance Analysis Pipeline
1. Lap Times Analysis
   - Average lap time calculation
   - Best lap identification
   - Sector time breakdown
   - Lap time consistency analysis

2. Speed Analysis
   - Top speed calculations
   - Average speed profiles
   - Speed trap data processing
   - DRS activation analysis

3. Race Strategy Analysis
   - Pit stop timing optimization
   - Tyre strategy evaluation
   - Position changes tracking
   - Race pace consistency

#### Data Processing Optimization
1. Memory Management
   - Efficient DataFrame caching
   - Memory pressure monitoring
   - Garbage collection tuning
   - Partition size optimization

2. Processing Configuration
   - Executor memory: 4GB per executor
   - Number of executors: 4 distributed across worker nodes
   - Cores per executor: 2 cores
   - Dynamic allocation enabled: min=2, max=6 executors

### Output Generation
#### Analysis Reports
- CSV file generation with timestamps
- Structured output directory organization
- Multiple analysis types:
  - Driver performance metrics
  - Team comparisons
  - Race strategy analysis
  - Technical performance data

#### Performance Metrics
- Processing time tracking
- Data volume measurements
- Resource utilization monitoring
- Error rate tracking

## Documentation
Detailed documentation is available in the `docs` directory:
- `architecture.md`: System architecture details
- `installation.md`: Setup and installation guide
- `hbase.md`: HBase configuration and usage
- `spark.md`: Spark processing documentation
- `problems.md`: Common issues and solutions
- `F1_data_analysis.md`: Data analysis outputs
- `openF1_data_population.md`: HBase poputlation with F1 data documentation
- `hbase_test_and_read`: HBase tests and read documentation

## Testing
Example scripts are provided in the `scripts/examples` directory:
- `hbase_test_connection.py`: HBase connectivity testing
- `hbase_test_operations.py`: Basic CRUD operations testing
- `hbase_read.py`: Data reading utilities

## Known Issues and Solutions
Common problems and their solutions are documented in `problems.md`, including:
- Instance type availability issues
- Storage configuration challenges
- SSH connection problems
- Security group configurations

## Contributing
1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License
This project is part of the Big Data course at ECE Paris.

## Acknowledgments
- EMR Documentation
- OpenF1 API
- AWS Support