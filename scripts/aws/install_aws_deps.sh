#!/bin/bash
# Script to install AWS dependencies with fallbacks for problematic packages

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Installing AWS dependencies with fallbacks ===${NC}"

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo -e "${YELLOW}Warning: No virtual environment detected${NC}"
    echo "It's recommended to activate your virtual environment first."
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Exiting..."
        exit 1
    fi
fi

# Install base requirements first
echo -e "\n${GREEN}=== Installing base requirements ===${NC}"
pip install -r backend/requirements.txt

# Install production server packages
echo -e "\n${GREEN}=== Installing production server packages ===${NC}"
pip install gunicorn>=21.2.0 uvloop>=0.19.0 httptools>=0.6.0

# Install performance optimization packages with fallbacks
echo -e "\n${GREEN}=== Installing performance optimization packages ===${NC}"

# Try to install aiodns
echo "Installing aiodns..."
pip install aiodns>=3.1.1 || echo -e "${YELLOW}Warning: Failed to install aiodns, skipping...${NC}"

# Install charset-normalizer instead of cchardet
echo "Installing charset-normalizer (alternative to cchardet)..."
pip install charset-normalizer>=3.3.2

# Try to install orjson
echo "Installing orjson..."
pip install orjson>=3.9.10 || echo -e "${YELLOW}Warning: Failed to install orjson, skipping...${NC}"

# Install monitoring packages
echo -e "\n${GREEN}=== Installing monitoring packages ===${NC}"
pip install prometheus-client>=0.17.1 || echo -e "${YELLOW}Warning: Failed to install prometheus-client, skipping...${NC}"

echo -e "\n${GREEN}=== Installation complete ===${NC}"
echo "You can now proceed with the AWS deployment."
