"""
MongoDB connection module for the Product Review Analyzer.
This module provides functions to connect to MongoDB Atlas and access collections.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MongoDB connection string from environment
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI environment variable is not set")

# MongoDB client instance
_client: Optional[MongoClient] = None

async def init_mongodb() -> bool:
    """
    Initialize MongoDB connection and verify it works.
    This function is called during application startup.

    Returns:
        bool: True if initialization is successful

    Raises:
        ConnectionFailure: If connection to MongoDB fails
        ServerSelectionTimeoutError: If server selection times out
        ValueError: If required environment variables are missing
    """
    try:
        # Validate connection string
        if not MONGODB_URI.startswith(('mongodb://', 'mongodb+srv://')):
            raise ValueError("Invalid MongoDB URI format")

        # Get client (this will handle connection errors and fallbacks)
        client = get_client()

        # Test connection with timeout
        client.admin.command('ping', serverSelectionTimeoutMS=10000)
        logger.info("MongoDB connection initialized successfully")

        # Check if we're using a mock client in development mode
        if os.getenv("DEVELOPMENT_MODE", "").lower() == "true" and hasattr(client, '_mock_obj'):
            logger.warning("Using mock MongoDB client - skipping collection initialization")
            return True

        try:
            # Initialize collections if they don't exist
            db = get_database()
            collections = db.list_collection_names()

            required_collections = [
                "users",
                "reviews",
                "keywords",
                "analysis_history",
                "weekly_summaries",
                "processing_times"
            ]

            for collection in required_collections:
                if collection not in collections:
                    db.create_collection(collection)
                    logger.info(f"Created collection: {collection}")
                else:
                    logger.debug(f"Collection already exists: {collection}")

            # Verify database access
            db_stats = db.command("dbStats")
            logger.info(f"Database stats: {db_stats}")
        except Exception as collection_error:
            # If we're in development mode, we can continue even if collection setup fails
            if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
                logger.warning(f"Failed to initialize collections: {str(collection_error)}")
                logger.warning("Continuing in development mode with limited functionality")
                return True
            else:
                # In production, we need to fail if collection setup fails
                raise

        return True
    except Exception as e:
        logger.error(f"Failed to initialize MongoDB: {str(e)}")

        # In development mode, we can continue even if MongoDB initialization fails
        if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
            logger.warning("Continuing in development mode with limited functionality")
            return True

        # In production, we need to fail if MongoDB initialization fails
        raise

def get_client() -> MongoClient:
    """
    Get MongoDB client instance with proper configuration.
    """
    global _client
    if _client is None:
        try:
            # Get MongoDB URI from environment
            uri = os.getenv("MONGODB_URI")
            if not uri:
                raise ValueError("MONGODB_URI environment variable is not set")

            # Log connection attempt (without sensitive info)
            logger.info("Attempting to connect to MongoDB Atlas...")
            if '@' in uri:
                # Hide username and password in logs
                parts = uri.split('@')
                logger.info(f"Connection string format: {parts[1]}")
            else:
                logger.info("Connection string format: Invalid format")

            # Log platform information
            import platform
            logger.info(f"Platform: {platform.system()} {platform.release()}")
            logger.info(f"Python version: {platform.python_version()}")

            # Try to create the client with appropriate settings
            try:
                # Use standard configuration
                _client = MongoClient(
                    uri,
                    connectTimeoutMS=30000,
                    serverSelectionTimeoutMS=30000,
                    socketTimeoutMS=30000
                )

                # Test the connection
                _client.admin.command('ping')
                logger.info("Successfully connected to MongoDB Atlas")
            except Exception as e:
                logger.warning(f"MongoDB connection failed: {str(e)}")

                # If in development mode, create a mock client
                if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
                    logger.warning("Creating mock MongoDB client for development mode")
                    from unittest.mock import MagicMock
                    _client = MagicMock()
                    logger.warning("Created mock MongoDB client")
                    return _client
                else:
                    # In production, we need to fail
                    raise
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            logger.error(f"Connection error type: {type(e).__name__}")
            if hasattr(e, 'args'):
                logger.error(f"Error args: {e.args}")

            # If in development mode, create a mock client
            if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
                logger.warning("Creating mock MongoDB client for development mode")
                try:
                    # Try to create a local MongoDB client as fallback
                    logger.info("Attempting to connect to local MongoDB...")
                    _client = MongoClient("mongodb://localhost:27017/")
                    _client.admin.command('ping')
                    logger.info("Successfully connected to local MongoDB")
                    return _client
                except Exception as local_e:
                    logger.warning(f"Failed to connect to local MongoDB: {str(local_e)}")
                    # Create a mock client as last resort
                    from unittest.mock import MagicMock
                    _client = MagicMock()
                    logger.warning("Created mock MongoDB client")
                    return _client
            raise
    return _client

def get_database(db_name: str = "product_reviews"):
    """
    Get a MongoDB database instance.

    Args:
        db_name (str): Name of the database

    Returns:
        Database: MongoDB database instance

    Raises:
        ConnectionFailure: If connection to MongoDB fails
    """
    try:
        client = get_client()
        db = client[db_name]
        # Verify database access
        db.command("ping")
        return db
    except Exception as e:
        logger.error(f"Error accessing database {db_name}: {str(e)}")
        raise

def get_collection(collection_name: str, db_name: str = "product_reviews"):
    """
    Get a MongoDB collection instance.

    Args:
        collection_name (str): Name of the collection
        db_name (str): Name of the database

    Returns:
        Collection: MongoDB collection instance

    Raises:
        ConnectionFailure: If connection to MongoDB fails
    """
    try:
        db = get_database(db_name)
        collection = db[collection_name]
        # Verify collection access
        collection.find_one({})
        return collection
    except Exception as e:
        logger.error(f"Error accessing collection {collection_name}: {str(e)}")
        raise

def close_connection():
    """Close the MongoDB connection."""
    global _client
    if _client is not None:
        try:
            _client.close()
            _client = None
            logger.info("MongoDB connection closed")
        except Exception as e:
            logger.error(f"Error closing MongoDB connection: {str(e)}")
            raise

async def get_connection_status() -> Dict[str, Any]:
    """
    Get the current MongoDB connection status.

    Returns:
        Dict[str, Any]: Connection status information
    """
    try:
        client = get_client()
        db = get_database()

        # Get server status
        server_status = client.admin.command("serverStatus")

        # Get database stats
        db_stats = db.command("dbStats")

        # Get collection stats
        collections = db.list_collection_names()
        collection_stats = {}
        for collection in collections:
            try:
                collection_stats[collection] = db.command("collStats", collection)
            except Exception as e:
                logger.warning(f"Could not get stats for collection {collection}: {str(e)}")

        return {
            "status": "connected",
            "server_info": {
                "version": server_status.get("version"),
                "host": server_status.get("host"),
                "uptime": server_status.get("uptime")
            },
            "database_stats": {
                "collections": db_stats.get("collections"),
                "objects": db_stats.get("objects"),
                "dataSize": db_stats.get("dataSize"),
                "storageSize": db_stats.get("storageSize")
            },
            "collections": collections,
            "collection_stats": collection_stats
        }
    except Exception as e:
        logger.error(f"Error getting connection status: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }
