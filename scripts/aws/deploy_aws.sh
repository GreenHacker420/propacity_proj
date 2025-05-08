#!/bin/bash
# AWS Deployment Script for Product Review Analyzer
# This script helps deploy the application to an EC2 instance

# Exit on error
set -e

# Configuration
EC2_USER="ubuntu"
EC2_HOST=""
PEM_FILE=""
APP_NAME="product-review-analyzer"
DEPLOY_DIR="/home/$EC2_USER/$APP_NAME"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to display usage
usage() {
    echo -e "${YELLOW}Usage:${NC} $0 -h <EC2_HOST> -k <PEM_FILE> [-u <EC2_USER>] [-d <DEPLOY_DIR>]"
    echo -e "  -h EC2_HOST     EC2 instance hostname or IP address"
    echo -e "  -k PEM_FILE     Path to the .pem key file for SSH access"
    echo -e "  -u EC2_USER     EC2 user (default: ubuntu)"
    echo -e "  -d DEPLOY_DIR   Deployment directory on EC2 (default: /home/\$EC2_USER/$APP_NAME)"
    exit 1
}

# Parse command line arguments
while getopts "h:k:u:d:" opt; do
    case $opt in
        h) EC2_HOST="$OPTARG" ;;
        k) PEM_FILE="$OPTARG" ;;
        u) EC2_USER="$OPTARG" ;;
        d) DEPLOY_DIR="$OPTARG" ;;
        *) usage ;;
    esac
done

# Check required parameters
if [ -z "$EC2_HOST" ] || [ -z "$PEM_FILE" ]; then
    echo -e "${RED}Error:${NC} EC2_HOST and PEM_FILE are required."
    usage
fi

# Check if PEM file exists
if [ ! -f "$PEM_FILE" ]; then
    echo -e "${RED}Error:${NC} PEM file not found: $PEM_FILE"
    exit 1
fi

echo -e "${GREEN}=== Deploying to AWS EC2 ===${NC}"
echo -e "Host: $EC2_HOST"
echo -e "User: $EC2_USER"
echo -e "Deploy Directory: $DEPLOY_DIR"

# Function to run SSH commands
run_ssh() {
    ssh -i "$PEM_FILE" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "$1"
}

# Function to run SCP commands
run_scp() {
    scp -i "$PEM_FILE" -o StrictHostKeyChecking=no "$1" "$EC2_USER@$EC2_HOST:$2"
}

# Check if we can connect to the EC2 instance
echo -e "\n${GREEN}=== Checking SSH connection ===${NC}"
if ! run_ssh "echo 'SSH connection successful'"; then
    echo -e "${RED}Error:${NC} Failed to connect to EC2 instance"
    exit 1
fi

# Create deployment directory if it doesn't exist
echo -e "\n${GREEN}=== Creating deployment directory ===${NC}"
run_ssh "mkdir -p $DEPLOY_DIR"

# Create a temporary directory for the build
echo -e "\n${GREEN}=== Creating local build ===${NC}"
TMP_DIR=$(mktemp -d)
echo "Temporary directory: $TMP_DIR"

# Copy necessary files to the temporary directory
echo "Copying files to temporary directory..."
cp -r backend frontend *.py *.sh Dockerfile .dockerignore "$TMP_DIR"
mkdir -p "$TMP_DIR/docs"
cp -r docs/deployment "$TMP_DIR/docs/"
mkdir -p "$TMP_DIR/scripts/aws"
cp -r scripts/aws/* "$TMP_DIR/scripts/aws/"

# Create .env file from .env.example if it doesn't exist
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}Warning:${NC} backend/.env not found. Creating from .env.example..."
    cp backend/.env.example "$TMP_DIR/backend/.env"
else
    cp backend/.env "$TMP_DIR/backend/.env"
fi

# Create a deployment package
echo -e "\n${GREEN}=== Creating deployment package ===${NC}"
DEPLOY_PACKAGE="$APP_NAME-deploy.tar.gz"
tar -czf "$DEPLOY_PACKAGE" -C "$TMP_DIR" .
echo "Created deployment package: $DEPLOY_PACKAGE"

# Upload the deployment package
echo -e "\n${GREEN}=== Uploading deployment package ===${NC}"
run_scp "$DEPLOY_PACKAGE" "$DEPLOY_DIR/"

# Extract the deployment package on the EC2 instance
echo -e "\n${GREEN}=== Extracting deployment package ===${NC}"
run_ssh "cd $DEPLOY_DIR && tar -xzf $DEPLOY_PACKAGE && rm $DEPLOY_PACKAGE"

# Install dependencies and set up the application
echo -e "\n${GREEN}=== Setting up the application ===${NC}"
run_ssh "cd $DEPLOY_DIR && chmod +x scripts/aws/setup_aws.sh && ./scripts/aws/setup_aws.sh"

# Clean up
echo -e "\n${GREEN}=== Cleaning up ===${NC}"
rm -rf "$TMP_DIR" "$DEPLOY_PACKAGE"

echo -e "\n${GREEN}=== Deployment completed successfully ===${NC}"
echo -e "Your application is now deployed to: $EC2_HOST"
echo -e "You can access it at: http://$EC2_HOST"
echo -e "\nTo SSH into your instance:"
echo -e "ssh -i $PEM_FILE $EC2_USER@$EC2_HOST"
