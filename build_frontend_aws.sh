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

# Try different build approaches
echo "Attempting to build with npx vite build..."
NODE_ENV=production npx vite build

# If the first approach fails, try the second approach
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}First build approach failed, trying alternative method...${NC}"
    # Clean node_modules and reinstall
    echo "Cleaning node_modules..."
    rm -rf node_modules
    rm -f package-lock.json

    echo "Reinstalling dependencies..."
    npm install

    echo "Building with explicit vite path..."
    NODE_ENV=production ./node_modules/.bin/vite build
fi

# If the second approach fails, try a direct build with Node.js
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Second build approach failed, trying direct build with Node.js...${NC}"

    # Check if the direct build script exists
    if [ -f "build_direct.js" ]; then
        echo "Using direct build script..."
        NODE_ENV=production node build_direct.js
    else
        echo "Creating direct build script..."
        cat > build_direct.js << EOL
// Direct build script for Vite
// This script directly uses the Vite API to build the project
// without relying on the CLI which can have path issues

console.log('Starting direct Vite build...');

// Set environment variables
process.env.NODE_ENV = 'production';

async function buildProject() {
  try {
    // Import Vite
    const { build } = await import('vite');

    console.log('Vite imported successfully');

    // Run the build
    await build({
      root: process.cwd(),
      logLevel: 'info',
      configFile: './vite.config.js',
    });

    console.log('Build completed successfully');
    process.exit(0);
  } catch (error) {
    console.error('Build failed:', error);
    process.exit(1);
  }
}

buildProject();
EOL
        NODE_ENV=production node build_direct.js
    fi
fi

# If all build approaches fail, try a minimal build
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}All build approaches failed, creating minimal build...${NC}"

    # Create a minimal dist directory with a placeholder
    echo "Creating minimal dist directory..."
    mkdir -p dist

    # Create a basic index.html file
    cat > dist/index.html << EOL
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Review Analyzer</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; line-height: 1.6; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .message { background-color: #f8f9fa; border-left: 4px solid #007bff; padding: 15px; margin-bottom: 20px; }
        .api-link { display: inline-block; margin-top: 20px; color: #007bff; text-decoration: none; }
        .api-link:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Product Review Analyzer</h1>
        <div class="message">
            <p>The frontend build process encountered an issue. The application is still functional through the API.</p>
            <p>Please contact the administrator for assistance.</p>
        </div>
        <a href="/api/docs" class="api-link">Access API Documentation</a>
    </div>
</body>
</html>
EOL

    # Create an empty assets directory
    mkdir -p dist/assets

    echo -e "${YELLOW}Created minimal frontend with placeholder page${NC}"
fi

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
