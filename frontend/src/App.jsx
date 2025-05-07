import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Import custom hooks
import useProcessing from './hooks/useProcessing';
import useDataProcessing from './hooks/useDataProcessing';

// Import components
import Header from './components/Header';
import DataInputTabs from './components/DataInputTabs';
import ProcessingSteps from './components/ProcessingSteps';
import LoadingIndicator from './components/LoadingIndicator';
import ErrorMessage from './components/ErrorMessage';
import ReviewsTable from './components/ReviewsTable';
import SummaryView from './components/SummaryView';
import HistoryView from './components/HistoryView';
import GitHubDetails from './components/GitHubDetails';
import APIStatusIndicator from './components/APIStatusIndicator';
import APIQuotaDisplay from './components/APIQuotaDisplay';
import GeminiStatusIndicator from './components/GeminiStatusIndicator';

/**
 * Main App component
 */
function App() {
  // Initialize processing hook
  const processingHook = useProcessing();
  const {
    loading,
    error,
    processingStep,
    processingSteps,
    uploadProgress,
    estimatedTime,
    apiStatus,
    clearApiStatus
  } = processingHook;

  // Initialize data processing hook
  const dataHook = useDataProcessing(processingHook);
  const {
    analyzedReviews,
    summary,
    activeView,
    setActiveView,
    processFileUpload,
    processScraping,
    processGitHubAnalysis,
    downloadPDF,
    resetData
  } = dataHook;

  // GitHub state
  const [repoUrl, setRepoUrl] = useState('');
  const [repoData, setRepoData] = useState(null);

  // History state
  const [showHistory, setShowHistory] = useState(false);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);

  // Handle GitHub analysis with URL tracking
  const handleGitHubAnalysis = async (url) => {
    setRepoUrl(url);
    const result = await processGitHubAnalysis(url);
    if (result && result.repoData) {
      setRepoData(result.repoData);
    }
  };

  // Reset all data and return to input screen
  const handleReset = () => {
    resetData();
    setRepoUrl('');
    setRepoData(null);
    clearApiStatus();
    setShowHistory(false);
    setSelectedHistoryItem(null);
  };

  // Toggle history view
  const handleToggleHistory = () => {
    setShowHistory(prev => !prev);
    if (selectedHistoryItem) {
      setSelectedHistoryItem(null);
    }
  };

  // Handle selecting an analysis from history
  const handleSelectAnalysis = (analysis) => {
    setSelectedHistoryItem(analysis);
    // Load the analysis data
    if (analysis && analysis.summary) {
      // Set the analyzed reviews from the history item if available
      // For now, we'll just set the summary and use the existing setActiveView
      resetData();
      // We don't have direct access to setSummary, so we'll need to
      // implement a different approach to load the summary
      // For now, we'll just use the summary from the history item
      // and set it in the state
      setActiveView('summary');
      setShowHistory(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          {/* Header with navigation buttons */}
          <Header
            hasData={analyzedReviews.length > 0}
            activeView={activeView}
            setActiveView={setActiveView}
            hasSummary={summary !== null}
            onDownloadPDF={downloadPDF}
            onReset={handleReset}
            onShowHistory={handleToggleHistory}
            loading={loading}
          />

          {/* Processing Steps - Show when loading */}
          <AnimatePresence>
            {loading && (
              <motion.div
                className="mb-8"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
              >
                <div className="card">
                  <h2 className="text-xl font-semibold text-gray-800 mb-4">Processing Your Data</h2>
                  <div className="flex justify-center mb-4">
                    <LoadingIndicator type="beat" size={30} text="Processing..." />
                  </div>
                  <ProcessingSteps
                    steps={processingSteps}
                    currentStep={processingStep}
                    apiStatus={apiStatus}
                    onClearApiStatus={clearApiStatus}
                  />
                  {estimatedTime && (
                    <p className="text-sm text-gray-600 mt-4 text-center">
                      Estimated time remaining: ~{Math.round(estimatedTime)} seconds
                    </p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Data Input Section - Only show if no data or explicitly in input mode */}
          {analyzedReviews.length === 0 && !loading && (
            <DataInputTabs
              onFileUpload={processFileUpload}
              onScrape={processScraping}
              onGitHubAnalysis={handleGitHubAnalysis}
              loading={loading}
              uploadProgress={uploadProgress}
            />
          )}

          {/* Error Message */}
          <ErrorMessage error={error} />

          {/* API Status Indicator - Show when not in processing view but API has errors */}
          {!loading && (
            <div className="mt-4">
              {/* Show Gemini status indicator */}
              <GeminiStatusIndicator className="mb-4" />

              {/* Show API error indicators */}
              {apiStatus && apiStatus.error && (
                apiStatus.error.includes('quota') ? (
                  <APIQuotaDisplay apiStatus={apiStatus} />
                ) : (
                  <APIStatusIndicator
                    apiStatus={apiStatus}
                    onClose={clearApiStatus}
                    showDetails={true}
                  />
                )
              )}
            </div>
          )}

          {/* Reviews View */}
          <AnimatePresence>
            {analyzedReviews.length > 0 && activeView === 'reviews' && (
              <motion.div
                className="mt-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Analyzed Reviews</h2>
                <ReviewsTable reviews={analyzedReviews} />
              </motion.div>
            )}
          </AnimatePresence>

          {/* GitHub Repository Details - Show when GitHub data is available */}
          <GitHubDetails repoData={repoData} repoUrl={repoUrl} />

          {/* Summary View */}
          <AnimatePresence>
            {summary && activeView === 'summary' && (
              <SummaryView summary={summary} onDownloadPDF={downloadPDF} />
            )}
          </AnimatePresence>

          {/* History View */}
          <AnimatePresence>
            {showHistory && (
              <motion.div
                className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.3 }}
              >
                <HistoryView
                  onSelectAnalysis={handleSelectAnalysis}
                  onClose={handleToggleHistory}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}

export default App;