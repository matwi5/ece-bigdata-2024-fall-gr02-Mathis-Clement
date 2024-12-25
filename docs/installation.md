# EMR Cluster Installation Guide

## Prerequisites
- AWS CLI installed
- AWS credentials configured
- SSH key pair "PolePredict Cluster"
- Appropriate IAM roles and permissions
- VPC and subnet configured

## Step-by-Step Installation

### 1. AWS CLI Setup
```bash
# Install AWS CLI
sudo apt-get update
sudo apt-get install awscli

# Configure AWS CLI
aws configure
# Enter your credentials when prompted
```

### 2. Verify Infrastructure
```bash
# Check VPC configuration
aws ec2 describe-vpcs

# Check available subnets
aws ec2 describe-subnets

# Verify EMR IAM roles
aws iam list-roles | grep -E "EMR|emr"
```

### 3. Create EMR Cluster
1. Create script file `create_cluster.sh`:
```bash
#!/bin/bash

CLUSTER_NAME="BigData-HBase-Spark"
REGION="eu-west-3"
EMR_VERSION="emr-7.5.0"
LOG_URI="s3://aws-logs-891376966635-eu-west-3/elasticmapreduce"
SERVICE_ROLE="arn:aws:iam::891376966635:role/service-role/AmazonEMR-ServiceRole-20241219T204718"
SUBNET_ID="subnet-08ea540a579532ef6"

aws emr create-cluster \
  --name "${CLUSTER_NAME}" \
  --release-label "${EMR_VERSION}" \
  --region "${REGION}" \
  --log-uri "${LOG_URI}" \
  --service-role "${SERVICE_ROLE}" \
  --applications Name=Hadoop Name=HBase Name=Spark Name=ZooKeeper Name=JupyterHub Name=Livy \
  --unhealthy-node-replacement \
  --tags 'for-use-with-amazon-emr-managed-policies=true' \
  --ec2-attributes "{
    \"InstanceProfile\":\"AmazonEMR-InstanceProfile-20241219T204701\",
    \"SubnetId\":\"${SUBNET_ID}\",
    \"KeyName\":\"PolePredict Cluster\"
  }" \
  --instance-groups "[
    {
      \"InstanceCount\":1,
      \"InstanceGroupType\":\"MASTER\",
      \"Name\":\"Primary\",
      \"InstanceType\":\"m7g.xlarge\",
      \"EbsConfiguration\":{
        \"EbsBlockDeviceConfigs\":[
          {
            \"VolumeSpecification\":{
              \"VolumeType\":\"gp3\",
              \"SizeInGB\":50
            },
            \"VolumesPerInstance\":1
          }
        ]
      }
    },
    {
      \"InstanceCount\":2,
      \"InstanceGroupType\":\"CORE\",
      \"Name\":\"Core\",
      \"InstanceType\":\"r7i.xlarge\",
      \"EbsConfiguration\":{
        \"EbsBlockDeviceConfigs\":[
          {
            \"VolumeSpecification\":{
              \"VolumeType\":\"gp3\",
              \"SizeInGB\":150
            },
            \"VolumesPerInstance\":1
          }
        ]
      }
    }
  ]" \
  --scale-down-behavior "TERMINATE_AT_TASK_COMPLETION" \
  --ebs-root-volume-size "50"
```

2. Make script executable:
```bash
chmod +x create_cluster.sh
```

3. Run script:
```bash
./create_cluster.sh
```

### 4. Verify Cluster Creation
```bash
# Get cluster status
aws emr describe-cluster --cluster-id <your-cluster-id>

# List active clusters
aws emr list-clusters --active
```

### 5. Access Cluster

#### Configure SSH Access
1. Get master node DNS:
```bash
aws emr describe-cluster --cluster-id <cluster-id> --query 'Cluster.MasterPublicDnsName'
```

2. Configure security group:
```bash
# Get security group ID
aws emr describe-cluster --cluster-id <cluster-id> --query 'Cluster.Ec2InstanceAttributes.EmrManagedMasterSecurityGroup'

# Add SSH access
aws ec2 authorize-security-group-ingress \
    --group-id <security-group-id> \
    --protocol tcp \
    --port 22 \
    --cidr 0.0.0.0/0
```

3. Set up SSH key (WSL users):
```bash
# Copy key to WSL home directory
cp "PolePredict Cluster.pem" ~/
cd ~
chmod 400 "PolePredict Cluster.pem"

# Connect to cluster
ssh -i "PolePredict Cluster.pem" hadoop@<master-node-public-dns>
```

4. Set up SSH key (non-WSL users):
```bash
chmod 400 "PolePredict Cluster.pem"
ssh -i "PolePredict Cluster.pem" hadoop@<master-node-public-dns>
```

#### Access Web Interfaces
```bash
# JupyterHub
https://<master-node-public-dns>:9443

# HBase UI
http://<master-node-public-dns>:16010

# Spark History Server
http://<master-node-public-dns>:18080
```