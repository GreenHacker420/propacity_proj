"""
Script to migrate data from SQLite to MongoDB.
"""

import logging
import sys
from app.utils.db_migration import migrate_all_data
from app.mongodb import get_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the migration from SQLite to MongoDB."""
    try:
        # Check if MongoDB URI is properly configured
        from app.mongodb import MONGODB_URI
        if "<username>" in MONGODB_URI or "<password>" in MONGODB_URI or "<cluster-address>" in MONGODB_URI:
            logger.error("MongoDB connection string contains placeholder values.")
            logger.error("Please update the MONGODB_URI in your .env file with your actual MongoDB Atlas credentials.")
            logger.error("Example: MONGODB_URI=mongodb+srv://myuser:mypassword@cluster0.abcde.mongodb.net/product_reviews?retryWrites=true&w=majority")
            sys.exit(1)

        # Test MongoDB connection
        client = get_client()
        client.admin.command('ping')
        logger.info("MongoDB connection successful")

        # Check if SQLite database exists and has tables
        import os
        from sqlalchemy import inspect
        from app.database import engine

        sqlite_db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.db")
        if not os.path.exists(sqlite_db_path):
            logger.warning("SQLite database file not found. Creating empty MongoDB collections.")
            # Create empty collections in MongoDB
            db = client["product_reviews"]
            db.create_collection("users")
            db.create_collection("reviews")
            db.create_collection("keywords")
            db.create_collection("analysis_history")
            db.create_collection("processing_times")
            logger.info("Empty MongoDB collections created successfully")
        else:
            # Check if tables exist in SQLite
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if not tables:
                logger.warning("No tables found in SQLite database. Creating empty MongoDB collections.")
                # Create empty collections in MongoDB
                db = client["product_reviews"]
                db.create_collection("users")
                db.create_collection("reviews")
                db.create_collection("keywords")
                db.create_collection("analysis_history")
                db.create_collection("processing_times")
                logger.info("Empty MongoDB collections created successfully")
            else:
                # Run migration
                logger.info(f"Starting data migration from SQLite to MongoDB for tables: {tables}...")
                migrate_all_data()
                logger.info("Migration completed successfully")

    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
