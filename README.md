# EMR F1 Data Analytics Platform

## Project Overview

This project delivers a robust, distributed data processing platform tailored for comprehensive Formula 1 race analysis. Deployed on Amazon EMR, the platform leverages the power of **Apache HBase** for efficient data storage and **Apache Spark** for high-performance data processing. This system is engineered to analyze a vast array of Formula 1 data, including detailed telemetry, race statistics, and driver performance metrics, offering deep insights into the intricacies of Formula 1 racing. The choice of an EMR cluster over alternatives like a Raspberry Pi cluster was driven by scalability requirements, budget considerations, and integration needs with other AWS services used in a broader web application context.

### Project Objectives

Aligned with the Big Data course requirements at ECE Paris, this project aims to:

-   Implement a scalable data pipeline for the ingestion, storage, and analysis of Formula 1 data.
-   Utilize a suite of distributed systems, showcasing their integration and practical application in a real-world scenario.
-   Provide a foundational understanding of distributed data processing technologies and their application in sports analytics.

The technical project option was chosen to demonstrate a tangible implementation of distributed systems processing a large dataset.

## Architecture

The platform is built on a 3-node Amazon EMR cluster, ensuring a balance of performance and resource utilization:

### Infrastructure

-   **Master Node**: `m7g.xlarge` (4 vCPU, 16 GB RAM)
    -   Orchestrates cluster management
    -   Hosts the HBase Master, and Spark Driver
-   **Core Nodes**: 2x `r7i.xlarge` (4 vCPU, 32 GB RAM each)
    -   Facilitate data storage and processing
    -   Run HBase RegionServers and HDFS DataNodes

### Software Stack

-   **EMR Version**: 7.5.0
-   **Operating System**: Amazon Linux 2023
-   **Components**:
    -   Apache Hadoop 3.4.0
    -   Apache HBase 2.5.10
    -   Apache Spark 3.5.2
    -   Apache ZooKeeper 3.9.2
    -   JupyterHub 1.5.0
    -   Apache Livy 0.8.0

The selection of these technologies was based on their ability to handle large-scale, structured datasets with requirements for fast read and write speeds, aligning with the project's data processing needs. The use of AWS EMR, EC2, and potentially S3 for storage was considered the best approach to centralize the data processing pipeline within the AWS ecosystem, providing a cohesive and efficient environment for data analysis.

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

Setting up the EMR cluster involves several key steps, detailed in the `installation.md` document. This includes configuring the AWS CLI, verifying your infrastructure, creating the EMR cluster, setting up security groups, and configuring access via SSH and web interfaces.

### Prerequisites

-   AWS CLI installed and configured.
-   "PolePredict Cluster" SSH key pair created in the `eu-west-3` region.
-   IAM roles properly configured.
-   VPC and subnet configured in the `eu-west-3` region.

### AWS Environment Setup

Detailed instructions are provided in the `installation.md` file, covering AWS CLI installation and configuration, infrastructure verification, and initial cluster setup steps.

### Cluster Creation

The `create_cluster.sh` script automates the cluster creation process. Execution and verification steps are outlined in the `installation.md` guide.

### Security Group Configuration

Ensuring secure access to the cluster is paramount. Steps to configure the necessary security group settings are detailed in the `installation.md` document.

### Access Configuration

-   **SSH Access**: Enabled using the "PolePredict Cluster" key pair.
-   **Web Interfaces**: Accessible via the master node's public DNS:
    -   JupyterHub: `https://<master-node-dns>:9443`
    -   HBase UI: `http://<master-node-dns>:16010`
    -   Spark History Server: `http://<master-node-dns>:18080`

## Data Processing Pipeline

The data processing pipeline is a critical aspect of the project, encompassing data collection and ingestion, storage, processing, and output generation.

### Data Collection and Ingestion

-   **OpenF1 API Integration**: Details on how data is sourced from the OpenF1 API are provided in `openF1_data_population.md`.
-   **Data Validation and Preprocessing**: Steps for ensuring data quality are integrated into the data ingestion process.

### Storage Layer (HBase)

-   **Table Design**: A deep dive into the optimized HBase table design is available in `hbase.md`.
-   **Performance Optimization**: Strategies for maximizing HBase performance are discussed in `hbase.md`.

### Processing Layer (Spark)

-   **Performance Analysis Pipeline**: The methodologies behind the analysis of lap times, speed, and race strategies are detailed in `spark.md`.
-   **Data Processing Optimization**: Techniques for efficient Spark processing are covered in `spark.md`.

### Output Generation

-   **Analysis Reports**: The generation of CSV reports for various analyses is described in `F1_data_analysis.md`.
-   **Performance Metrics**: Insights into the tracking of processing times and resource utilization are provided in `spark.md`.

## Documentation

Comprehensive documentation is maintained within the `docs` directory, offering insights and guidance on every aspect of the project:

-   [**Architecture Overview**](docs/architecture.md): Detailed breakdown of the system's architecture.
-   [**Installation Guide**](docs/installation.md): Step-by-step instructions for setting up the cluster.
-   [**HBase Configuration and Usage**](docs/hbase.md): Guidance on HBase setup, configuration, and optimization.
-   [**HBase Test and Read**](docs/hbase_test_and_read.md): Guidance on HBase test and read.
-   [**Spark Processing**](docs/spark.md): Documentation on Spark configuration and data processing pipelines.
-   [**OpenF1 Data Population**](docs/openF1_data_population.md): Documentation on openF1 data population.
-   [**F1 Data Analysis**](docs/F1_data_analysis.md): Description of data analysis outputs and methodologies.
-   [**Problems and Solutions**](docs/problems.md): Troubleshooting common issues encountered during the project.

## Testing

The `scripts/examples` directory contains utilities for testing HBase connectivity, CRUD operations, and data reading, ensuring the system's operational integrity.
-   `hbase_test_connection.py`: HBase connectivity testing
-   `hbase_test_operations.py`: Basic CRUD operations testing
-   `hbase_read.py`: Data reading utilities

## License

This project is developed as part of the Big Data course at ECE Paris and is not under an open-source license.

## Acknowledgments

-   AWS EMR Documentation
-   OpenF1 API
-   AWS Support and Cloud Resources

## Team Members

<div align="center">
  <p><strong>Data & IA - ING5 Group 02</strong></p>
</div>

#

<div align="center">
  <img src="https://github.com/matwi5.png" width="100" style="border-radius: 50%;">
  <p><strong>Mathis BAUDRILLARD</strong></p>
  <a href="https://github.com/matwi5">
    <img src="https://img.shields.io/github/followers/matwi5?label=Follow&style=social">
  </a>
</div>

<div align="center">
  <img src="https://github.com/clementjalouzet.png" width="100" style="border-radius: 50%;">
  <p><strong>Clément JALOUET</strong></p>
  <a href="https://github.com/clementjalouzet">
    <img src="https://img.shields.io/github/followers/clementjalouzet?label=Follow&style=social">
  </a>
</div>


