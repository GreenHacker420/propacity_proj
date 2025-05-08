# AWS Deployment Guide

This guide provides detailed instructions for deploying the Product Review Analyzer on Amazon Web Services (AWS).

## Prerequisites

Before deploying to AWS, ensure you have:

1. **AWS Account**: Active AWS account with appropriate permissions
2. **MongoDB Atlas Account**: For database storage (already set up)
3. **Google Gemini API Key**: For advanced AI analysis
4. **Domain Name** (Optional): For custom domain setup

## AWS Services Used

This deployment utilizes the following AWS services:

- **Amazon EC2**: For hosting the application
- **Amazon S3** (Optional): For static file storage
- **Amazon CloudFront** (Optional): For content delivery
- **Amazon Route 53** (Optional): For domain management
- **AWS Elastic Load Balancer** (Optional): For load balancing

## Deployment Options

1. **EC2 Direct Deployment**: Deploy directly on an EC2 instance
2. **Docker on EC2**: Deploy using Docker on EC2
3. **Elastic Beanstalk**: Managed deployment with Elastic Beanstalk

## EC2 Direct Deployment

### Step 1: Launch an EC2 Instance

1. Log in to the AWS Management Console
2. Navigate to EC2 service
3. Click "Launch Instance"
4. Choose an Amazon Machine Image (AMI):
   - Recommended: Ubuntu Server 22.04 LTS
5. Choose an Instance Type:
   - Recommended: t2.medium or larger (for ML workloads)
6. Configure Instance Details:
   - Default VPC is fine for basic deployment
   - Enable Auto-assign Public IP
7. Add Storage:
   - Recommended: At least 20GB
8. Add Tags (Optional):
   - Key: Name, Value: product-review-analyzer
9. Configure Security Group:
   - Create a new security group
   - Add rules for HTTP (80), HTTPS (443), and SSH (22)
10. Review and Launch
11. Create or select an existing key pair for SSH access

### Step 2: Connect to Your EC2 Instance

```bash
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-dns
```

### Step 3: Install Required Software

```bash
# Update package lists
sudo apt update
sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install pip
sudo apt install -y python3-pip

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Git
sudo apt install -y git

# Install Docker (optional, for Docker deployment)
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

### Step 4: Clone the Repository

```bash
git clone https://github.com/yourusername/product-review-analyzer.git
cd product-review-analyzer
```

### Step 5: Set Up Environment Variables

```bash
# Create .env file in the backend directory
cat > backend/.env << EOL
MONGODB_URI=your_mongodb_uri
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_MODEL=models/gemini-2.0-flash
PORT=8000
HOST=0.0.0.0
DEVELOPMENT_MODE=false
EOL
```

### Step 6: Install Dependencies

```bash
# Create and activate virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.aws.txt  # Use AWS-specific requirements for production
# Or if the file doesn't exist:
# pip install -r backend/requirements.txt

# Download NLTK resources
python backend/download_nltk_resources.py

# Install frontend dependencies
cd frontend
npm install
```

The `requirements.aws.txt` file includes additional dependencies optimized for production deployment:
- `gunicorn`: Production-grade WSGI server
- `uvloop`: Ultra-fast asyncio event loop
- `httptools`: Fast HTTP parsing
- Additional performance optimizations

For easier installation with fallbacks for problematic packages, you can use the provided script:
```bash
./install_aws_deps.sh
```

This script will handle installation of all required dependencies and provide fallbacks for packages that might have compilation issues on certain platforms.

### Step 7: Build the Frontend

```bash
# Build the frontend
npm run build
cd ..
```

### Step 8: Set Up Nginx as a Reverse Proxy

```bash
# Install Nginx
sudo apt install -y nginx

# Create Nginx configuration
sudo tee /etc/nginx/sites-available/product-review-analyzer << EOL
server {
    listen 80;
    server_name your-domain.com;  # Replace with your domain or EC2 public IP

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }
}
EOL

# Enable the site
sudo ln -s /etc/nginx/sites-available/product-review-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 9: Set Up Systemd Service

```bash
# Create a systemd service file
sudo tee /etc/systemd/system/product-review-analyzer.service << EOL
[Unit]
Description=Product Review Analyzer
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/product-review-analyzer
ExecStart=/home/ubuntu/product-review-analyzer/venv/bin/python serve.py
Restart=always
Environment="PYTHONPATH=/home/ubuntu/product-review-analyzer:/home/ubuntu/product-review-analyzer/backend"

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
sudo systemctl enable product-review-analyzer
sudo systemctl start product-review-analyzer
```

## Docker on EC2 Deployment

### Step 1: Launch an EC2 Instance

Follow the same steps as in the EC2 Direct Deployment section.

### Step 2: Connect to Your EC2 Instance

```bash
ssh -i /path/to/your-key.pem ubuntu@your-ec2-public-dns
```

### Step 3: Install Docker

```bash
sudo apt update
sudo apt install -y docker.io
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

### Step 4: Clone the Repository

```bash
git clone https://github.com/yourusername/product-review-analyzer.git
cd product-review-analyzer
```

### Step 5: Set Up Environment Variables

```bash
# Create .env file
cat > .env << EOL
MONGODB_URI=your_mongodb_uri
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
GEMINI_MODEL=models/gemini-2.0-flash
PORT=8000
HOST=0.0.0.0
DEVELOPMENT_MODE=false
EOL
```

### Step 6: Build and Run Docker Container

```bash
# Build the Docker image
docker build -t product-review-analyzer .

# Run the container
docker run -d -p 80:8000 --env-file .env --name product-review-analyzer product-review-analyzer
```

## SSL/TLS Setup with Let's Encrypt

If you have a domain name pointing to your EC2 instance, you can set up SSL/TLS:

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain and install certificate
sudo certbot --nginx -d your-domain.com

# Certbot will automatically update your Nginx configuration
```

## Monitoring and Maintenance

### Setting Up CloudWatch Monitoring

```bash
# Install CloudWatch agent
sudo apt install -y amazon-cloudwatch-agent

# Configure CloudWatch agent
sudo tee /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json << EOL
{
  "metrics": {
    "metrics_collected": {
      "cpu": {
        "measurement": ["cpu_usage_idle", "cpu_usage_user", "cpu_usage_system"]
      },
      "mem": {
        "measurement": ["mem_used_percent"]
      },
      "disk": {
        "measurement": ["disk_used_percent"],
        "resources": ["/"]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "product-review-analyzer-syslog",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/home/ubuntu/product-review-analyzer/app.log",
            "log_group_name": "product-review-analyzer-app",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
EOL

# Start CloudWatch agent
sudo systemctl enable amazon-cloudwatch-agent
sudo systemctl start amazon-cloudwatch-agent
```

## Backup and Disaster Recovery

### Database Backup

MongoDB Atlas provides automated backups. Ensure your MongoDB Atlas cluster has backups enabled.

### Application Backup

Set up a cron job to back up your application code and configuration:

```bash
# Create a backup script
cat > /home/ubuntu/backup.sh << EOL
#!/bin/bash
BACKUP_DIR=/home/ubuntu/backups
mkdir -p \$BACKUP_DIR
TIMESTAMP=\$(date +%Y%m%d%H%M%S)
tar -czf \$BACKUP_DIR/product-review-analyzer-\$TIMESTAMP.tar.gz -C /home/ubuntu product-review-analyzer
# Upload to S3 (optional)
# aws s3 cp \$BACKUP_DIR/product-review-analyzer-\$TIMESTAMP.tar.gz s3://your-bucket/backups/
EOL

# Make the script executable
chmod +x /home/ubuntu/backup.sh

# Add to crontab (daily backup at 2 AM)
(crontab -l 2>/dev/null; echo "0 2 * * * /home/ubuntu/backup.sh") | crontab -
```

## Troubleshooting

### Common Issues

1. **Application Not Starting**:
   - Check systemd service status: `sudo systemctl status product-review-analyzer`
   - Check logs: `sudo journalctl -u product-review-analyzer`

2. **Nginx Not Working**:
   - Check Nginx status: `sudo systemctl status nginx`
   - Check Nginx error logs: `sudo cat /var/log/nginx/error.log`

3. **MongoDB Connection Issues**:
   - Ensure MongoDB Atlas IP whitelist includes your EC2 instance's public IP
   - Check MongoDB connection string in `.env` file

4. **SSL Certificate Issues**:
   - Check Certbot logs: `sudo cat /var/log/letsencrypt/letsencrypt.log`
   - Renew certificate: `sudo certbot renew`

5. **Frontend Build Issues**:
   - If you encounter errors during frontend build like `SyntaxError: Cannot use import statement outside a module` or `Cannot find module '/node_modules/dist/node/cli.js'`, it's likely a Vite/Node.js compatibility issue
   - Solutions:

     a) Use the enhanced build script that tries multiple approaches:
     ```bash
     ./build_frontend_aws.sh
     ```

     b) If that fails, use the Vite fix script that updates package.json with compatible versions:
     ```bash
     ./fix_vite_build.sh
     ```

     c) For manual fixing:
     ```bash
     cd frontend
     # Downgrade Vite to a more stable version
     npm uninstall vite
     npm install vite@4.5.0
     # Build using the Node.js API directly
     node -e "import('vite').then(v => v.build({root: process.cwd()}))"
     ```

6. **Python Package Installation Issues**:
   - If you encounter errors like `error: command '/usr/bin/x86_64-linux-gnu-g++' failed with exit code 1` when installing packages like `cchardet`
   - Solution: Use the provided installation script that includes fallbacks:
     ```bash
     ./install_aws_deps.sh
     ```
   - For specific package issues:
     - For `cchardet`: Use `charset-normalizer` as an alternative
     - For C extension errors: Install development packages with:
       ```bash
       sudo apt-get install python3.11-dev build-essential
       ```

## Security Best Practices

1. **Keep Software Updated**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

2. **Use Security Groups Effectively**:
   - Limit SSH access to your IP address
   - Only open necessary ports

3. **Enable AWS CloudTrail**:
   - For auditing and monitoring AWS API calls

4. **Use IAM Roles**:
   - Create and use IAM roles with least privilege

5. **Regularly Rotate Credentials**:
   - Update API keys and passwords regularly

## Cost Optimization

1. **Right-size EC2 Instances**:
   - Start with t2.medium and adjust based on usage

2. **Use Reserved Instances**:
   - For long-term cost savings

3. **Monitor Usage**:
   - Set up AWS Budgets to monitor costs
   - Use CloudWatch to track resource utilization

## Additional Resources

- [AWS Documentation](https://docs.aws.amazon.com/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
