"""
Utility functions for migrating data from SQLite to MongoDB.
"""

import logging
from sqlalchemy.orm import Session
from ..database import get_db
from ..mongodb import get_collection
from ..models.db_models import Review, Keyword
from ..models.user import User
from ..models.analysis_history import AnalysisHistory
from ..models.processing_time import ProcessingTime
from ..models.mongo_models import (
    MongoReview, MongoKeyword, MongoUser,
    MongoAnalysisHistory, MongoProcessingTime
)

# Set up logging
logger = logging.getLogger(__name__)

def migrate_users(db: Session):
    """
    Migrate users from SQLite to MongoDB.

    Args:
        db (Session): SQLAlchemy database session
    """
    users_collection = get_collection("users")
    users = db.query(User).all()

    for user in users:
        mongo_user = MongoUser.from_sqlalchemy(user)
        # Convert to dict and remove None values
        user_dict = mongo_user.model_dump(by_alias=True)
        user_dict = {k: v for k, v in user_dict.items() if v is not None}

        # Check if user already exists
        existing_user = users_collection.find_one({"username": user.username})
        if not existing_user:
            users_collection.insert_one(user_dict)
            logger.info(f"Migrated user: {user.username}")
        else:
            logger.info(f"User already exists: {user.username}")

    logger.info(f"Migrated {len(users)} users to MongoDB")

def migrate_keywords(db: Session):
    """
    Migrate keywords from SQLite to MongoDB.

    Args:
        db (Session): SQLAlchemy database session
    """
    keywords_collection = get_collection("keywords")
    keywords = db.query(Keyword).all()

    for keyword in keywords:
        mongo_keyword = MongoKeyword.from_sqlalchemy(keyword)
        # Convert to dict and remove None values
        keyword_dict = mongo_keyword.model_dump(by_alias=True)
        keyword_dict = {k: v for k, v in keyword_dict.items() if v is not None}

        # Check if keyword already exists
        existing_keyword = keywords_collection.find_one({"text": keyword.text})
        if not existing_keyword:
            keywords_collection.insert_one(keyword_dict)
            logger.info(f"Migrated keyword: {keyword.text}")
        else:
            logger.info(f"Keyword already exists: {keyword.text}")

    logger.info(f"Migrated {len(keywords)} keywords to MongoDB")

def migrate_reviews(db: Session):
    """
    Migrate reviews from SQLite to MongoDB.

    Args:
        db (Session): SQLAlchemy database session
    """
    reviews_collection = get_collection("reviews")
    reviews = db.query(Review).all()

    for review in reviews:
        mongo_review = MongoReview.from_sqlalchemy(review)
        # Convert to dict and remove None values
        review_dict = mongo_review.model_dump(by_alias=True)
        review_dict = {k: v for k, v in review_dict.items() if v is not None}

        # Check if review already exists (using text as unique identifier)
        existing_review = reviews_collection.find_one({"text": review.text})
        if not existing_review:
            reviews_collection.insert_one(review_dict)
            logger.info(f"Migrated review: {review.id}")
        else:
            logger.info(f"Review already exists: {review.id}")

    logger.info(f"Migrated {len(reviews)} reviews to MongoDB")

def migrate_analysis_history(db: Session):
    """
    Migrate analysis history from SQLite to MongoDB.

    Args:
        db (Session): SQLAlchemy database session
    """
    history_collection = get_collection("analysis_history")
    histories = db.query(AnalysisHistory).all()

    for history in histories:
        mongo_history = MongoAnalysisHistory.from_sqlalchemy(history)
        # Convert to dict and remove None values
        history_dict = mongo_history.model_dump(by_alias=True)
        history_dict = {k: v for k, v in history_dict.items() if v is not None}

        # Check if history already exists
        existing_history = history_collection.find_one({
            "source_type": history.source_type,
            "source_name": history.source_name,
            "timestamp": history.timestamp
        })
        if not existing_history:
            history_collection.insert_one(history_dict)
            logger.info(f"Migrated analysis history: {history.id}")
        else:
            logger.info(f"Analysis history already exists: {history.id}")

    logger.info(f"Migrated {len(histories)} analysis histories to MongoDB")

def migrate_processing_times(db: Session):
    """
    Migrate processing times from SQLite to MongoDB.

    Args:
        db (Session): SQLAlchemy database session
    """
    times_collection = get_collection("processing_times")
    times = db.query(ProcessingTime).all()

    for time in times:
        mongo_time = MongoProcessingTime.from_sqlalchemy(time)
        # Convert to dict and remove None values
        time_dict = mongo_time.model_dump(by_alias=True)
        time_dict = {k: v for k, v in time_dict.items() if v is not None}

        # Check if processing time already exists
        existing_time = times_collection.find_one({
            "operation": time.operation,
            "timestamp": time.timestamp
        })
        if not existing_time:
            times_collection.insert_one(time_dict)
            logger.info(f"Migrated processing time: {time.id}")
        else:
            logger.info(f"Processing time already exists: {time.id}")

    logger.info(f"Migrated {len(times)} processing times to MongoDB")

def migrate_all_data():
    """Migrate all data from SQLite to MongoDB."""
    try:
        # Get SQLAlchemy session
        db = next(get_db())

        # Migrate data with error handling for each table
        try:
            migrate_users(db)
        except Exception as e:
            logger.warning(f"Error migrating users: {str(e)}")
            logger.warning("Skipping users migration")

        try:
            migrate_keywords(db)
        except Exception as e:
            logger.warning(f"Error migrating keywords: {str(e)}")
            logger.warning("Skipping keywords migration")

        try:
            migrate_reviews(db)
        except Exception as e:
            logger.warning(f"Error migrating reviews: {str(e)}")
            logger.warning("Skipping reviews migration")

        try:
            migrate_analysis_history(db)
        except Exception as e:
            logger.warning(f"Error migrating analysis history: {str(e)}")
            logger.warning("Skipping analysis history migration")

        try:
            migrate_processing_times(db)
        except Exception as e:
            logger.warning(f"Error migrating processing times: {str(e)}")
            logger.warning("Skipping processing times migration")

        logger.info("Data migration completed with available tables")
    except Exception as e:
        logger.error(f"Error during data migration: {str(e)}")
        raise
    finally:
        db.close()
