import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ChartBarIcon, ClockIcon } from '@heroicons/react/24/outline';
import ProgressBar from './ProgressBar';

/**
 * Component to display batch processing status
 */
const BatchProcessingStatus = ({ 
  currentBatch = 1, 
  totalBatches = 1, 
  batchSize = 100,
  totalItems = 0,
  processingSpeed = 0, // items per second
  remainingTime = 0,
  className = ''
}) => {
  // Calculate progress percentage
  const progress = Math.min(((currentBatch - 1) / totalBatches) * 100, 100);
  
  // Format time remaining
  const formatTime = (seconds) => {
    if (seconds < 60) {
      return `${Math.round(seconds)} seconds`;
    } else if (seconds < 3600) {
      return `${Math.floor(seconds / 60)} minutes ${Math.round(seconds % 60)} seconds`;
    } else {
      return `${Math.floor(seconds / 3600)} hours ${Math.floor((seconds % 3600) / 60)} minutes`;
    }
  };

  // Calculate items processed
  const itemsProcessed = Math.min((currentBatch - 1) * batchSize, totalItems);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`bg-blue-50 border border-blue-200 rounded-lg p-4 ${className}`}
    >
      <div className="flex items-center mb-2">
        <ChartBarIcon className="h-5 w-5 text-blue-500 mr-2" />
        <h3 className="text-sm font-medium text-blue-700">Batch Processing Status</h3>
      </div>
      
      <div className="mb-3">
        <ProgressBar 
          progress={progress} 
          height={6} 
          color="#3b82f6" 
          showPercentage={true} 
        />
      </div>
      
      <div className="grid grid-cols-2 gap-2 text-xs text-gray-600">
        <div>
          <span className="font-medium">Current Batch:</span> {currentBatch} of {totalBatches}
        </div>
        <div>
          <span className="font-medium">Batch Size:</span> {batchSize} items
        </div>
        <div>
          <span className="font-medium">Items Processed:</span> {itemsProcessed} of {totalItems}
        </div>
        <div>
          <span className="font-medium">Processing Speed:</span> {processingSpeed.toFixed(2)} items/sec
        </div>
      </div>
      
      {remainingTime > 0 && (
        <div className="mt-3 flex items-center text-xs text-blue-600">
          <ClockIcon className="h-4 w-4 mr-1" />
          <span>
            <span className="font-medium">Estimated time remaining:</span> {formatTime(remainingTime)}
          </span>
        </div>
      )}
    </motion.div>
  );
};

export default BatchProcessingStatus;
