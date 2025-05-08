import asyncio
import logging
import sys
import os

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.mongodb import init_mongodb, get_client, get_database, get_collection, close_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_connection():
    try:
        # Test initialization
        logger.info("Testing MongoDB initialization...")
        result = await init_mongodb()
        logger.info(f"Initialization result: {result}")

        # Test client
        logger.info("Testing MongoDB client...")
        client = get_client()
        logger.info(f"Client info: {client}")

        # Test database
        logger.info("Testing database access...")
        db = get_database()
        logger.info(f"Database info: {db}")

        # Test collection
        logger.info("Testing collection access...")
        users_collection = get_collection("users")
        logger.info(f"Users collection info: {users_collection}")

        # Test basic operation
        logger.info("Testing basic operation (find_one)...")
        result = users_collection.find_one({})
        logger.info(f"Find one result: {result}")

        logger.info("All tests passed successfully!")
        return True

    except Exception as e:
        logger.error(f"Test failed with error: {str(e)}", exc_info=True)
        return False
    finally:
        logger.info("Closing MongoDB connection...")
        close_connection()

if __name__ == "__main__":
    logger.info("Starting MongoDB connection test...")
    success = asyncio.run(test_connection())
    if success:
        logger.info("Test completed successfully!")
        sys.exit(0)
    else:
        logger.error("Test failed!")
        sys.exit(1) 