"""
Optimized sentiment analysis implementation with better parallel processing
and resource management to prevent API timeouts during processing.
"""

import concurrent.futures
import os
import logging
import time
from typing import List, Dict, Any, Callable, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OptimizedSentimentProcessor:
    """
    Optimized sentiment processor that uses parallel processing and resource management
    to prevent API timeouts during processing.
    """
    
    def __init__(self, 
                 max_workers: int = None, 
                 batch_size: int = 100,
                 max_cpu_percent: float = 80.0):
        """
        Initialize the optimized sentiment processor.
        
        Args:
            max_workers: Maximum number of worker threads to use (default: CPU count * 2)
            batch_size: Size of batches to process at once
            max_cpu_percent: Maximum CPU percentage to use before throttling
        """
        self.max_workers = max_workers or min(32, os.cpu_count() * 2)
        self.batch_size = batch_size
        self.max_cpu_percent = max_cpu_percent
        logger.info(f"Initialized OptimizedSentimentProcessor with {self.max_workers} workers")
        
    def process_batch(self, 
                     texts: List[str], 
                     processor_func: Callable[[str], Any],
                     progress_callback: Optional[Callable] = None) -> List[Any]:
        """
        Process a batch of texts using parallel processing with resource management.
        
        Args:
            texts: List of texts to process
            processor_func: Function to process each text
            progress_callback: Optional callback function for progress updates
            
        Returns:
            List of processing results
        """
        if not texts:
            return []
            
        start_time = time.time()
        logger.info(f"Starting batch processing of {len(texts)} texts")
        
        # Split into smaller batches for better progress reporting and resource management
        batches = [texts[i:i+self.batch_size] for i in range(0, len(texts), self.batch_size)]
        results = []
        total_processed = 0
        
        for batch_idx, batch in enumerate(batches):
            batch_start_time = time.time()
            
            # Check CPU usage and throttle if necessary
            self._throttle_if_needed()
            
            # Process batch in parallel
            batch_results = self._process_parallel(batch, processor_func)
            results.extend(batch_results)
            
            # Update progress
            total_processed += len(batch)
            batch_time = time.time() - batch_start_time
            progress = total_processed / len(texts) * 100
            
            # Calculate metrics
            elapsed_time = time.time() - start_time
            avg_speed = total_processed / elapsed_time if elapsed_time > 0 else 0
            estimated_remaining = (len(texts) - total_processed) / avg_speed if avg_speed > 0 else 0
            
            logger.info(f"Batch {batch_idx+1}/{len(batches)} completed in {batch_time:.2f}s - "
                       f"{progress:.1f}% complete, {avg_speed:.1f} items/sec, "
                       f"~{estimated_remaining:.1f}s remaining")
            
            # Call progress callback if provided
            if progress_callback:
                progress_callback(
                    batch_idx + 1, 
                    len(batches),
                    batch_time,
                    total_processed,
                    len(texts),
                    avg_speed,
                    estimated_remaining
                )
                
            # Force garbage collection periodically
            if batch_idx % 5 == 0 and batch_idx > 0:
                self._collect_garbage()
        
        total_time = time.time() - start_time
        logger.info(f"Completed batch processing in {total_time:.2f}s - "
                   f"Average speed: {len(texts)/total_time:.1f} items/sec")
        
        return results
    
    def _process_parallel(self, batch: List[str], processor_func: Callable[[str], Any]) -> List[Any]:
        """Process a batch of texts in parallel"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            return list(executor.map(processor_func, batch))
    
    def _throttle_if_needed(self):
        """Check CPU usage and throttle if necessary"""
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=0.1)
            if cpu_percent > self.max_cpu_percent:
                sleep_time = (cpu_percent - self.max_cpu_percent) / 100
                logger.info(f"CPU usage at {cpu_percent:.1f}% - throttling for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        except ImportError:
            # psutil not available, skip throttling
            pass
    
    def _collect_garbage(self):
        """Force garbage collection to free memory"""
        try:
            import gc
            before = self._get_memory_usage()
            gc.collect()
            after = self._get_memory_usage()
            logger.info(f"Garbage collection freed {before-after:.1f} MB")
        except Exception:
            # Ignore errors in garbage collection
            pass
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

# Create a singleton instance
optimized_processor = OptimizedSentimentProcessor()
