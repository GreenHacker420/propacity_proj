"""
MongoDB-based timing service for the Product Review Analyzer.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
import statistics

from ..mongodb import get_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MongoTimingService:
    """Service for managing processing times in MongoDB."""

    @staticmethod
    def record_processing_time(time_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record the time taken for a processing operation.

        Args:
            time_data: Processing time data

        Returns:
            Recorded processing time
        """
        try:
            logger.info(f"Recording processing time: {time_data}")
            times_collection = get_collection("processing_times")

            # Create processing time document
            processing_time = {
                "operation": time_data.get("operation"),
                "record_count": time_data.get("record_count", 0),
                "duration_seconds": time_data.get("duration_seconds", 0.0),
                "timestamp": datetime.now()
            }

            # Add optional fields
            if "file_name" in time_data:
                processing_time["file_name"] = time_data["file_name"]
            if "source" in time_data:
                processing_time["source"] = time_data["source"]
            if "query" in time_data:
                processing_time["query"] = time_data["query"]

            # Insert processing time
            result = times_collection.insert_one(processing_time)
            processing_time["_id"] = result.inserted_id

            logger.info(f"Recorded processing time with ID: {result.inserted_id}")
            return processing_time

        except Exception as e:
            logger.error(f"Error recording processing time: {str(e)}")
            raise

    @staticmethod
    def get_estimated_time(operation: str, record_count: int) -> Dict[str, Any]:
        """
        Get estimated processing time for an operation.

        Args:
            operation: Operation name
            record_count: Number of records to process

        Returns:
            Estimated processing time
        """
        try:
            times_collection = get_collection("processing_times")

            # Get processing times for the operation
            query = {"operation": operation}
            processing_times = list(times_collection.find(query).sort("timestamp", -1).limit(20))

            if not processing_times:
                # No data available, return a default estimate
                return {
                    "operation": operation,
                    "record_count": record_count,
                    "estimated_seconds": record_count * 0.1,  # Default estimate
                    "confidence": "low",
                    "based_on_samples": 0
                }

            # Calculate time per record for each sample
            times_per_record = []
            for pt in processing_times:
                if pt.get("record_count", 0) > 0:
                    times_per_record.append(pt.get("duration_seconds", 0) / pt.get("record_count"))

            if not times_per_record:
                # No valid data available, return a default estimate
                return {
                    "operation": operation,
                    "record_count": record_count,
                    "estimated_seconds": record_count * 0.1,  # Default estimate
                    "confidence": "low",
                    "based_on_samples": 0
                }

            # Calculate average time per record
            avg_time_per_record = statistics.mean(times_per_record)

            # Calculate estimated time
            estimated_seconds = avg_time_per_record * record_count

            # Determine confidence level
            if len(times_per_record) >= 10:
                confidence = "high"
            elif len(times_per_record) >= 5:
                confidence = "medium"
            else:
                confidence = "low"

            return {
                "operation": operation,
                "record_count": record_count,
                "estimated_seconds": estimated_seconds,
                "confidence": confidence,
                "based_on_samples": len(times_per_record)
            }

        except Exception as e:
            logger.error(f"Error getting estimated time: {str(e)}")
            raise

    @staticmethod
    def get_all_processing_times(operation: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all processing times.

        Args:
            operation: Optional operation name to filter by
            limit: Maximum number of records to return

        Returns:
            List of processing times
        """
        try:
            times_collection = get_collection("processing_times")

            # Build query
            query = {}
            if operation:
                query["operation"] = operation

            # Get processing times
            processing_times = list(
                times_collection.find(query)
                .sort("timestamp", -1)
                .limit(limit)
            )

            # Convert ObjectId to string
            for pt in processing_times:
                pt["_id"] = str(pt["_id"])

            return processing_times

        except Exception as e:
            logger.error(f"Error getting processing times: {str(e)}")
            raise

# Create singleton instance
mongo_timing_service = MongoTimingService()
