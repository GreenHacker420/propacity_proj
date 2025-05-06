import React from 'react';
import { ClipLoader, BeatLoader } from 'react-spinners';
import { motion } from 'framer-motion';

const LoadingIndicator = ({ type = 'clip', size = 35, color = '#0284c7', text = 'Loading...' }) => {
  const getLoader = () => {
    switch (type) {
      case 'beat':
        return <BeatLoader color={color} size={size / 2.5} />;
      case 'clip':
      default:
        return <ClipLoader color={color} size={size} />;
    }
  };

  return (
    <motion.div 
      className="flex flex-col items-center justify-center p-4"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      {getLoader()}
      {text && (
        <motion.p 
          className="mt-3 text-sm text-gray-600 font-medium"
          initial={{ y: -10, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          {text}
        </motion.p>
      )}
    </motion.div>
  );
};

export default LoadingIndicator;
