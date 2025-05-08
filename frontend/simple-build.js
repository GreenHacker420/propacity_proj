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
