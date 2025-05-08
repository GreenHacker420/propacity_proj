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
