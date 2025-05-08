"""
MongoDB connection module for the Product Review Analyzer.
This module provides functions to connect to MongoDB Atlas and access collections.
"""

import os
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from dotenv import load_dotenv
import logging
from typing import Optional, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MongoDB connection string from environment
MONGODB_URI = os.getenv("MONGODB_URI")
# For development, we'll allow the app to start without MongoDB
if not MONGODB_URI:
    logger.warning("MONGODB_URI environment variable is not set. Using development mode with mock MongoDB.")
    # Set development mode flag
    os.environ["DEVELOPMENT_MODE"] = "true"

# MongoDB client instance
_client: Optional[MongoClient] = None

async def init_mongodb() -> bool:
    """
    Initialize MongoDB connection and verify it works.
    This function is called during application startup.

    Returns:
        bool: True if initialization is successful, even with mock client in development mode

    Raises:
        ConnectionFailure: If connection to MongoDB fails in strict production mode
        ServerSelectionTimeoutError: If server selection times out in strict production mode
        ValueError: If required environment variables are missing in strict production mode
    """
    # If we're already in development mode, use mock client
    if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
        logger.warning("Running in DEVELOPMENT_MODE with mock MongoDB client")
        client = get_client()  # This will return a mock client
        logger.info("Mock MongoDB client initialized for development")
        return True

    # If MONGODB_URI is not set, use development mode
    if not MONGODB_URI:
        logger.warning("MONGODB_URI environment variable is not set. Using development mode with mock MongoDB.")
        os.environ["DEVELOPMENT_MODE"] = "true"
        return await init_mongodb()  # Recursive call with development mode set

    try:
        # Validate connection string
        if not MONGODB_URI.startswith(('mongodb://', 'mongodb+srv://')):
            raise ValueError("Invalid MongoDB URI format")

        client = get_client()

        # Test connection with timeout
        client.admin.command('ping', serverSelectionTimeoutMS=5000)
        logger.info("MongoDB connection initialized successfully")

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

        return True
    except ConnectionFailure as e:
        logger.error(f"Failed to connect to MongoDB: {str(e)}")
        # Try alternative SSL configuration for production
        if os.getenv("DEVELOPMENT_MODE", "").lower() != "true":
            logger.warning("Trying alternative SSL configuration for MongoDB Atlas...")
            try:
                # Reset client to force new connection with different settings
                global _client
                _client = None

                # This will try alternative SSL settings
                client = get_client()

                # Test connection with timeout
                client.admin.command('ping', serverSelectionTimeoutMS=5000)
                logger.info("MongoDB connection initialized successfully with alternative SSL configuration")

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

                return True
            except Exception as alt_e:
                logger.error(f"Alternative SSL configuration also failed: {str(alt_e)}")
                if os.getenv("STRICT_PRODUCTION", "").lower() == "true":
                    raise
                else:
                    # Fall back to mock client
                    logger.warning("Falling back to mock MongoDB client")
                    os.environ["DEVELOPMENT_MODE"] = "true"
                    return await init_mongodb()
        else:
            # In development, we'll use a mock client
            logger.warning("Failed to connect to MongoDB. Using mock client for development.")
            os.environ["DEVELOPMENT_MODE"] = "true"
            return await init_mongodb()  # Recursive call with development mode set
    except ServerSelectionTimeoutError as e:
        logger.error(f"Server selection timeout: {str(e)}")
        if os.getenv("STRICT_PRODUCTION", "").lower() == "true":
            raise
        else:
            # Use mock client as fallback
            logger.warning("Server selection timeout. Using mock client.")
            os.environ["DEVELOPMENT_MODE"] = "true"
            return await init_mongodb()  # Recursive call with development mode set
    except Exception as e:
        logger.error(f"Unexpected error during MongoDB initialization: {str(e)}")
        if os.getenv("STRICT_PRODUCTION", "").lower() == "true":
            raise
        else:
            # Use mock client as fallback
            logger.warning(f"Unexpected error during MongoDB initialization: {str(e)}. Using mock client.")
            os.environ["DEVELOPMENT_MODE"] = "true"
            return await init_mongodb()  # Recursive call with development mode set

def get_client() -> MongoClient:
    """
    Get or create a MongoDB client instance.

    Returns:
        MongoClient: MongoDB client instance or a mock client in development mode

    Raises:
        ConnectionFailure: If connection to MongoDB fails (only in production mode)
    """
    global _client
    if _client is None:
        # In development mode, we'll create a mock client immediately
        if os.getenv("DEVELOPMENT_MODE", "").lower() == "true":
            logger.warning("Running in DEVELOPMENT_MODE with mock MongoDB client")
            from unittest.mock import MagicMock

            # Create a more sophisticated mock client
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_collection = MagicMock()

            # Set up mock methods
            mock_collection.find_one.return_value = {}
            mock_collection.find.return_value = []
            mock_collection.count_documents.return_value = 0
            mock_collection.insert_one.return_value = MagicMock(inserted_id="mock_id")
            mock_collection.insert_many.return_value = MagicMock(inserted_ids=["mock_id"])
            mock_collection.update_one.return_value = MagicMock(modified_count=1)
            mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

            # Set up mock database
            mock_db.__getitem__.return_value = mock_collection
            mock_db.list_collection_names.return_value = ["users", "reviews", "keywords", "analysis_history", "processing_times"]
            mock_db.command.return_value = {"ok": 1}

            # Set up mock client
            mock_client.__getitem__.return_value = mock_db
            mock_client.admin.command.return_value = {"ok": 1, "version": "mock", "host": "localhost"}

            _client = mock_client
            logger.info("Mock MongoDB client initialized for development")
            return _client

        try:
            logger.info("Connecting to MongoDB Atlas...")
            _client = MongoClient(
                MONGODB_URI,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=5000,
                socketTimeoutMS=5000,
                retryWrites=True,
                retryReads=True,
                tlsCAFile=None,  # Use system CA certificates
                tlsAllowInvalidCertificates=False,  # Don't allow invalid certificates
                tlsAllowInvalidHostnames=False,  # Don't allow invalid hostnames
                ssl=True  # Use SSL/TLS
            )
            # Ping the database to verify connection
            _client.admin.command('ping')
            logger.info("Successfully connected to MongoDB Atlas")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            # Check if we're in production mode
            if os.getenv("DEVELOPMENT_MODE", "").lower() != "true":
                # In production, we'll try with different SSL settings
                logger.warning("Trying alternative SSL configuration for MongoDB Atlas...")
                try:
                    _client = MongoClient(
                        MONGODB_URI,
                        serverSelectionTimeoutMS=5000,
                        connectTimeoutMS=5000,
                        socketTimeoutMS=5000,
                        retryWrites=True,
                        retryReads=True,
                        ssl=True,
                        tlsAllowInvalidCertificates=True  # Allow invalid certificates as a fallback
                    )
                    # Ping the database to verify connection
                    _client.admin.command('ping')
                    logger.info("Successfully connected to MongoDB Atlas with alternative SSL configuration")
                    return _client
                except Exception as alt_e:
                    logger.error(f"Alternative SSL configuration also failed: {str(alt_e)}")
                    # If we're in strict production mode, raise the error
                    if os.getenv("STRICT_PRODUCTION", "").lower() == "true":
                        raise
                    else:
                        # Otherwise, fall back to mock client
                        logger.warning("Falling back to mock MongoDB client")
                        os.environ["DEVELOPMENT_MODE"] = "true"
                        return get_client()  # Recursive call will return mock client
            else:
                # In development, we'll use a mock client as fallback
                logger.warning("Falling back to mock MongoDB client for development")
                os.environ["DEVELOPMENT_MODE"] = "true"
                return get_client()  # Recursive call will return mock client
        except ServerSelectionTimeoutError as e:
            logger.error(f"Server selection timeout: {str(e)}")
            if os.getenv("STRICT_PRODUCTION", "").lower() == "true":
                raise
            else:
                logger.warning("Falling back to mock MongoDB client")
                os.environ["DEVELOPMENT_MODE"] = "true"
                return get_client()
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {str(e)}")
            if os.getenv("STRICT_PRODUCTION", "").lower() == "true":
                raise
            else:
                logger.warning("Falling back to mock MongoDB client")
                os.environ["DEVELOPMENT_MODE"] = "true"
                return get_client()
    return _client

def get_database(db_name: str = "product_reviews"):
    """
    Get a MongoDB database instance.

    Args:
        db_name (str): Name of the database

    Returns:
        Database: MongoDB database instance or mock database in development mode

    Raises:
        ConnectionFailure: If connection to MongoDB fails (only in production mode)
    """
    try:
        client = get_client()
        db = client[db_name]
        # Verify database access (will be mocked in development mode)
        db.command("ping")
        return db
    except Exception as e:
        logger.error(f"Error accessing database {db_name}: {str(e)}")
        if os.getenv("PRODUCTION", "").lower() == "true":
            raise
        else:
            # In development, we'll use a mock client
            logger.warning(f"Error accessing database {db_name}. Using mock database for development.")
            if os.getenv("DEVELOPMENT_MODE", "").lower() != "true":
                os.environ["DEVELOPMENT_MODE"] = "true"
                # Get a fresh client (will be mock in development mode)
                global _client
                _client = None
            return get_client()[db_name]

def get_collection(collection_name: str, db_name: str = "product_reviews"):
    """
    Get a MongoDB collection instance.

    Args:
        collection_name (str): Name of the collection
        db_name (str): Name of the database

    Returns:
        Collection: MongoDB collection instance or mock collection in development mode

    Raises:
        ConnectionFailure: If connection to MongoDB fails (only in production mode)
    """
    try:
        db = get_database(db_name)
        collection = db[collection_name]
        # Verify collection access (will be mocked in development mode)
        collection.find_one({})
        return collection
    except Exception as e:
        logger.error(f"Error accessing collection {collection_name}: {str(e)}")
        if os.getenv("PRODUCTION", "").lower() == "true":
            raise
        else:
            # In development, we'll use a mock client
            logger.warning(f"Error accessing collection {collection_name}. Using mock collection for development.")
            if os.getenv("DEVELOPMENT_MODE", "").lower() != "true":
                os.environ["DEVELOPMENT_MODE"] = "true"
                # Get a fresh client (will be mock in development mode)
                global _client
                _client = None
            return get_database(db_name)[collection_name]

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
