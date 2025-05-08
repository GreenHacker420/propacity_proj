#!/bin/bash
# Script to fix Vite build issues on AWS

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Fixing Vite build issues ===${NC}"

# Navigate to frontend directory
cd frontend

# Create a package.json backup
echo "Creating package.json backup..."
cp package.json package.json.bak

# Update package.json to use a specific Vite version
echo "Updating package.json to use a specific Vite version..."
if command -v jq &> /dev/null; then
    # If jq is available, use it to update package.json
    jq '.devDependencies.vite = "4.5.0"' package.json > package.json.tmp && mv package.json.tmp package.json
else
    # Otherwise, use sed (less reliable but should work for simple cases)
    sed -i 's/"vite": ".*"/"vite": "4.5.0"/g' package.json
fi

# Clean node_modules and reinstall
echo "Cleaning node_modules..."
rm -rf node_modules
rm -f package-lock.json

# Reinstall dependencies
echo "Reinstalling dependencies..."
npm install

# Create a direct build script
echo "Creating direct build script..."
cat > build_direct.js << EOL
// Direct build script for Vite
// This script directly uses the Vite API to build the project
// without relying on the CLI which can have path issues

console.log('Starting direct Vite build...');

// Set environment variables
process.env.NODE_ENV = 'production';

// Use CommonJS require for better compatibility
try {
  console.log('Attempting to require vite...');
  const vite = require('vite');

  console.log('Vite imported successfully');

  // Run the build
  vite.build({
    root: process.cwd(),
    logLevel: 'info',
    configFile: './vite.config.js',
  }).then(() => {
    console.log('Build completed successfully');
    process.exit(0);
  }).catch((error) => {
    console.error('Build failed:', error);
    process.exit(1);
  });
} catch (error) {
  console.error('Failed to import vite:', error);

  // Try alternative approach with dynamic import
  console.log('Trying alternative approach with dynamic import...');

  import('vite').then((vite) => {
    console.log('Vite imported successfully via dynamic import');

    return vite.build({
      root: process.cwd(),
      logLevel: 'info',
      configFile: './vite.config.js',
    });
  }).then(() => {
    console.log('Build completed successfully');
    process.exit(0);
  }).catch((error) => {
    console.error('All build attempts failed:', error);
    process.exit(1);
  });
}
EOL

# Run the direct build script
echo "Running direct build script..."
NODE_ENV=production node build_direct.js

# Check if build was successful
if [ -d "dist" ] && [ "$(ls -A dist)" ]; then
    echo -e "\n${GREEN}=== Build successful! ===${NC}"
    echo "Build files are in the dist directory"
else
    echo -e "\n${RED}=== Build failed ===${NC}"
    echo "Creating minimal dist directory as fallback..."
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

# Return to the original directory
cd ..

echo -e "\n${GREEN}=== Vite build fix process completed ===${NC}"
