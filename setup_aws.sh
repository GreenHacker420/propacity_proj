#!/bin/bash
# AWS Setup Script for Product Review Analyzer
# This script is executed on the EC2 instance to set up the application

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Setting up Product Review Analyzer on AWS ===${NC}"
echo "Current directory: $(pwd)"

# Update package lists
echo -e "\n${GREEN}=== Updating package lists ===${NC}"
sudo apt update
sudo apt upgrade -y

# Install required packages
echo -e "\n${GREEN}=== Installing required packages ===${NC}"
sudo apt install -y software-properties-common curl gnupg

# Add Python 3.11 repository
echo -e "\n${GREEN}=== Adding Python 3.11 repository ===${NC}"
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update

# Install Python 3.11
echo -e "\n${GREEN}=== Installing Python 3.11 ===${NC}"
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js
echo -e "\n${GREEN}=== Installing Node.js ===${NC}"
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Nginx
echo -e "\n${GREEN}=== Installing Nginx ===${NC}"
sudo apt install -y nginx

# Create Python virtual environment
echo -e "\n${GREEN}=== Creating Python virtual environment ===${NC}"
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo -e "\n${GREEN}=== Installing Python dependencies ===${NC}"
pip install --upgrade pip
pip install -r backend/requirements.txt

# Download NLTK resources
echo -e "\n${GREEN}=== Downloading NLTK resources ===${NC}"
python backend/download_nltk_resources.py

# Install frontend dependencies and build
echo -e "\n${GREEN}=== Setting up frontend ===${NC}"
cd frontend
npm install
npm run build
cd ..

# Configure Nginx
echo -e "\n${GREEN}=== Configuring Nginx ===${NC}"
sudo tee /etc/nginx/sites-available/product-review-analyzer << EOL
server {
    listen 80;
    server_name _;  # Will match any hostname

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

# Enable Nginx site
sudo ln -sf /etc/nginx/sites-available/product-review-analyzer /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# Create systemd service
echo -e "\n${GREEN}=== Creating systemd service ===${NC}"
sudo tee /etc/systemd/system/product-review-analyzer.service << EOL
[Unit]
Description=Product Review Analyzer
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/python serve.py
Restart=always
Environment="PYTHONPATH=$(pwd):$(pwd)/backend"

[Install]
WantedBy=multi-user.target
EOL

# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable product-review-analyzer
sudo systemctl start product-review-analyzer

# Check service status
echo -e "\n${GREEN}=== Checking service status ===${NC}"
sudo systemctl status product-review-analyzer --no-pager

echo -e "\n${GREEN}=== Setup completed successfully ===${NC}"
echo "Your application should now be running at http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo "To check the service logs: sudo journalctl -u product-review-analyzer"
