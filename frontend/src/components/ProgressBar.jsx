import React from 'react';
import { motion } from 'framer-motion';

const ProgressBar = ({ progress, height = 8, color = '#0284c7', showPercentage = true }) => {
  return (
    <div className="w-full">
      <div className="w-full bg-gray-200 rounded-full" style={{ height: `${height}px` }}>
        <motion.div
          className="rounded-full"
          style={{ 
            backgroundColor: color,
            height: '100%',
          }}
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5 }}
        />
      </div>
      {showPercentage && (
        <div className="text-right mt-1">
          <span className="text-xs font-medium text-gray-600">{Math.round(progress)}%</span>
        </div>
      )}
    </div>
  );
};

export default ProgressBar;
