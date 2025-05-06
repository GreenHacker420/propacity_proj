import React, { useState } from 'react';
import { Tab } from '@headlessui/react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import FileDropzone from './FileDropzone';
import GitHubRepoInput from './GitHubRepoInput';

// Helper function for class names
function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

/**
 * Component for data input tabs (Upload CSV, Scrape Data, GitHub Repo)
 */
const DataInputTabs = ({ 
  onFileUpload, 
  onScrape, 
  onGitHubAnalysis, 
  loading, 
  uploadProgress 
}) => {
  // Tab state
  const [selectedTab, setSelectedTab] = useState(0);
  
  // File upload state
  const [file, setFile] = useState(null);
  
  // Scraping state
  const [scrapeSource, setScrapeSource] = useState('twitter');
  const [scrapeQuery, setScrapeQuery] = useState('');
  const [scrapeLimit, setScrapeLimit] = useState(50);
  
  // Handle file selection
  const handleFileSelected = (selectedFile) => {
    setFile(selectedFile);
  };
  
  // Handle file upload
  const handleFileUpload = () => {
    if (file) {
      onFileUpload(file);
    }
  };
  
  // Handle scrape
  const handleScrape = () => {
    if (scrapeQuery) {
      onScrape(scrapeSource, scrapeQuery, scrapeLimit);
    }
  };
  
  return (
    <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
      <Tab.List className="flex space-x-1 rounded-xl bg-primary-900/20 p-1">
        <Tab
          className={({ selected }) =>
            classNames(
              'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
              'ring-white ring-opacity-60 ring-offset-2 ring-offset-primary-400 focus:outline-none focus:ring-2',
              selected
                ? 'bg-white text-primary-700 shadow'
                : 'text-primary-100 hover:bg-white/[0.12] hover:text-white'
            )
          }
        >
          Upload CSV
        </Tab>
        <Tab
          className={({ selected }) =>
            classNames(
              'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
              'ring-white ring-opacity-60 ring-offset-2 ring-offset-primary-400 focus:outline-none focus:ring-2',
              selected
                ? 'bg-white text-primary-700 shadow'
                : 'text-primary-100 hover:bg-white/[0.12] hover:text-white'
            )
          }
        >
          Scrape Data
        </Tab>
        <Tab
          className={({ selected }) =>
            classNames(
              'w-full rounded-lg py-2.5 text-sm font-medium leading-5',
              'ring-white ring-opacity-60 ring-offset-2 ring-offset-primary-400 focus:outline-none focus:ring-2',
              selected
                ? 'bg-white text-primary-700 shadow'
                : 'text-primary-100 hover:bg-white/[0.12] hover:text-white'
            )
          }
        >
          GitHub Repo
        </Tab>
      </Tab.List>

      <Tab.Panels className="mt-6">
        {/* Upload CSV Panel */}
        <Tab.Panel>
          <motion.div
            className="card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="text-lg font-medium text-gray-800 mb-4">Upload CSV File</h2>
            <FileDropzone
              onFileAccepted={handleFileSelected}
              isUploading={loading}
              uploadProgress={uploadProgress}
            />

            {file && (
              <div className="mt-4">
                <button
                  className="btn btn-primary w-full"
                  onClick={handleFileUpload}
                  disabled={loading || !file}
                >
                  {loading ? 'Processing...' : 'Analyze File'}
                </button>
              </div>
            )}
          </motion.div>
        </Tab.Panel>

        {/* Scrape Data Panel */}
        <Tab.Panel>
          <motion.div
            className="card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="text-lg font-medium text-gray-800 mb-4">Scrape Online Reviews</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Source</label>
                <select
                  className="input mt-1"
                  value={scrapeSource}
                  onChange={(e) => setScrapeSource(e.target.value)}
                  disabled={loading}
                >
                  <option value="twitter">Twitter</option>
                  <option value="playstore">Google Play Store</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  {scrapeSource === 'twitter' ? 'Search Query' : 'App ID'}
                </label>
                <input
                  type="text"
                  className="input mt-1"
                  value={scrapeQuery}
                  onChange={(e) => setScrapeQuery(e.target.value)}
                  placeholder={scrapeSource === 'twitter' ? 'e.g., spotify OR #spotify' : 'e.g., com.instagram.android'}
                  disabled={loading}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">Limit</label>
                <input
                  type="number"
                  className="input mt-1"
                  value={scrapeLimit}
                  onChange={(e) => setScrapeLimit(parseInt(e.target.value))}
                  min="1"
                  max="100"
                  disabled={loading}
                />
              </div>

              <button
                className="btn btn-primary w-full"
                onClick={handleScrape}
                disabled={loading || !scrapeQuery}
              >
                <MagnifyingGlassIcon className="w-5 h-5 inline-block mr-2" />
                {loading ? 'Processing...' : 'Scrape Data'}
              </button>
            </div>
          </motion.div>
        </Tab.Panel>

        {/* GitHub Repo Panel */}
        <Tab.Panel>
          <motion.div
            className="card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <h2 className="text-lg font-medium text-gray-800 mb-4">Analyze GitHub Repository</h2>
            <GitHubRepoInput onSubmit={onGitHubAnalysis} isLoading={loading} />
          </motion.div>
        </Tab.Panel>
      </Tab.Panels>
    </Tab.Group>
  );
};

export default DataInputTabs;
