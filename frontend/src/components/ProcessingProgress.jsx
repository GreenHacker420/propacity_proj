import React from 'react';
import { motion } from 'framer-motion';

const ProcessingProgress = ({ step, progress }) => {
  const steps = [
    { id: 0, label: 'Data Upload' },
    { id: 1, label: 'Sentiment Analysis' },
    { id: 2, label: 'Categorization' },
    { id: 3, label: 'Keyword Extraction' },
    { id: 4, label: 'Summary Generation' }
  ];

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="flex justify-between mb-4">
        {steps.map((s) => (
          <div
            key={s.id}
            className={`flex flex-col items-center ${
              s.id <= step ? 'text-blue-600' : 'text-gray-400'
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center mb-2 ${
                s.id < step
                  ? 'bg-blue-600 text-white'
                  : s.id === step
                  ? 'bg-blue-100 text-blue-600 border-2 border-blue-600'
                  : 'bg-gray-100 text-gray-400'
              }`}
            >
              {s.id < step ? '✓' : s.id + 1}
            </div>
            <span className="text-sm font-medium">{s.label}</span>
          </div>
        ))}
      </div>

      <div className="relative h-2 bg-gray-200 rounded-full overflow-hidden">
        <motion.div
          className="absolute top-0 left-0 h-full bg-blue-600"
          initial={{ width: '0%' }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.3 }}
        />
      </div>

      <div className="mt-4 text-center text-sm text-gray-600">
        {step < steps.length - 1
          ? `Processing ${steps[step].label.toLowerCase()}...`
          : 'Processing complete!'}
      </div>
    </div>
  );
};

export default ProcessingProgress; 