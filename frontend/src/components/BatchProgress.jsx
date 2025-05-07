import React, { useState, useEffect } from 'react';
import { Progress, Box, Text, Flex, Badge } from '@chakra-ui/react';

/**
 * Component to display batch processing progress
 * 
 * @param {Object} props Component props
 * @param {Object} props.status Batch processing status
 * @param {boolean} props.isVisible Whether the component is visible
 * @param {function} props.onComplete Callback when processing is complete
 */
const BatchProgress = ({ status, isVisible, onComplete }) => {
  const [timeRemaining, setTimeRemaining] = useState('');
  
  useEffect(() => {
    // Format time remaining
    if (status && status.estimated_time_remaining) {
      const seconds = Math.round(status.estimated_time_remaining);
      if (seconds < 60) {
        setTimeRemaining(`${seconds} seconds`);
      } else {
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        setTimeRemaining(`${minutes} min ${remainingSeconds} sec`);
      }
    }
    
    // Call onComplete when processing is done
    if (status && status.progress_percentage === 100 && onComplete) {
      // Add a small delay to show 100% before completing
      setTimeout(() => {
        onComplete();
      }, 1000);
    }
  }, [status, onComplete]);
  
  if (!isVisible || !status) {
    return null;
  }
  
  return (
    <Box 
      p={4} 
      borderWidth="1px" 
      borderRadius="lg" 
      boxShadow="md" 
      bg="white" 
      mb={4}
    >
      <Flex justify="space-between" mb={2}>
        <Text fontWeight="bold">Processing Reviews</Text>
        <Badge colorScheme={status.progress_percentage < 100 ? "blue" : "green"}>
          {status.progress_percentage < 100 ? "Processing" : "Complete"}
        </Badge>
      </Flex>
      
      <Progress 
        value={status.progress_percentage} 
        size="sm" 
        colorScheme="blue" 
        mb={2} 
        borderRadius="md"
        hasStripe={status.progress_percentage < 100}
        isAnimated={status.progress_percentage < 100}
      />
      
      <Flex justify="space-between" fontSize="sm" color="gray.600">
        <Text>
          {status.items_processed} / {status.total_items} items
          {status.avg_speed ? ` (${status.avg_speed.toFixed(1)} items/sec)` : ''}
        </Text>
        {timeRemaining && status.progress_percentage < 100 && (
          <Text>Est. time remaining: {timeRemaining}</Text>
        )}
      </Flex>
      
      {status.current_batch && status.total_batches && (
        <Text fontSize="xs" color="gray.500" mt={1}>
          Batch {status.current_batch} of {status.total_batches}
          {status.batch_time ? ` (${status.batch_time.toFixed(1)}s per batch)` : ''}
        </Text>
      )}
    </Box>
  );
};

export default BatchProgress;
