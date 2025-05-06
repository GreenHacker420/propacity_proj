import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { CodeBracketIcon } from '@heroicons/react/24/outline';

const GitHubRepoInput = ({ onSubmit, isLoading }) => {
  const [repoUrl, setRepoUrl] = useState('');
  const [error, setError] = useState('');

  const validateUrl = (url) => {
    // Basic GitHub URL validation
    const githubRegex = /^https?:\/\/(www\.)?github\.com\/[\w-]+\/[\w.-]+\/?$/;
    return githubRegex.test(url);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!repoUrl.trim()) {
      setError('Please enter a GitHub repository URL');
      return;
    }
    
    if (!validateUrl(repoUrl)) {
      setError('Please enter a valid GitHub repository URL');
      return;
    }
    
    setError('');
    onSubmit(repoUrl);
  };

  return (
    <motion.div 
      className="w-full"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            GitHub Repository URL
          </label>
          <div className="relative rounded-md shadow-sm">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <CodeBracketIcon className="h-5 w-5 text-gray-400" />
            </div>
            <input
              type="text"
              className={`input pl-10 ${error ? 'border-red-300 focus:ring-red-500' : ''}`}
              placeholder="https://github.com/username/repository"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              disabled={isLoading}
            />
          </div>
          {error && (
            <p className="mt-1 text-sm text-red-600">{error}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Enter the URL of a public GitHub repository to analyze its issues and discussions
          </p>
        </div>

        <div className="flex items-center space-x-4">
          <button
            type="submit"
            className="btn btn-primary w-full"
            disabled={isLoading}
          >
            {isLoading ? 'Analyzing...' : 'Analyze Repository'}
          </button>
        </div>
      </form>
    </motion.div>
  );
};

export default GitHubRepoInput;
