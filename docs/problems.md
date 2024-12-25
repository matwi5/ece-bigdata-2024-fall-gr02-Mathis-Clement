# EMR Cluster Problems and Solutions for F1 Data Analytics Platform

## 1. Introduction

This document provides a comprehensive guide to troubleshooting common problems encountered during the setup, configuration, and operation of the Amazon EMR cluster for the Formula 1 data analytics platform. It covers various issues related to instance types, storage, networking, security, application stack, and cost management, providing detailed solutions and best practices to resolve them.

This document is a valuable resource for anyone working with the F1 data analytics platform, helping to quickly identify and resolve issues, ensuring smooth operation and optimal performance of the EMR cluster.

## 2. Instance Type Availability Issues

### 2.1. Problem 1: `r7g.xlarge` Not Available

**Error Message:**

```
An error occurred (ValidationException) when calling the RunJobFlow operation: Instance type 'r7g.xlarge' is not supported.
```

**Explanation:**

This error occurs when the specified instance type (`r7g.xlarge` in this case) is not available in the selected AWS region (`eu-west-3`). Instance type availability can vary between regions due to capacity constraints or regional limitations.

**Solutions:**

1. **Change to `r7i.xlarge`**:
    -   This was the chosen solution for the project, as `r7i.xlarge` instances were available in the `eu-west-3` region and provided similar specifications to `r7g.xlarge`.
    -   Modify the `create_cluster.sh` script to use `r7i.xlarge` for the core nodes.

2. **Use `r5.xlarge`**:
    -   `r5.xlarge` is another suitable alternative that is generally available in most regions.
    -   This instance type offers a good balance of compute and memory resources for HBase and Spark workloads.
    -   Modify the `create_cluster.sh` script to use `r5.xlarge` if `r7i.xlarge` is also not available.

3. **Choose a Different Region**:
   - If the `r7g.xlarge` instance type is essential for your workload, consider deploying the cluster in a different region where it is available.
   - However, this might introduce latency issues or data transfer costs if other components of your application are located in the original region.

**Verification:**

-   Use the AWS CLI to check the availability of instance types in different regions:

    ```bash
    aws ec2 describe-instance-type-offerings --location-type availability-zone --filters "Name=instance-type,Values=r7g.xlarge,r7i.xlarge,r5.xlarge" --region eu-west-3
    ```

### 2.2. Problem 2: Instance Type Performance

**Observation:**

Initially, the project considered using `t3.small/medium` instances for cost savings. However, these instances proved insufficient for the memory requirements of HBase and Spark.

**Explanation:**

-   `t3` instances are burstable performance instances designed for workloads with occasional CPU bursts. They are not ideal for sustained, memory-intensive workloads like those handled by HBase RegionServers and Spark Executors.
-   HBase and Spark require significant amounts of memory for optimal performance. `t3.small/medium` instances did not provide enough RAM to handle the data volume and processing demands of the F1 data analytics platform.

**Solution:**

-   **Upgrade to `r7i.xlarge` for Core Nodes**: This provides sufficient memory (32GB) for HBase RegionServers and Spark Executors to operate efficiently.
-   **Select `m7g.xlarge` for Master Node**: This instance type offers a good balance of compute and memory resources (16GB) for managing the cluster, running the HBase Master, YARN ResourceManager, and Spark Driver.

**Rationale:**

-   The `r7i.xlarge` and `m7g.xlarge` instance types provide the necessary compute and memory resources to ensure the smooth operation of HBase and Spark, preventing performance bottlenecks and out-of-memory errors.
-   While these instances are more expensive than `t3` instances, they are essential for the performance requirements of the F1 data analytics platform.

## 3. Storage Configuration

### 3.1. Problem 1: EBS Volume Size

**Issue:**

The initial 32GB EBS volume size was insufficient for HDFS replication and overall storage needs, leading to storage space issues.

**Explanation:**

-   HDFS requires sufficient storage space for data replication. With a replication factor of 2, the total storage needed is at least double the size of the data being stored.
-   32GB was insufficient to accommodate the replicated HDFS data, temporary files, logs, and operating system requirements.

**Solution:**

-   **Increase EBS Volume Size**: Increased the EBS volume size to 150GB for core nodes and 50GB for the master node in the `create_cluster.sh` script.
    ```bash
    # In create_cluster.sh:
    # For Master Node:
    InstanceGroupType=MASTER,InstanceCount=1,InstanceType="$MASTER_INSTANCE_TYPE",EbsConfiguration={EbsBlockDeviceConfigs=[{VolumeSpecification={SizeInGB=50,VolumeType=gp3},VolumesPerInstance=1}]}
    # For Core Nodes:
    InstanceGroupType=CORE,InstanceCount="$CORE_INSTANCE_COUNT",InstanceType="$CORE_INSTANCE_TYPE",EbsConfiguration={EbsBlockDeviceConfigs=[{VolumeSpecification={SizeInGB=150,VolumeType=gp3},VolumesPerInstance=1}]}
    ```
-   **Use `gp3` Volumes**: Configured `gp3` EBS volumes for better performance compared to the default `gp2` volumes. `gp3` volumes offer higher IOPS and throughput, which is beneficial for HBase and Spark workloads.

**Rationale:**

-   The larger EBS volumes provide ample space for HDFS data, temporary files, logs, and the operating system.
-   `gp3` volumes provide better performance for I/O-intensive operations, improving the overall performance of HBase and Spark.

### 3.2. Problem 2: HDFS Replication Factor

**Issue:**

The default HDFS replication factor of 3 caused under-replication errors with only two core nodes, leading to data inconsistency and potential data loss.

**Explanation:**

-   HDFS replicates data blocks across multiple DataNodes for fault tolerance and data availability.
-   A replication factor of 3 requires at least three DataNodes to store three copies of each data block.
-   With only two core nodes (and thus two DataNodes), a replication factor of 3 could not be satisfied, resulting in under-replicated blocks.

**Solution:**

1. **Modify HDFS Configuration**:
    -   Edited the `hdfs-site.xml` file on all nodes to set the replication factor to 2.

    ```bash
    sudo vim /etc/hadoop/conf/hdfs-site.xml
    # Add or modify the following property:
    <property>
      <name>dfs.replication</name>
      <value>2</value>
    </property>
    ```

2. **Modify HBase Configuration**:
    -   Edited the `hbase-site.xml` file on all nodes to set the replication factor to 2.
    ```bash
    sudo vim /etc/hbase/conf/hbase-site.xml
    # Add or modify the following property:
    <property>
      <name>dfs.replication</name>
      <value>2</value>
    </property>
    ```

3. **Apply Changes**:
    -   Restarted the NameNode and HBase Master to apply the new configuration.
    -   Manually adjusted the replication factor for existing HBase data in HDFS.

    ```bash
    # On the master node:
    sudo systemctl restart hadoop-hdfs-namenode
    sudo systemctl restart hbase-master
    # After restarting, wait for HBase to fully initialize before running:
    hdfs dfs -setrep -w 2 -R /hbase
    ```

**Challenges:**

-   **Region Server Restart**: RegionServers required a manual restart after the configuration change.
-   **Initial Under-Replication**: Some data blocks remained under-replicated initially, requiring time for HDFS to replicate them to the second DataNode.
-   **WAL File Blocking**: WAL (Write Ahead Log) files initially blocked the replication adjustment process. This was resolved by temporarily disabling WALs, adjusting the replication factor, and then re-enabling WALs.

**Verification Process:**

-   **Check Replication Factor**:

    ```bash
    hdfs getconf -confKey dfs.replication
    ```

-   **Monitor Replication Status**:

    ```bash
    hdfs dfsadmin -report
    ```
    This command provides information about the number of live DataNodes, under-replicated blocks, and overall HDFS status.

-   **Verify Block Replication**:

    ```bash
    hdfs fsck /hbase -files -blocks
    ```
    This command checks the file system integrity and provides details about block replication. Look for any under-replicated blocks.

## 4. Application Stack Integration

### 4.1. Problem: JupyterHub Access

**Issue:**

JupyterHub was not accessible immediately after cluster creation.

**Explanation:**

-   It takes time for all services to fully initialize and start after the EMR cluster enters the `RUNNING` state.
-   JupyterHub, being a web application, requires all its dependencies and services to be up and running before it becomes accessible.

**Solution:**

-   **Wait for Initialization**: Allow 15-20 minutes after the cluster reaches the `RUNNING` state for all services to fully initialize.
-   **Verify Security Group**: Ensure that the security group associated with the master node allows inbound traffic on port 9443 (the default port for JupyterHub).
-   **Access via Public DNS**: Use the master node's public DNS name to access JupyterHub: `https://<master-node-public-dns>:9443`.

**Verification:**

-   Check the EMR console to see if the cluster state is `RUNNING` and all applications are started.
-   Try accessing JupyterHub through the web browser after waiting for 15-20 minutes.
-   Verify that the security group allows inbound traffic on port 9443.

## 5. Networking

### 5.1. Problem: Subnet Configuration

**Issue:**

Multiple subnets were available in the VPC, leading to potential confusion and misconfiguration.

**Explanation:**

-   A VPC can have multiple subnets, each spanning a different Availability Zone.
-   Choosing the correct subnet is crucial for network connectivity, latency, and availability.

**Solution:**

-   **Select `subnet-08ea540a579532ef6`**: This subnet resides in the `eu-west-3a` Availability Zone.
-   **Ensure Consistency**: Using the same subnet for all nodes ensures they are in the same Availability Zone, reducing inter-node latency and simplifying network configuration.

**Rationale:**

-   Placing all nodes in the same Availability Zone minimizes latency and improves performance for distributed applications like HBase and Spark.
-   Using a single subnet simplifies network configuration and security group management.

## 6. SSH Issues

### 6.1. Problem 1: Invalid SSH Key Name

**Error Message:**

```
VALIDATION_ERROR_INVALID_SSH_KEY_NAME
Your cluster has terminated because the key pair name that you provided to SSH into the primary instance is invalid
```

**Explanation:**

This error occurs when the specified SSH key pair name does not exist in the selected AWS region (`eu-west-3`).

**Solution:**

1. **Create SSH Key Pair in `eu-west-3`**:
    -   Use the AWS CLI to create a new key pair named "PolePredict Cluster" in the `eu-west-3` region.

    ```bash
    aws ec2 create-key-pair \
        --key-name "PolePredict Cluster" \
        --region eu-west-3 \
        --query 'KeyMaterial' \
        --output text > "PolePredict Cluster.pem"
    ```

    This command creates the key pair and saves the private key to a file named `PolePredict Cluster.pem`.

**Verification:**

-   Verify that the key pair exists in the `eu-west-3` region using the AWS console or the CLI:

    ```bash
    aws ec2 describe-key-pairs --region eu-west-3
    ```

### 6.2. Problem 2: SSH Connection Timeout

**Issue:**

The SSH connection hangs and requires manual termination (Ctrl+C).

**Explanation:**

This typically occurs when the security group associated with the master node does not allow inbound SSH traffic (port 22).

**Solution:**

1. **Get Security Group ID**:
    -   Retrieve the security group ID for the master node using the `describe-cluster` command.

    ```bash
    aws emr describe-cluster --cluster-id <cluster-id> --query 'Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup'
    ```

2. **Add Inbound SSH Rule**:
    -   Use the `authorize-security-group-ingress` command to add an inbound rule allowing SSH traffic (TCP port 22) from your IP address.

    ```bash
    aws ec2 authorize-security-group-ingress \
        --group-id <security-group-id> \
        --protocol tcp \
        --port 22 \
        --cidr <your-ip-address>/32
    ```

    **Important Security Note:** Replace `<your-ip-address>` with your actual public IP address. For testing purposes, you can use `0.0.0.0/0` to allow traffic from any IP, but this is **not recommended for production environments**.

**Verification:**

-   Try connecting to the master node via SSH again. The connection should now succeed without hanging.

### 6.3. Problem 3: WSL SSH Key Permissions

**Error Message:**

```
WARNING: UNPROTECTED PRIVATE KEY FILE!
Permissions 0555 for 'PolePredict Cluster.pem' are too open.
```

**Explanation:**

-   When using WSL (Windows Subsystem for Linux), files stored in Windows-mounted directories (e.g., `/mnt/c/`) may have incorrect permissions when accessed from within WSL.
-   SSH requires strict permissions (0400) on private key files for security reasons.

**Solution:**

1. **Copy Key to WSL Home**:
    -   Copy the key file from the Windows-mounted directory to your WSL home directory.

    ```bash
    cp "/mnt/c/path/to/PolePredict Cluster.pem" ~/
    ```

2. **Set Correct Permissions**:
    -   Change the permissions of the key file within WSL to 0400.

    ```bash
    cd ~
    chmod 400 "PolePredict Cluster.pem"
    ```

3. **Connect from WSL Home**:
    -   Use the key file from your WSL home directory when connecting via SSH.

    ```bash
    ssh -i ~/"PolePredict Cluster.pem" hadoop@<master-public-dns>
    ```

**Verification:**

-   The SSH connection should now succeed without the permission warning.

## 7. Security

### 7.1. Problem 1: IAM Roles Initial Setup

**Issue:**

Uncertainty about which IAM roles are required for EMR cluster creation and operation.

**Explanation:**

-   EMR requires specific IAM roles to access other AWS services on your behalf.
-   Using the correct roles is crucial for security and proper cluster functionality.

**Solution:**

-   **Use Predefined Roles**: Utilize the predefined AWS-managed roles for EMR:
    -   **Service Role**: `AmazonEMR-ServiceRole-20241219T204718` (or a similar, more recent version if available)
    -   **Instance Profile**: `AmazonEMR-InstanceProfile-20241219T204701` (or a similar, more recent version if available)

**Rationale:**

-   These roles are designed specifically for EMR and have the necessary permissions for cluster creation, management, and access to other AWS services.
-   Using predefined roles simplifies the setup process and ensures that the cluster has the required permissions.

### 7.2. Problem 2: Insufficient EC2 Permissions

**Error Message:**

```
Service role arn:aws:iam::891376966635:role/service-role/AmazonEMR-ServiceRole-20241219T204718 has insufficient EC2 permissions.
EC2 Message: You are not authorized to perform: ec2:CreateSecurityGroup
```

**Explanation:**

-   The `AmazonEMR-ServiceRole-20241219T204718` role lacked the necessary permissions to create and manage EC2 security groups, which are essential for EMR cluster operation.

**Solution:**

1. **Go to IAM Console**:
    -   Log in to the AWS Management Console and navigate to the IAM service.

2. **Find the Role**:
    -   Search for the role `AmazonEMR-ServiceRole-20241219T204718` and select it.

3. **Add Permissions**:
    -   You can either add the `AmazonEMR_FullAccess` managed policy (which grants broad EMR permissions) or create a custom policy with the specific permissions required. For this specific error, the following permissions are needed:

    ```json
    {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "ec2:CreateSecurityGroup",
                    "ec2:AuthorizeSecurityGroupIngress",
                    "ec2:DeleteSecurityGroup",
                    "ec2:RevokeSecurityGroupIngress"
                ],
                "Resource": "*"
            }
        ]
    }
    ```

**Rationale:**

-   Adding these permissions allows the EMR service role to create and manage security groups, which are necessary for controlling network access to the cluster nodes.

### 7.3 Problem 3: DataNode Not Starting on Master Node

**Issue:**

```bash
sudo systemctl start hadoop-hdfs-datanode
Job for hadoop-hdfs-datanode.service failed
```

**Explanation:**

This is actually **normal behavior** in a standard EMR setup.
- **Master Node**: Primarily responsible for resource management (YARN) and job coordination, not for storing data (HDFS). It runs the NameNode, but not the DataNode.
- **Core Nodes**: Designed to store data and run the DataNode service.

**Solution:**

- **No action required.** The DataNode should **not** be running on the Master Node. It should only run on Core Nodes.

**Verification:**

```bash
# Check HDFS nodes status
hdfs dfsadmin -report

# Should show:
- NameNode on master node
- Two active DataNodes on core nodes (if you have two core nodes)
- No data corruption or replication issues
```

## 8. Cost Management and Optimization

### 8.1. Cost Overview

**Current Status:**

The current month's cost is $12.47, primarily driven by EC2 compute costs.

![AWS Cost Overview](screenshots/aws_cost_overview.png)

**Breakdown:**

-   **EC2 Compute**: The main cost component, reflecting the usage of master and core node instances.
-   **EMR Service**: Additional costs associated with the EMR service, including MapReduce usage.
-   **Tax**: Standard AWS tax rates applied to the overall usage.
-   **Other Services**: Minimal costs associated with other services, likely related to logging, monitoring, or small data transfers.

### 8.2. Cost Optimization Strategies

1. **Instance Selection Optimization**:
    -   **Right-Sizing**: Continuously evaluate the performance of the cluster and consider downsizing instance types if the current instances are underutilized.
    -   **Spot Instances**: Explore the use of Spot Instances for core nodes, which can offer significant cost savings compared to On-Demand instances. However, be aware of the potential for Spot Instances to be terminated with short notice.
    -   **Reserved Instances**: If the cluster usage is expected to be consistent over a longer period (1 or 3 years), consider purchasing Reserved Instances for cost savings.

2. **Storage Cost Management**:
    -   **EBS Volume Optimization**: Regularly review EBS volume usage and consider deleting any unused or underutilized volumes.
    -   **`gp3` Volumes**: Ensure that `gp3` volumes are being used, as they offer better price/performance compared to `gp2`.
    -   **Lifecycle Policies**: Implement lifecycle policies for S3 buckets used for logging or data archiving to automatically transition older data to cheaper storage classes (e.g., S3 Glacier).
    -   **Cleanup**: Regularly clean up temporary files, old logs, and any other unnecessary data stored in HDFS or S3.

3. **Operational Cost Reduction**:
    -   **Auto-Termination**: Configure auto-termination for development or test clusters that are not needed 24/7. This ensures that the cluster automatically shuts down after a period of inactivity.
    -   **Scheduled Operations**: Schedule data processing jobs and other cluster operations during off-peak hours when Spot Instance prices are typically lower.
    -   **Data Transfer Costs**: Be mindful of data transfer costs, especially when transferring data between regions or to the internet. Optimize data transfer patterns to minimize these costs.
    -   **Monitoring**: Regularly monitor costs using AWS Cost Explorer and set up budget alerts to proactively manage spending.

## 9. Conclusion

This document provides a comprehensive guide to troubleshooting common problems encountered during the setup and operation of the EMR cluster for the F1 data analytics platform. By following the solutions and best practices outlined in this document, you can effectively address issues related to instance types, storage, networking, security, application stack, and cost management, ensuring the smooth and efficient operation of your EMR cluster. Remember to regularly monitor your cluster, review logs, and adapt your configuration as needed to optimize performance and cost-effectiveness.