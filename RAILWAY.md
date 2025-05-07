# Deploying Product Pulse to Railway

This guide provides instructions for deploying the Product Pulse application to Railway.

## Prerequisites

1. A Railway account (https://railway.app/)
2. A MongoDB Atlas account with a database set up
3. (Optional) A Google Gemini API key for advanced analysis features

## Runtime Requirements

### Python Version

This application is configured to use Python 3.11, which provides the best compatibility with all the required packages. The following files specify the Python version:

- `runtime.txt`: Specifies Python 3.11.7
- `.python-version`: Specifies Python 3.11.7
- `backend/requirements.txt`: Includes a Python 3.11 requirement
- `railway.json`: Configures Nixpacks to use Python 3.11

### Node.js Version

The frontend requires Node.js 18 or later. The following files specify the Node.js version:

- `.nvmrc`: Specifies Node.js 18
- `package.json`: Specifies Node.js >=18.0.0 in the engines field
- `railway.json`: Configures Nixpacks to use Node.js 18

## Environment Variables

The following environment variables need to be set in your Railway project:

- `MONGODB_URI`: Your MongoDB Atlas connection string
- `PORT`: Set by Railway automatically
- `FRONTEND_URL`: The URL of your deployed application (will be provided by Railway)
- `JWT_SECRET`: A secret key for JWT authentication
- `JWT_ALGORITHM`: HS256
- `ACCESS_TOKEN_EXPIRE_MINUTES`: 30
- `GOOGLE_API_KEY`: (Optional) Your Google Gemini API key

## Configuration Files

The following configuration files are used for Railway deployment:

- `railway.json`: Main configuration file for Railway
- `Dockerfile`: Defines the container image for deployment
- `.dockerignore`: Specifies files to exclude from the Docker build
- `runtime.txt`: Specifies the Python version
- `.nvmrc`: Specifies the Node.js version
- `.python-version`: Specifies the Python version
- `package.json`: Defines Node.js dependencies and scripts
- `.npmrc`: Configures npm behavior

## Deployment Steps

1. **Create a new Railway project**

   - Go to [Railway Dashboard](https://railway.app/dashboard)
   - Click "New Project"
   - Select "Deploy from GitHub repo"

2. **Connect your GitHub repository**

   - Select the repository containing your Product Pulse application
   - Railway will automatically detect the configuration files

3. **Set environment variables**

   - In your project settings, go to the "Variables" tab
   - Add all the required environment variables listed above

4. **Deploy the application**

   - Railway will automatically deploy your application using the Dockerfile
   - The deployment process will:
     - Build a Docker image with Python 3.11 and Node.js 18
     - Install backend dependencies
     - Download NLTK resources
     - Install frontend dependencies
     - Build the frontend
     - Start the FastAPI server

5. **Access your application**

   - Once deployed, Railway will provide a URL for your application
   - Update the `FRONTEND_URL` environment variable with this URL

## Troubleshooting

- **MongoDB Connection Issues**: Ensure your MongoDB Atlas IP whitelist includes Railway's IP ranges or is set to allow connections from anywhere (0.0.0.0/0)
- **NLTK Resource Download Failures**: Check the deployment logs for any issues with NLTK resource downloads
- **Frontend Not Loading**: Verify that the `FRONTEND_URL` environment variable is set correctly

## Monitoring and Scaling

- Use Railway's monitoring tools to track application performance
- Scale your application as needed using Railway's scaling options

## Maintenance

- Update your application by pushing changes to your GitHub repository
- Railway will automatically redeploy your application when changes are detected

## Additional Resources

- [Railway Documentation](https://docs.railway.app/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
