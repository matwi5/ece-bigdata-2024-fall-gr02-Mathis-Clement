# EMR Cluster Architecture Documentation

## Overview
This document details the architecture of our 3-node Amazon EMR cluster, designed for high-performance distributed data storage and processing using HBase and Spark. The architecture is optimized for Formula 1 data analysis, providing robust storage capabilities and efficient data processing.

## Cluster Architecture

### Physical Infrastructure
The following diagram illustrates the cluster's physical architecture and node distribution:

```mermaid
graph TB
    subgraph EMR Cluster
        subgraph Master["Master Node (m7g.xlarge)"]
            direction LR
            MS[Management Services]
            HM[HBase Master]
            ZK[ZooKeeper]
            SD[Spark Driver]
            YM[YARN Manager]
        end

        subgraph Core1["Core Node 1 (r7i.xlarge)"]
            direction LR
            RS1[RegionServer]
            DN1[DataNode]
            SE1[Spark Executor]
        end

        subgraph Core2["Core Node 2 (r7i.xlarge)"]
            direction LR
            RS2[RegionServer]
            DN2[DataNode]
            SE2[Spark Executor]
        end

        Master --> |manages| Core1
        Master --> |manages| Core2
        Core1 <--> |data replication| Core2
    end

    style Master fill:#f9f,stroke:#333,stroke-width:4px
    style Core1 fill:#bbf,stroke:#333,stroke-width:2px
    style Core2 fill:#bbf,stroke:#333,stroke-width:2px
```

### Node Specifications

#### Master Node (m7g.xlarge)
- **Compute**: 4 vCPU, 16 GB RAM
- **Storage**: 50 GB EBS gp3
- **Services**:
  - Cluster management
  - HBase Master
  - YARN ResourceManager
  - Spark Driver
  - ZooKeeper

#### Core Nodes (2x r7i.xlarge)
- **Compute**: 4 vCPU, 32 GB RAM each
- **Storage**: 150 GB EBS gp3 each
- **Services**:
  - HBase RegionServers
  - HDFS DataNodes
  - YARN NodeManagers
  - Spark Executors

## Software Architecture

### Component Stack
The following diagram shows the software stack and component interactions:

```mermaid
graph TD
    subgraph Applications
        JH[JupyterHub]
        Livy[Apache Livy]
    end

    subgraph Processing
        Spark[Apache Spark 3.5.2]
        YARN[YARN]
    end

    subgraph Storage
        HBase[Apache HBase 2.5.10]
        HDFS[Apache Hadoop 3.4.0]
        ZK2[ZooKeeper 3.9.2]
    end

    subgraph OS
        AL[Amazon Linux 2023]
    end

    Applications --> Processing
    Processing --> Storage
    Storage --> OS
    ZK2 --> |coordinates| HBase
```

### Data Flow Architecture
The following diagram illustrates the data flow through the system:

```mermaid
graph LR
    subgraph Input
        CSV[CSV Files]
        API[OpenF1 API]
    end

    subgraph Storage
        HDFS2[HDFS]
        HB[HBase]
    end

    subgraph Processing
        SP[Spark]
        YN[YARN]
    end

    subgraph Output
        VIZ[Visualizations]
        AN[Analytics]
        RPT[Reports]
    end

    Input --> Storage
    Storage --> Processing
    Processing --> Output
```

## Network Architecture

### Network Configuration
- **Region**: eu-west-3 (Paris)
- **VPC ID**: vpc-063a9ec520f6871a7
- **Subnet**: subnet-08ea540a579532ef6

### Network Flow
```mermaid
graph TD
    subgraph External
        User[User]
        API2[APIs]
    end

    subgraph VPC["VPC (vpc-063a9ec520f6871a7)"]
        subgraph Public["Public Subnet"]
            JH2[JupyterHub]
            LV[Livy]
        end

        subgraph Private["Private Subnet"]
            EMR[EMR Cluster]
        end
    end

    User --> Public
    API2 --> Public
    Public --> Private
```

## Security Architecture

### Access Control
```mermaid
graph LR
    subgraph IAM
        SR[Service Role]
        IP[Instance Profile]
    end

    subgraph Access
        SSH[SSH Access]
        WEB[Web Interfaces]
    end

    subgraph Security
        SG[Security Groups]
        KP[Key Pairs]
    end

    IAM --> Access
    Security --> Access
```

### Security Components
- **IAM Roles**:
  - Service Role: AmazonEMR-ServiceRole-20241219T204718
  - Instance Profile: AmazonEMR-InstanceProfile-20241219T204701
- **Access Methods**:
  - SSH via "PolePredict Cluster" key pair
  - Web interfaces:
    - JupyterHub: `https://<master-node>:9443`
    - HBase UI: `http://<master-node>:16010`
    - Spark History: `http://<master-node>:18080`

## Resource Management

### YARN Configuration
```mermaid
graph TB
    subgraph YARN["YARN Resource Management"]
        RM[Resource Manager]
        NM1[Node Manager 1]
        NM2[Node Manager 2]
    end

    subgraph Resources
        MEM[Memory]
        CPU[CPU]
        DISK[Storage]
    end

    RM --> NM1
    RM --> NM2
    NM1 --> Resources
    NM2 --> Resources
```

### Resource Allocation
- **Executor Configuration**:
  - Memory: 4GB per executor
  - Cores: 2 per executor
- **Dynamic Allocation**:
  - Enabled for automatic scaling
  - Based on workload demands
