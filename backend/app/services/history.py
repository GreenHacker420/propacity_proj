import logging
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.analysis_history import AnalysisHistory, AnalysisHistoryCreate, AnalysisHistoryList

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HistoryService:
    """Service for tracking analysis history"""
    
    def record_analysis(
        self, 
        db: Session, 
        history_data: AnalysisHistoryCreate, 
        user_id: Optional[int] = None
    ) -> AnalysisHistory:
        """
        Record an analysis in the history
        
        Args:
            db: Database session
            history_data: Analysis history data
            user_id: Optional user ID
            
        Returns:
            The created AnalysisHistory record
        """
        db_history = AnalysisHistory(
            source_type=history_data.source_type,
            source_name=history_data.source_name,
            record_count=history_data.record_count,
            avg_sentiment_score=history_data.avg_sentiment_score,
            pain_point_count=history_data.pain_point_count,
            feature_request_count=history_data.feature_request_count,
            positive_feedback_count=history_data.positive_feedback_count,
            summary=history_data.summary,
            user_id=user_id
        )
        
        db.add(db_history)
        db.commit()
        db.refresh(db_history)
        
        logger.info(f"Recorded analysis history: {db_history}")
        return db_history
    
    def get_analysis_history(
        self, 
        db: Session, 
        user_id: Optional[int] = None,
        source_type: Optional[str] = None,
        skip: int = 0, 
        limit: int = 100
    ) -> AnalysisHistoryList:
        """
        Get analysis history
        
        Args:
            db: Database session
            user_id: Optional filter by user ID
            source_type: Optional filter by source type
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of AnalysisHistory records
        """
        query = db.query(AnalysisHistory)
        
        if user_id is not None:
            query = query.filter(AnalysisHistory.user_id == user_id)
        
        if source_type:
            query = query.filter(AnalysisHistory.source_type == source_type)
        
        total = query.count()
        items = query.order_by(AnalysisHistory.timestamp.desc()).offset(skip).limit(limit).all()
        
        return AnalysisHistoryList(
            items=items,
            total=total
        )
    
    def get_analysis_by_id(self, db: Session, analysis_id: int) -> Optional[AnalysisHistory]:
        """
        Get a specific analysis history record by ID
        
        Args:
            db: Database session
            analysis_id: Analysis history ID
            
        Returns:
            AnalysisHistory record if found, None otherwise
        """
        return db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()
    
    def delete_analysis(self, db: Session, analysis_id: int) -> bool:
        """
        Delete an analysis history record
        
        Args:
            db: Database session
            analysis_id: Analysis history ID
            
        Returns:
            True if deleted, False if not found
        """
        db_history = db.query(AnalysisHistory).filter(AnalysisHistory.id == analysis_id).first()
        if not db_history:
            return False
        
        db.delete(db_history)
        db.commit()
        return True

# Create a history service instance
history_service = HistoryService()
