"""
MongoDB connection module for the Product Review Analyzer.
This module provides functions to connect to MongoDB Atlas and access collections.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get MongoDB connection string from environment
MONGODB_URI = os.getenv("MONGODB_URI")

# MongoDB client instance
_client = None

def get_client():
    """
    Get or create a MongoDB client instance.
    
    Returns:
        MongoClient: MongoDB client instance
    """
    global _client
    if _client is None:
        try:
            logger.info("Connecting to MongoDB Atlas...")
            _client = MongoClient(MONGODB_URI)
            # Ping the database to verify connection
            _client.admin.command('ping')
            logger.info("Successfully connected to MongoDB Atlas")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise
    return _client

def get_database(db_name="product_reviews"):
    """
    Get a MongoDB database instance.
    
    Args:
        db_name (str): Name of the database
        
    Returns:
        Database: MongoDB database instance
    """
    client = get_client()
    return client[db_name]

def get_collection(collection_name, db_name="product_reviews"):
    """
    Get a MongoDB collection instance.
    
    Args:
        collection_name (str): Name of the collection
        db_name (str): Name of the database
        
    Returns:
        Collection: MongoDB collection instance
    """
    db = get_database(db_name)
    return db[collection_name]

def close_connection():
    """Close the MongoDB connection."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")
