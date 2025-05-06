# MongoDB Atlas Migration Guide

This guide explains how to migrate the Product Review Analyzer from SQLite to MongoDB Atlas.

## Setting Up MongoDB Atlas

1. **Create a MongoDB Atlas Account**
   - Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) and sign up for a free account
   - Create a new organization if prompted

2. **Create a New Project**
   - Create a new project (e.g., "Product Review Analyzer")

3. **Create a Cluster**
   - Click "Build a Database"
   - Choose the free tier (M0)
   - Select your preferred cloud provider and region
   - Click "Create Cluster"

4. **Set Up Database Access**
   - In the left sidebar, click "Database Access"
   - Click "Add New Database User"
   - Create a username and password (save these credentials)
   - Set privileges to "Read and Write to Any Database"
   - Click "Add User"

5. **Set Up Network Access**
   - In the left sidebar, click "Network Access"
   - Click "Add IP Address"
   - For development, you can add your current IP or use "0.0.0.0/0" to allow access from anywhere (not recommended for production)
   - Click "Confirm"

6. **Get Connection String**
   - Once your cluster is created, click "Connect"
   - Choose "Connect your application"
   - Select "Python" as the driver and the appropriate version
   - Copy the connection string

7. **Update .env File**
   - Open the `.env` file in the backend directory
   - Replace the placeholder in the `MONGODB_URI` variable with your connection string
   - Replace `<username>`, `<password>`, `<cluster-address>`, and `<database-name>` with your actual values
   - Example: `MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.abcde.mongodb.net/product_reviews?retryWrites=true&w=majority`

   **Important**: You must update the connection string with your actual MongoDB Atlas credentials before running the migration script. The application will not work with the placeholder values.

## Migrating Data from SQLite to MongoDB

1. **Install Required Packages**
   ```bash
   pip install pymongo
   ```

2. **Run Migration Script**
   ```bash
   cd backend
   python migrate_to_mongodb.py
   ```

3. **Verify Migration**
   - Log in to MongoDB Atlas
   - Go to your cluster
   - Click "Browse Collections"
   - You should see the collections: `users`, `reviews`, `keywords`, `analysis_history`, and `processing_times`
   - Verify that your data has been migrated correctly

## Using MongoDB in the Application

The application now supports both SQLite and MongoDB. The MongoDB connection is used by default if the `MONGODB_URI` environment variable is set.

To use MongoDB exclusively:
1. Make sure the `MONGODB_URI` environment variable is set correctly
2. Use the MongoDB-specific functions in your code:
   - `from app.mongodb import get_collection` to get a MongoDB collection
   - Use the MongoDB collection methods (`find_one`, `find`, `insert_one`, etc.) to interact with the data

## Troubleshooting

- **Connection Issues**: Make sure your IP address is allowed in the Network Access settings
- **Authentication Issues**: Verify your username and password in the connection string
- **Database Not Found**: Make sure the database name in the connection string is correct
- **Migration Errors**: Check the logs for specific error messages

## Additional Resources

- [MongoDB Atlas Documentation](https://docs.atlas.mongodb.com/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB CRUD Operations](https://docs.mongodb.com/manual/crud/)
