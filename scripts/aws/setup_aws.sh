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

# Install Node.js (using version 20 for better ES modules support)
echo -e "\n${GREEN}=== Installing Node.js ===${NC}"
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verify Node.js version
echo "Node.js version: $(node --version)"
echo "npm version: $(npm --version)"

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

# Check if install_aws_deps.sh script exists
if [ -f "install_aws_deps.sh" ]; then
    echo "Using AWS dependencies installation script..."
    chmod +x install_aws_deps.sh
    ./install_aws_deps.sh
else
    # Check if AWS requirements file exists
    if [ -f "backend/requirements.aws.txt" ]; then
        echo "Installing AWS-specific requirements..."
        # Try to install with pip, but continue even if some packages fail
        pip install -r backend/requirements.aws.txt || {
            echo -e "${YELLOW}Warning: Some AWS packages failed to install.${NC}"
            echo "Falling back to standard requirements..."
            pip install -r backend/requirements.txt

            # Try to install critical production packages individually
            echo "Installing critical production packages individually..."
            pip install gunicorn uvloop httptools || echo "Failed to install some production packages."
        }
    else
        echo "AWS requirements file not found, using standard requirements..."
        pip install -r backend/requirements.txt
    fi
fi

# Download NLTK resources
echo -e "\n${GREEN}=== Downloading NLTK resources ===${NC}"
python backend/download_nltk_resources.py

# Install frontend dependencies and build
echo -e "\n${GREEN}=== Setting up frontend ===${NC}"
cd frontend

# Create a .env file for production
echo "Creating .env file for production..."
cat > .env << EOL
VITE_API_URL=/api
EOL

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Build the frontend
echo "Building frontend..."
NODE_ENV=production npm run build

# Check if build was successful
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    echo -e "${GREEN}Frontend build successful!${NC}"
else
    echo -e "${YELLOW}Warning: Frontend build failed. Trying alternative build method...${NC}"

    # Check if fix_vite_build.sh exists in the parent directory
    if [ -f "../scripts/aws/fix_vite_build.sh" ]; then
        echo "Using fix_vite_build.sh script..."
        chmod +x ../scripts/aws/fix_vite_build.sh
        ../scripts/aws/fix_vite_build.sh
    else
        echo "fix_vite_build.sh not found, trying direct fix..."

        # Try to fix Vite issues directly
        echo "Cleaning node_modules..."
        rm -rf node_modules
        rm -f package-lock.json

        echo "Installing specific Vite version..."
        npm install
        npm install vite@4.5.0 --save-dev

        echo "Trying build again with specific Vite version..."
        NODE_ENV=production npx vite build

        # If still not successful, create minimal dist directory
        if [ ! -d "dist" ] || [ ! "$(ls -A dist)" ]; then
            echo "Creating minimal dist directory..."
            mkdir -p dist
            echo "<html><body><h1>Product Review Analyzer</h1><p>Frontend build failed. Please check the logs.</p></body></html>" > dist/index.html
        fi
    fi
fi

cd ..

# Configure Nginx
echo -e "\n${GREEN}=== Configuring Nginx ===${NC}"
sudo tee /etc/nginx/sites-available/product-review-analyzer << EOL
server {
    listen 80;
    server_name _;  # Will match any hostname

    # Serve frontend static files directly
    location / {
        root $(pwd)/frontend/dist;
        index index.html;
        try_files \$uri \$uri/ /index.html;
    }

    # Proxy API requests to the backend
    location /api {
        proxy_pass http://localhost:8000/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Serve API documentation
    location /docs {
        proxy_pass http://localhost:8000/docs;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # Serve OpenAPI schema
    location /openapi.json {
        proxy_pass http://localhost:8000/openapi.json;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
    }

    # WebSocket support
    location /ws {
        proxy_pass http://localhost:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
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

# Check if gunicorn is available
if $(pwd)/venv/bin/pip show gunicorn > /dev/null 2>&1; then
    echo "Using Gunicorn for production deployment..."
    sudo tee /etc/systemd/system/product-review-analyzer.service << EOL
[Unit]
Description=Product Review Analyzer
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$(pwd)
ExecStart=$(pwd)/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --access-logfile - --error-logfile - serve:app
Restart=always
Environment="PYTHONPATH=$(pwd):$(pwd)/backend"
Environment="DEVELOPMENT_MODE=false"

[Install]
WantedBy=multi-user.target
EOL
else
    echo "Gunicorn not found, using standard Python server..."
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
Environment="DEVELOPMENT_MODE=false"

[Install]
WantedBy=multi-user.target
EOL
fi

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
