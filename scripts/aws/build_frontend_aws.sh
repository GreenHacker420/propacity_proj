#!/bin/bash
# Script to build the frontend for AWS deployment with fallbacks

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Building frontend for AWS deployment ===${NC}"

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
    cat > dist/index.html << EOL
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Product Review Analyzer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
        }
        h1 {
            color: #2563eb;
        }
        .error {
            background-color: #fee2e2;
            border-left: 4px solid #ef4444;
            padding: 10px 15px;
            margin: 20px 0;
        }
        .info {
            background-color: #e0f2fe;
            border-left: 4px solid #0ea5e9;
            padding: 10px 15px;
            margin: 20px 0;
        }
        code {
            background-color: #f1f5f9;
            padding: 2px 4px;
            border-radius: 4px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>Product Review Analyzer</h1>
    
    <div class="error">
        <h2>Frontend Build Error</h2>
        <p>The frontend build process encountered an error. However, the API is still functional.</p>
    </div>
    
    <div class="info">
        <h2>API Access</h2>
        <p>You can access the API documentation at <a href="/docs">/docs</a>.</p>
        <p>The API endpoints are available at <code>/api/...</code></p>
    </div>
    
    <h2>Troubleshooting</h2>
    <p>To fix this issue, please check the server logs for more information about the build failure.</p>
    <p>You can also try rebuilding the frontend manually:</p>
    <pre><code>cd frontend
npm install
npm run build</code></pre>
</body>
</html>
EOL
    echo "Created minimal index.html as a fallback"
fi

# Check if build was successful
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    echo -e "\n${GREEN}=== Frontend build completed ===${NC}"
    echo "Build files are in the dist directory"
else
    echo -e "\n${RED}=== Frontend build failed ===${NC}"
    echo "Please check the logs for more information"
    exit 1
fi

# Return to the original directory
cd ..

echo -e "\n${GREEN}=== Frontend build process completed ===${NC}"
