#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Checking Product Review Analyzer Deployment ===${NC}"

# Check if Nginx is running
echo -e "\n${YELLOW}Checking Nginx status:${NC}"
if systemctl is-active --quiet nginx; then
    echo -e "${GREEN}Nginx is running${NC}"
else
    echo -e "${RED}Nginx is not running${NC}"
    echo "Try: sudo systemctl start nginx"
fi

# Check if our application service is running
echo -e "\n${YELLOW}Checking Product Review Analyzer service status:${NC}"
if systemctl is-active --quiet product-review-analyzer; then
    echo -e "${GREEN}Product Review Analyzer service is running${NC}"
else
    echo -e "${RED}Product Review Analyzer service is not running${NC}"
    echo "Try: sudo systemctl start product-review-analyzer"
    echo "Check logs: sudo journalctl -u product-review-analyzer -f"
fi

# Check if the backend API is accessible
echo -e "\n${YELLOW}Checking backend API:${NC}"
if curl -s http://localhost:8000/api/health | grep -q "status"; then
    echo -e "${GREEN}Backend API is accessible${NC}"
else
    echo -e "${RED}Backend API is not accessible${NC}"
    echo "Check if the backend is running on port 8000"
fi

# Check if the frontend is being served by Nginx
echo -e "\n${YELLOW}Checking frontend:${NC}"
if curl -s -I http://localhost | grep -q "200 OK"; then
    echo -e "${GREEN}Frontend is being served by Nginx${NC}"
else
    echo -e "${RED}Frontend is not being served by Nginx${NC}"
    echo "Check Nginx configuration and logs"
fi

echo -e "\n${GREEN}=== Deployment check completed ===${NC}"
