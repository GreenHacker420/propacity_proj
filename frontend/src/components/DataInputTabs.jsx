import React, { useState } from 'react';
import { Tab } from '@headlessui/react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { motion } from 'framer-motion';
import FileDropzone from './FileDropzone';

// Helper function for class names
function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

/**
 * Component for data input tabs (Upload CSV, Scrape Data)
 */
const DataInputTabs = ({
  onFileUpload,
  onScrape,
  loading,
  uploadProgress
}) => {
  // Tab state
  const [selectedTab, setSelectedTab] = useState(0);

  // File upload state
  const [file, setFile] = useState(null);

  // Scraping state
  const [scrapeSource, setScrapeSource] = useState('playstore');
  const [scrapeQuery, setScrapeQuery] = useState('');
  const [scrapeLimit, setScrapeLimit] = useState(50); // Default to minimum value of 50

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
    // Validate the review limit
    if (scrapeLimit < 50 || scrapeLimit > 5000) {
      alert('Number of reviews must be between 50 and 5000');
      return;
    }

    if (scrapeQuery) {
      // For Play Store, validate the URL format
      if (scrapeSource === 'playstore') {
        const appIdMatch = scrapeQuery.match(/id=([^&]+)/);
        if (!appIdMatch) {
          alert('Please enter a valid Google Play Store URL (e.g., https://play.google.com/store/apps/details?id=com.example.app)');
          return;
        }
        // Pass the full URL as the query parameter
        onScrape(scrapeSource, scrapeQuery, scrapeLimit);
      } else {
        onScrape(scrapeSource, scrapeQuery, scrapeLimit);
      }
    } else {
      alert('Please enter a search query or app URL');
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
            <h2 className="text-lg font-medium text-gray-800 mb-4">Scrape Data</h2>
            <div className="space-y-4">
              {/* Source Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Data Source
                </label>
                <select
                  value={scrapeSource}
                  onChange={(e) => setScrapeSource(e.target.value)}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                >
                  <option value="playstore">Google Play Store</option>
                  <option value="twitter">Twitter</option>
                </select>
              </div>

              {/* Query Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {scrapeSource === 'playstore' ? 'App URL' : 'Search Query'}
                </label>
                <input
                  type="text"
                  value={scrapeQuery}
                  onChange={(e) => setScrapeQuery(e.target.value)}
                  placeholder={scrapeSource === 'playstore'
                    ? "https://play.google.com/store/apps/details?id=com.example.app"
                    : "Enter search query"}
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                {scrapeSource === 'playstore' && (
                  <p className="mt-1 text-sm text-gray-500">
                    Enter the full Google Play Store URL of the app
                  </p>
                )}
              </div>

              {/* Limit Input */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Number of Reviews
                </label>
                <input
                  type="number"
                  value={scrapeLimit}
                  onChange={(e) => {
                    const value = parseInt(e.target.value);
                    // Ensure the value is within the valid range
                    if (value < 50) {
                      setScrapeLimit(50);
                    } else if (value > 5000) {
                      setScrapeLimit(5000);
                    } else {
                      setScrapeLimit(value);
                    }
                  }}
                  min="50"
                  max="5000"
                  className="w-full rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Enter a value between 50 and 5000 reviews
                </p>
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
      </Tab.Panels>
    </Tab.Group>
  );
};

export default DataInputTabs;
