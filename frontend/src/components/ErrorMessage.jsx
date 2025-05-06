import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ExclamationCircleIcon } from '@heroicons/react/24/outline';

/**
 * Component for displaying error messages
 */
const ErrorMessage = ({ error }) => {
  if (!error) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        className="mt-4 p-4 bg-red-50 text-red-700 rounded-md flex items-start"
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -10 }}
        transition={{ duration: 0.3 }}
      >
        <ExclamationCircleIcon className="w-5 h-5 mr-2 flex-shrink-0 mt-0.5" />
        <span>{error}</span>
      </motion.div>
    </AnimatePresence>
  );
};

export default ErrorMessage;
