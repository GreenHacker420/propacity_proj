import React from 'react';
import { motion } from 'framer-motion';
import CodeBlock from './CodeBlock';

/**
 * Component for displaying GitHub repository details
 */
const GitHubDetails = ({ repoData, repoUrl }) => {
  if (!repoData) {
    return null;
  }

  return (
    <motion.div
      className="mt-8"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.5 }}
    >
      <h2 className="text-2xl font-bold text-gray-900 mb-6">GitHub Repository Analysis</h2>
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Repository Details</h3>
        <div className="mb-4">
          <p className="text-sm text-gray-700 mb-2">
            <span className="font-medium">Repository URL:</span> {repoUrl}
          </p>
          <p className="text-sm text-gray-700">
            <span className="font-medium">Issues Analyzed:</span> {repoData.issues.length}
          </p>
          <p className="text-sm text-gray-700">
            <span className="font-medium">Discussions Analyzed:</span> {repoData.discussions.length}
          </p>
        </div>

        <h4 className="text-md font-medium text-gray-800 mb-2">Sample Issue</h4>
        <CodeBlock
          code={JSON.stringify(repoData.issues[0], null, 2)}
          language="json"
        />
      </div>
    </motion.div>
  );
};

export default GitHubDetails;
