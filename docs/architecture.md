# EMR Cluster Architecture

## Overview
The architecture consists of a 3-node Amazon EMR cluster designed for distributed data storage and processing using HBase and Spark.

## Cluster Configuration
- **Master Node**: m7g.xlarge
  - 4 vCPU, 16 GB RAM
  - 50 GB EBS gp3 storage
  - Runs cluster management services

- **Core Nodes**: 2x r7i.xlarge
  - 4 vCPU, 32 GB RAM each
  - 150 GB EBS gp3 storage each
  - Handles data storage and processing

## Software Stack
- EMR Version: 7.5.0
- Operating System: Amazon Linux 2023
- Components:
  - Apache Hadoop 3.4.0
  - Apache HBase 2.5.10
  - Apache Spark 3.5.2
  - Apache ZooKeeper 3.9.2
  - JupyterHub 1.5.0
  - Apache Livy 0.8.0

## Storage Architecture
### HDFS Layer
- Distributed across core nodes
- Replication factor: 3
- Used by HBase for data storage

### HBase Layer
- Runs on top of HDFS
- RegionServers on core nodes
- Master server on master node
- ZooKeeper for coordination

## Processing Architecture
### Spark Processing
- Distributed processing across all nodes
- Driver on master node
- Executors on core nodes

### Resource Management
- YARN for resource management
- Dynamic resource allocation enabled
- Default executor configuration:
  - Memory: 4GB per executor
  - Cores: 2 per executor

## Network Architecture
- Region: eu-west-3 (Paris)
- VPC ID: vpc-063a9ec520f6871a7
- Subnet: subnet-08ea540a579532ef6
- Security Groups: Managed by EMR

## Access and Security
- IAM Roles:
  - Service Role: AmazonEMR-ServiceRole-20241219T204718
  - Instance Profile: AmazonEMR-InstanceProfile-20241219T204701
- SSH Access via "PolePredict Cluster" key pair
- Web Interfaces:
  - JupyterHub for notebook access
  - Livy REST interface for Spark jobs