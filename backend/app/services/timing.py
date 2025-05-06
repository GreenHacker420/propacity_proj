import logging
import time
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.processing_time import ProcessingTime, ProcessingTimeCreate, EstimatedProcessingTime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TimingService:
    """Service for tracking and estimating processing times"""
    
    def __init__(self):
        # Default estimated times (in seconds) if no historical data is available
        self.default_times = {
            "upload": 5.0,
            "scrape": 10.0,
            "sentiment_analysis": 15.0,
            "categorization": 8.0,
            "keyword_extraction": 5.0,
            "summary_generation": 3.0
        }
        
        # Default estimated times per record (in seconds)
        self.default_times_per_record = {
            "upload": 0.05,
            "scrape": 0.1,
            "sentiment_analysis": 0.15,
            "categorization": 0.08,
            "keyword_extraction": 0.05,
            "summary_generation": 0.03
        }
    
    def record_processing_time(self, db: Session, time_data: ProcessingTimeCreate) -> ProcessingTime:
        """
        Record the time taken for a processing operation
        
        Args:
            db: Database session
            time_data: Processing time data
            
        Returns:
            The created ProcessingTime record
        """
        db_time = ProcessingTime(
            operation=time_data.operation,
            file_name=time_data.file_name,
            source=time_data.source,
            query=time_data.query,
            record_count=time_data.record_count,
            duration_seconds=time_data.duration_seconds
        )
        
        db.add(db_time)
        db.commit()
        db.refresh(db_time)
        
        logger.info(f"Recorded processing time: {db_time}")
        return db_time
    
    def get_estimated_time(self, db: Session, operation: str, record_count: int) -> EstimatedProcessingTime:
        """
        Get estimated processing time for an operation based on historical data
        
        Args:
            db: Database session
            operation: The operation type
            record_count: Number of records to process
            
        Returns:
            Estimated processing time
        """
        # Get average processing time from historical data
        avg_time, avg_time_per_record = self._calculate_average_time(db, operation)
        
        # If no historical data, use defaults
        if avg_time is None:
            avg_time = self.default_times.get(operation, 5.0)
            avg_time_per_record = self.default_times_per_record.get(operation, 0.05)
        
        # Calculate estimated time based on record count
        estimated_seconds = avg_time + (avg_time_per_record * record_count)
        
        return EstimatedProcessingTime(
            operation=operation,
            estimated_seconds=estimated_seconds,
            estimated_seconds_per_record=avg_time_per_record
        )
    
    def _calculate_average_time(self, db: Session, operation: str) -> Tuple[Optional[float], Optional[float]]:
        """
        Calculate average processing time from historical data
        
        Args:
            db: Database session
            operation: The operation type
            
        Returns:
            Tuple of (average_time, average_time_per_record)
        """
        # Get the 10 most recent processing times for this operation
        recent_times = db.query(ProcessingTime).filter(
            ProcessingTime.operation == operation
        ).order_by(ProcessingTime.timestamp.desc()).limit(10).all()
        
        if not recent_times:
            return None, None
        
        # Calculate average time
        total_time = sum(time_record.duration_seconds for time_record in recent_times)
        avg_time = total_time / len(recent_times)
        
        # Calculate average time per record
        total_time_per_record = sum(
            time_record.duration_seconds / time_record.record_count 
            for time_record in recent_times 
            if time_record.record_count > 0
        )
        avg_time_per_record = total_time_per_record / len(recent_times)
        
        return avg_time, avg_time_per_record
    
    def get_all_processing_times(self, db: Session, operation: Optional[str] = None, limit: int = 100) -> List[ProcessingTime]:
        """
        Get all processing time records
        
        Args:
            db: Database session
            operation: Optional filter by operation type
            limit: Maximum number of records to return
            
        Returns:
            List of ProcessingTime records
        """
        query = db.query(ProcessingTime)
        
        if operation:
            query = query.filter(ProcessingTime.operation == operation)
        
        return query.order_by(ProcessingTime.timestamp.desc()).limit(limit).all()

# Create a timing service instance
timing_service = TimingService()
