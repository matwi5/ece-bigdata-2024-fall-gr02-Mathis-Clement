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