"""
This module redirects database operations to MongoDB.
SQLite is no longer used in this application.
"""

import logging
from .mongodb import get_collection, get_database

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dummy Base class for backward compatibility
class Base:
    """Dummy Base class for backward compatibility"""
    metadata = type('', (), {'create_all': lambda bind: None})()

# Dummy engine for backward compatibility
engine = None

# Dependency to get DB session (redirects to MongoDB)
def get_db():
    """
    This function is kept for backward compatibility.
    It yields None since we're using MongoDB directly now.
    """
    logger.warning("get_db() called - SQLite is no longer used, use MongoDB functions instead")
    try:
        yield None
    finally:
        pass
