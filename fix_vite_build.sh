#!/bin/bash
# Script to fix Vite build issues by updating package.json and reinstalling dependencies

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Fixing Vite build issues ===${NC}"

# Check if we're in the project root
if [ ! -d "frontend" ]; then
    echo -e "${RED}Error: frontend directory not found${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Backup the original package.json
echo "Backing up original package.json..."
cp package.json package.json.bak

# Update package.json to use specific versions known to work together
echo "Updating package.json with compatible versions..."
cat > package.json << EOL
{
  "name": "frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "keywords": [],
  "author": "",
  "license": "ISC",
  "description": "",
  "dependencies": {
    "@chakra-ui/react": "^3.0.0",
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "@headlessui/react": "^1.7.17",
    "@heroicons/react": "^2.0.18",
    "axios": "^1.6.2",
    "framer-motion": "^10.16.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.3",
    "react-intersection-observer": "^9.5.2",
    "react-router-dom": "^6.20.0",
    "react-spinners": "^0.13.8",
    "react-syntax-highlighter": "^15.5.0",
    "recharts": "^2.9.0",
    "tailwindcss": "^3.3.5"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "autoprefixer": "^10.4.16",
    "postcss": "^8.4.31",
    "terser": "^5.24.0",
    "vite": "^4.5.0"
  }
}
EOL

echo "Cleaning node_modules and package-lock.json..."
rm -rf node_modules
rm -f package-lock.json

echo "Installing dependencies with the updated package.json..."
npm install

echo "Creating a simple build script..."
cat > simple-build.js << EOL
// Simple build script that doesn't rely on the Vite CLI
import { build } from 'vite';

// Set environment variables
process.env.NODE_ENV = 'production';

console.log('Starting Vite build...');

build({
  root: process.cwd(),
  logLevel: 'info',
  configFile: './vite.config.js',
})
  .then(() => {
    console.log('Build completed successfully');
    process.exit(0);
  })
  .catch((error) => {
    console.error('Build failed:', error);
    process.exit(1);
  });
EOL

echo "Building with the simple build script..."
node simple-build.js

# Check if build was successful
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    echo -e "\n${GREEN}=== Build successful! ===${NC}"
    echo "Frontend build is available in the frontend/dist directory"
else
    echo -e "\n${RED}=== Build failed! ===${NC}"
    echo "Please check the error messages above"
    
    # Restore the original package.json
    echo "Restoring original package.json..."
    mv package.json.bak package.json
    
    exit 1
fi

# Return to project root
cd ..

echo -e "\n${GREEN}=== Vite build fix complete ===${NC}"
echo "You can now deploy the application to AWS using the deploy_aws.sh script"
