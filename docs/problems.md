# EMR Cluster Problems and Solutions

## Instance Type Availability Issues

### Problem 1: r7g.xlarge Not Available
**Error Message:**
```
An error occurred (ValidationException) when calling the RunJobFlow operation: Instance type 'r7g.xlarge' is not supported.
```

**Solution:**
- Changed instance type to r7i.xlarge which is available in eu-west-3 region
- Alternative solution would be to use r5.xlarge

### Problem 2: Instance Type Performance
**Observation:**
Initially planned to use t3.small/medium instances for cost savings.

**Solution:**
- Opted for r7i.xlarge for core nodes to ensure adequate memory for HBase
- Selected m7g.xlarge for master node to handle cluster management efficiently

## Storage Configuration

### Problem: EBS Volume Size
**Issue:**
Initial 32GB storage was insufficient for HDFS replication.

**Solution:**
- Increased EBS volume size to 150GB for core nodes
- Configured gp3 volumes for better performance
- Set 50GB for master node

## Application Stack Integration

### Problem: JupyterHub Access
**Issue:**
JupyterHub not accessible after cluster creation.

**Solution:**
- Wait for cluster to fully initialize (takes ~15-20 minutes)
- Verify security group allows inbound traffic on port 9443
- Access via master node public DNS

## Networking

### Problem: Subnet Configuration
**Issue:**
Multiple subnets available in VPC.

**Solution:**
- Selected subnet-08ea540a579532ef6 in eu-west-3a
- Ensures all nodes are in same availability zone
- Reduces inter-node latency

## SSH Key Issues

### Problem: Invalid SSH Key Name
**Error Message:**
```
VALIDATION_ERROR_INVALID_SSH_KEY_NAME
Your cluster has terminated because the key pair name that you provided to SSH into the primary instance is invalid
```

**Solution:**
1. Create SSH key pair in eu-west-3 region:
```bash
aws ec2 create-key-pair \
    --key-name "PolePredict Cluster" \
    --region eu-west-3 \
    --query 'KeyMaterial' \
    --output text > "PolePredict Cluster.pem"
```
2. Secure the key file:
```bash
chmod 400 "PolePredict Cluster.pem"
```
3. Re-run cluster creation script

## Security

### Problem 1: IAM Roles Initial Setup
**Issue:**
Understanding which IAM roles are needed.

**Solution:**
Using predefined roles:
- Service role: AmazonEMR-ServiceRole-20241219T204718
- Instance profile: AmazonEMR-InstanceProfile-20241219T204701

### Problem 2: Insufficient EC2 Permissions
**Error Message:**
```
Service role arn:aws:iam::891376966635:role/service-role/AmazonEMR-ServiceRole-20241219T204718 has insufficient EC2 permissions.
EC2 Message: You are not authorized to perform: ec2:CreateSecurityGroup
```

**Solution:**
1. Go to IAM Console
2. Find the role "AmazonEMR-ServiceRole-20241219T204718"
3. Add the following permissions (via AmazonEMR_FullAccess or custom policy):
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

## Best Practices Learned

1. Instance Selection
- Always verify instance availability in target region
- Use AWS CLI to check instance type support
- Consider memory requirements for HBase

2. Storage Planning
- Calculate storage needs including replication factor
- Use gp3 volumes for better performance
- Allocate sufficient space for logs and temporary files

3. Networking
- Use same subnet for all nodes
- Verify security group configurations
- Enable required ports for services

4. Monitoring
- Regular checks using `describe-cluster`
- Monitor CloudWatch metrics
- Review EMR logs in S3