import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircleIcon } from '@heroicons/react/24/solid';
import { ClockIcon } from '@heroicons/react/24/outline';
import LoadingIndicator from './LoadingIndicator';
import APIStatusIndicator from './APIStatusIndicator';
import APIQuotaDisplay from './APIQuotaDisplay';

const ProcessingSteps = ({ steps, currentStep, apiStatus, onClearApiStatus }) => {
  return (
    <div className="w-full max-w-md mx-auto">
      {apiStatus && apiStatus.error && (
        apiStatus.error.includes('quota') ? (
          <APIQuotaDisplay apiStatus={apiStatus} className="mb-4" />
        ) : (
          <APIStatusIndicator
            apiStatus={apiStatus}
            onClose={onClearApiStatus}
            showDetails={true}
          />
        )
      )}
      <div className="space-y-4">
        {steps.map((step, index) => {
          const isCompleted = index < currentStep;
          const isActive = index === currentStep;

          return (
            <motion.div
              key={index}
              className={`flex items-center p-3 rounded-lg ${
                isActive ? 'bg-primary-50 border border-primary-200' :
                isCompleted ? 'bg-green-50' : 'bg-gray-50'
              }`}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <div className="flex-shrink-0 mr-3">
                {isCompleted ? (
                  <CheckCircleIcon className="w-6 h-6 text-green-500" />
                ) : isActive ? (
                  <LoadingIndicator type="beat" size={20} color="#0284c7" text="" />
                ) : (
                  <ClockIcon className="w-6 h-6 text-gray-400" />
                )}
              </div>
              <div className="flex-1">
                <p className={`text-sm font-medium ${
                  isActive ? 'text-primary-700' :
                  isCompleted ? 'text-green-700' : 'text-gray-500'
                }`}>
                  {step.label}
                </p>
                {step.description && (
                  <p className="text-xs text-gray-500">{step.description}</p>
                )}
                {isActive && step.estimatedTime && (
                  <p className="text-xs text-primary-600 mt-1">
                    Estimated time: {step.estimatedTime}
                  </p>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};

export default ProcessingSteps;
