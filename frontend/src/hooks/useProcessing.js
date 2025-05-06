import { useState, useEffect } from 'react';
import api from '../services/api';

// Default processing steps
const defaultProcessingSteps = [
  {
    label: 'Uploading data',
    description: 'Transferring your data to our servers',
    estimatedTime: '10-20 seconds'
  },
  {
    label: 'Analyzing sentiment',
    description: 'Determining positive and negative feedback',
    estimatedTime: '30-45 seconds'
  },
  {
    label: 'Categorizing feedback',
    description: 'Identifying pain points, feature requests, and positive feedback',
    estimatedTime: '20-30 seconds'
  },
  {
    label: 'Extracting insights',
    description: 'Generating actionable recommendations',
    estimatedTime: '15-25 seconds'
  },
  {
    label: 'Creating summary',
    description: 'Preparing your feedback dashboard',
    estimatedTime: '5-10 seconds'
  }
];

// Operation types for each processing step
const operationTypes = [
  "upload",
  "sentiment_analysis",
  "categorization",
  "keyword_extraction",
  "summary_generation"
];

/**
 * Custom hook for managing processing state and progress
 */
const useProcessing = (initialRecordCount = 50) => {
  // Processing state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [processingStep, setProcessingStep] = useState(0);
  const [processingSteps, setProcessingSteps] = useState(defaultProcessingSteps);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [estimatedTime, setEstimatedTime] = useState(null);
  const [recordCount, setRecordCount] = useState(initialRecordCount);

  // Update estimated time when processing step changes
  useEffect(() => {
    if (loading && processingStep < processingSteps.length) {
      updateEstimatedTime();
    }
  }, [loading, processingStep, recordCount]);

  // Get estimated time from the backend
  const updateEstimatedTime = async () => {
    const operation = operationTypes[processingStep];
    
    if (operation) {
      try {
        const timeEstimate = await api.getEstimatedTime(operation, recordCount);
        setEstimatedTime(timeEstimate.estimated_seconds);
        
        // Update the processingSteps with the new estimated time
        const updatedSteps = [...processingSteps];
        updatedSteps[processingStep].estimatedTime = 
          `${Math.floor(timeEstimate.estimated_seconds)} seconds`;
        
        setProcessingSteps(updatedSteps);
      } catch (error) {
        console.error("Error getting time estimate:", error);
        
        // Fall back to static estimates if API call fails
        const currentStepTime = processingSteps[processingStep].estimatedTime;
        const timeRange = currentStepTime.split('-');
        const avgTime = (parseInt(timeRange[0]) + parseInt(timeRange[1].split(' ')[0])) / 2;
        setEstimatedTime(avgTime);
      }
    } else {
      // Fall back to static estimates if no operation mapping
      const currentStepTime = processingSteps[processingStep].estimatedTime;
      const timeRange = currentStepTime.split('-');
      const avgTime = (parseInt(timeRange[0]) + parseInt(timeRange[1].split(' ')[0])) / 2;
      setEstimatedTime(avgTime);
    }
  };

  // Start a progress simulation
  const startProgressSimulation = (intervalTime = 300, increment = 5, callback = null) => {
    const interval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 95) {
          clearInterval(interval);
          if (callback) callback();
          return prev;
        }
        return prev + increment;
      });
    }, intervalTime);
    
    return interval;
  };

  // Complete progress
  const completeProgress = () => {
    setUploadProgress(100);
  };

  // Reset processing state
  const resetProcessing = () => {
    setLoading(false);
    setUploadProgress(0);
    setProcessingStep(0);
    setError(null);
  };

  return {
    loading,
    setLoading,
    error,
    setError,
    processingStep,
    setProcessingStep,
    processingSteps,
    uploadProgress,
    estimatedTime,
    setRecordCount,
    startProgressSimulation,
    completeProgress,
    resetProcessing
  };
};

export default useProcessing;
