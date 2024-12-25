## EMR Cluster Troubleshooting for F1 Data Analytics Platform

This document provides solutions to common problems encountered while setting up and operating an Amazon EMR cluster for the Formula 1 data analytics platform. It focuses on key issues and their resolutions for efficient cluster management.

## Instance Type Availability & Performance

| Problem                                | Explanation                                                                                                | Solution(s)                                                                                                                                                                                          | Verification                                                                                                                                       |
| -------------------------------------- | ---------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `r7g.xlarge` Not Available             | Instance type unavailable in the selected region (`eu-west-3`).                                              | 1. **Change to `r7i.xlarge`**: Similar specs, available in `eu-west-3`. Modify `create_cluster.sh`. <br> 2. **Use `r5.xlarge`**: Generally available, good balance for HBase/Spark. Modify `create_cluster.sh`. <br> 3. **Different Region**: If `r7g.xlarge` is essential. Consider latency/transfer costs. | Use AWS CLI: `aws ec2 describe-instance-type-offerings --location-type availability-zone --filters "Name=instance-type,Values=r7g.xlarge,r7i.xlarge,r5.xlarge" --region eu-west-3` |
| Instance Type Performance (Insufficient) | `t3.small/medium` insufficient memory for sustained HBase/Spark workloads.                                | **Upgrade to `r7i.xlarge` (Core)**: Sufficient memory (32GB). <br> **Select `m7g.xlarge` (Master)**: Balance of compute/memory (16GB).                                                                | N/A - Based on performance observation.                                                                                                            |

## Storage Configuration

| Problem                   | Explanation                                                                                               | Solution(s)                                                                                                                                                                                                                                                                                                                                                                                                                           | Verification                                                                                                                                     |
| ------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| EBS Volume Size           | Initial 32GB EBS insufficient for HDFS replication and overall storage.                                  | **Increase EBS Volume Size**: Core nodes: 150GB, Master node: 50GB in `create_cluster.sh`. <br> **Use `gp3` Volumes**: Improved performance for HBase/Spark.                                                                                                                                                                                                                                                                    | Check EBS volume sizes in the EMR console.                                                                                                   |
| HDFS Replication Factor   | Default replication factor of 3 caused under-replication errors with only two core nodes.                 | 1. **Modify HDFS Configuration**: Set `dfs.replication` to 2 in `hdfs-site.xml` on all nodes. <br> 2. **Modify HBase Configuration**: Set `dfs.replication` to 2 in `hbase-site.xml` on all nodes. <br> 3. **Apply Changes**: Restart NameNode and HBase Master. Manually adjust replication for existing HBase data: `hdfs dfs -setrep -w 2 -R /hbase`.                                                                  | `hdfs getconf -confKey dfs.replication` <br> `hdfs dfsadmin -report` <br> `hdfs fsck /hbase -files -blocks`                                   |

## Application Stack Integration

| Problem             | Explanation                                                                   | Solution                                                                                             | Verification                                                              |
| ------------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| JupyterHub Access   | Not immediately accessible after cluster creation. Services need initialization. | **Wait for Initialization**: 15-20 minutes after cluster reaches `RUNNING`. <br> **Verify Security Group**: Allow inbound on port 9443. <br> **Access via Public DNS**: `https://<master-node-public-dns>:9443`. | Check cluster status in EMR console, then try accessing JupyterHub. |

## Networking

| Problem              | Explanation                                                              | Solution                                                                    | Rationale                                                                        |
| -------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Subnet Configuration | Multiple subnets available, potential for confusion/misconfiguration. | **Select `subnet-08ea540a579532ef6`**:  Resides in `eu-west-3a`.             | Ensures nodes are in the same Availability Zone, reducing latency and simplifying config. |

## SSH Issues

| Problem                   | Explanation                                                                                              | Solution                                                                                                                                                                                                                                                                                                | Verification                                                                                              |
| ------------------------- | -------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| Invalid SSH Key Name      | Specified SSH key pair name doesn't exist in the selected region (`eu-west-3`).                             | **Create SSH Key Pair in `eu-west-3`**: Use AWS CLI: `aws ec2 create-key-pair --key-name "PolePredict Cluster" --region eu-west-3 --query 'KeyMaterial' --output text > "PolePredict Cluster.pem"`.                                                                                                      | `aws ec2 describe-key-pairs --region eu-west-3`                                                           |
| SSH Connection Timeout    | Security group doesn't allow inbound SSH traffic (port 22).                                              | 1. **Get Security Group ID**: `aws emr describe-cluster --cluster-id <cluster-id> --query 'Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup'`. <br> 2. **Add Inbound SSH Rule**: `aws ec2 authorize-security-group-ingress --group-id <security-group-id> --protocol tcp --port 22 --cidr <your-ip-address>/32`. | Try connecting via SSH.                                                                                   |
| WSL SSH Key Permissions   | Incorrect permissions on private key file when accessed from WSL.                                      | 1. **Copy Key to WSL Home**: `cp "/mnt/c/path/to/PolePredict Cluster.pem" ~/`. <br> 2. **Set Correct Permissions**: `cd ~ && chmod 400 "PolePredict Cluster.pem"`. <br> 3. **Connect from WSL Home**: `ssh -i ~/"PolePredict Cluster.pem" hadoop@<master-public-dns>`.                                 | SSH connection should succeed without permission warnings.                                                 |

## Security

| Problem                         | Explanation                                                                                             | Solution                                                                                                                                                              | Rationale                                                                                                                                                                                                                            |
| ------------------------------- | ------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| IAM Roles Initial Setup        | Uncertainty about required IAM roles.                                                                   | **Use Predefined Roles**: <br> - **Service Role**: `AmazonEMR-ServiceRole-20241219T204718` <br> - **Instance Profile**: `AmazonEMR-InstanceProfile-20241219T204701` | Designed for EMR, with necessary permissions for cluster creation and AWS service access.                                                                                                                                           |
| Insufficient EC2 Permissions    | Service role lacks permissions to create security groups.                                               | **Add Permissions to Service Role**: Grant `ec2:CreateSecurityGroup`, `ec2:AuthorizeSecurityGroupIngress`, `ec2:DeleteSecurityGroup`, `ec2:RevokeSecurityGroupIngress`. | Allows EMR to manage security groups for network access control.                                                                                                                                                                        |
| DataNode Not Starting on Master Node | Normal behavior. Master node runs NameNode, Core nodes run DataNode.                                     | **No action required.** DataNode should only run on Core Nodes.                                                                                                    | Master node is for resource management, not data storage. Core nodes are designed for data storage and run the DataNode service.                                                                                                     |

## Cost Management and Optimization

**Current Status:**

The current month's cost is $12.47, primarily driven by EC2 compute costs.

![AWS Cost Overview](screenshots/aws_cost_overview.png)

**Cost Optimization Strategies:**

*   **Instance Selection:**
    *   **Right-Sizing:**  Downsize if underutilized.
    *   **Spot Instances:**  For core nodes (potential savings, risk of termination).
    *   **Reserved Instances:**  For consistent long-term usage.
*   **Storage Cost:**
    *   **EBS Optimization:** Delete unused volumes.
    *   **`gp3` Volumes:**  Ensure usage for better price/performance.
    *   **Lifecycle Policies (S3):**  Move older data to cheaper storage.
    *   **Cleanup:** Remove temporary files and old logs.
*   **Operational Cost:**
    *   **Auto-Termination:** For non-production clusters.
    *   **Scheduled Operations:** During off-peak hours (lower Spot prices).
    *   **Minimize Data Transfer:** Be mindful of inter-region/internet transfers.
    *   **Monitoring:** Use AWS Cost Explorer and set budget alerts.

## Conclusion

This document provides solutions to common EMR cluster issues for the F1 data analytics platform. By understanding these solutions and best practices, you can ensure efficient cluster operation, optimize performance, and manage costs effectively. Continuous monitoring and adaptation are key for maintaining a healthy and cost-effective EMR environment.
