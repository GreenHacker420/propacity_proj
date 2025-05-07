#!/bin/bash
# Script to build the frontend for AWS deployment

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Building frontend for AWS deployment ===${NC}"

# Check if we're in the project root
if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: frontend directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Create .env file for production
echo -e "\n${GREEN}=== Creating .env file for production ===${NC}"
cat > .env << EOL
VITE_API_URL=/api
EOL

echo "Created .env file with content:"
cat .env

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo -e "\n${GREEN}=== Installing dependencies ===${NC}"
    npm install
else
    echo -e "\n${GREEN}=== Dependencies already installed ===${NC}"
fi

# Build the frontend
echo -e "\n${GREEN}=== Building frontend ===${NC}"
NODE_ENV=production npm run build

# Check if build was successful
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    echo -e "\n${GREEN}=== Build successful! ===${NC}"
    echo "Frontend build is available in the frontend/dist directory"
else
    echo -e "\n${RED}=== Build failed! ===${NC}"
    echo "Please check the error messages above"
    exit 1
fi

# Return to project root
cd ..

echo -e "\n${GREEN}=== Frontend build complete ===${NC}"
echo "You can now deploy the application to AWS using the deploy_aws.sh script"
