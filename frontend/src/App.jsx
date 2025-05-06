import React, { useState, useEffect } from 'react'
import { Tab } from '@headlessui/react'
import {
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ChartPieIcon,
  ExclamationCircleIcon
} from '@heroicons/react/24/outline'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'

// Import custom components
import LoadingIndicator from './components/LoadingIndicator'
import ProgressBar from './components/ProgressBar'
import FileDropzone from './components/FileDropzone'
import ProcessingSteps from './components/ProcessingSteps'
import GitHubRepoInput from './components/GitHubRepoInput'
import CodeBlock from './components/CodeBlock'

// Configure axios base URL to match the backend server port
axios.defaults.baseURL = 'http://localhost:8000';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ')
}

function App() {
  // Tab state
  const [selectedTab, setSelectedTab] = useState(0)

  // File upload state
  const [file, setFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)

  // Scraping state
  const [scrapeSource, setScrapeSource] = useState('twitter')
  const [scrapeQuery, setScrapeQuery] = useState('')
  const [scrapeLimit, setScrapeLimit] = useState(50)

  // GitHub state
  const [repoUrl, setRepoUrl] = useState('')
  const [repoData, setRepoData] = useState(null)

  // Data state
  const [analyzedReviews, setAnalyzedReviews] = useState([])
  const [summary, setSummary] = useState(null)

  // Processing state
  const [processingStep, setProcessingStep] = useState(0)
  const [estimatedTime, setEstimatedTime] = useState(null)

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeView, setActiveView] = useState('reviews') // 'reviews' or 'summary'

  // Processing steps
  const processingSteps = [
    {
      label: 'Uploading data',
      description: 'Transferring your data to our servers',
      estimatedTime: '10-20 seconds'
    },
    {
      label: 'Analyzing sentiment',
      description: 'Determining positive and negative feedback',
      estimatedTime: '30-45 seconds'
    },
    {
      label: 'Categorizing feedback',
      description: 'Identifying pain points, feature requests, and positive feedback',
      estimatedTime: '20-30 seconds'
    },
    {
      label: 'Extracting insights',
      description: 'Generating actionable recommendations',
      estimatedTime: '15-25 seconds'
    },
    {
      label: 'Creating summary',
      description: 'Preparing your feedback dashboard',
      estimatedTime: '5-10 seconds'
    }
  ]

  // Calculate estimated total time
  useEffect(() => {
    if (loading && processingStep < processingSteps.length) {
      const currentStepTime = processingSteps[processingStep].estimatedTime;
      const timeRange = currentStepTime.split('-');
      const avgTime = (parseInt(timeRange[0]) + parseInt(timeRange[1].split(' ')[0])) / 2;
      setEstimatedTime(avgTime);
    }
  }, [loading, processingStep]);

  const handleFileSelected = (selectedFile) => {
    setFile(selectedFile)
  }

  const handleFileUpload = async () => {
    if (!file) return

    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      setError(null)
      setProcessingStep(0) // Start at the first step

      // Simulate upload progress
      const uploadInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 95) {
            clearInterval(uploadInterval)
            return prev
          }
          return prev + 5
        })
      }, 300)

      // Upload and analyze the file
      console.log('Sending upload request to:', axios.defaults.baseURL + '/api/upload')
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      // Clear upload interval and set progress to 100%
      clearInterval(uploadInterval)
      setUploadProgress(100)

      // Move to sentiment analysis step
      setProcessingStep(1)

      // Simulate processing time for sentiment analysis
      await new Promise(resolve => setTimeout(resolve, 2000))
      setProcessingStep(2)

      // Simulate processing time for categorization
      await new Promise(resolve => setTimeout(resolve, 1500))
      setProcessingStep(3)

      // Simulate processing time for insights extraction
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Store the analyzed reviews
      setAnalyzedReviews(response.data)

      // Move to summary creation step
      setProcessingStep(4)

      // Generate summary from the analyzed reviews
      await generateSummary(response.data)

      // Switch to the summary view
      setActiveView('summary')
    } catch (err) {
      console.error('Upload error:', err)
      if (err.response?.status === 400 && err.response?.data?.detail?.includes("'text' column")) {
        setError("CSV file must contain a 'text' column. Please check your file format.")
      } else {
        setError(err.response?.data?.detail || 'Error uploading file')
      }
    } finally {
      setLoading(false)
      setUploadProgress(0)
      setProcessingStep(0)
    }
  }

  const handleScrape = async () => {
    try {
      setLoading(true)
      setError(null)
      setProcessingStep(0) // Start at the first step

      // Prepare parameters based on the selected source
      const params = {
        source: scrapeSource,
        limit: scrapeLimit
      }

      // Add query or app_id based on the source
      if (scrapeSource === 'twitter') {
        params.query = scrapeQuery
      } else if (scrapeSource === 'playstore') {
        params.app_id = scrapeQuery
      }

      // Simulate data collection progress
      const scrapeInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 95) {
            clearInterval(scrapeInterval)
            return prev
          }
          return prev + 3
        })
      }, 200)

      // Scrape and analyze the data
      const response = await axios.get('/api/scrape', { params })

      // Clear interval and set progress to 100%
      clearInterval(scrapeInterval)
      setUploadProgress(100)

      // Move to sentiment analysis step
      setProcessingStep(1)

      // Simulate processing time for sentiment analysis
      await new Promise(resolve => setTimeout(resolve, 2000))
      setProcessingStep(2)

      // Simulate processing time for categorization
      await new Promise(resolve => setTimeout(resolve, 1500))
      setProcessingStep(3)

      // Simulate processing time for insights extraction
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Store the analyzed reviews
      setAnalyzedReviews(response.data)

      // Move to summary creation step
      setProcessingStep(4)

      // Generate summary from the analyzed reviews
      await generateSummary(response.data)

      // Switch to the summary view
      setActiveView('summary')
    } catch (err) {
      console.error('Scrape error:', err)
      setError(err.response?.data?.detail || 'Error scraping data')
    } finally {
      setLoading(false)
      setUploadProgress(0)
      setProcessingStep(0)
    }
  }

  const handleGitHubAnalysis = async (url) => {
    try {
      setLoading(true)
      setError(null)
      setProcessingStep(0) // Start at the first step
      setRepoUrl(url)

      // Simulate data collection progress
      const fetchInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 95) {
            clearInterval(fetchInterval)
            return prev
          }
          return prev + 2
        })
      }, 150)

      // In a real implementation, we would call the backend API to analyze the GitHub repo
      // For now, we'll simulate the API call with a timeout
      await new Promise(resolve => setTimeout(resolve, 3000))

      // Clear interval and set progress to 100%
      clearInterval(fetchInterval)
      setUploadProgress(100)

      // Move to sentiment analysis step
      setProcessingStep(1)

      // Simulate processing time for sentiment analysis
      await new Promise(resolve => setTimeout(resolve, 2000))
      setProcessingStep(2)

      // Simulate processing time for categorization
      await new Promise(resolve => setTimeout(resolve, 1500))
      setProcessingStep(3)

      // Simulate processing time for insights extraction
      await new Promise(resolve => setTimeout(resolve, 1500))

      // Create mock data for GitHub analysis
      const mockGitHubData = {
        issues: [
          { id: 1, title: "App crashes when uploading large files", body: "When I try to upload files larger than 10MB, the app crashes without any error message.", labels: ["bug", "high-priority"] },
          { id: 2, title: "Add dark mode support", body: "It would be great to have a dark mode option for the UI.", labels: ["enhancement", "ui"] },
          { id: 3, title: "Search functionality not working properly", body: "The search doesn't return results for partial matches.", labels: ["bug"] }
        ],
        discussions: [
          { id: 1, title: "Roadmap for v2.0", body: "Let's discuss the features we want to include in version 2.0" },
          { id: 2, title: "Performance improvements", body: "We should focus on improving load times for the dashboard" }
        ]
      };

      setRepoData(mockGitHubData);

      // Create mock analyzed reviews from GitHub data
      const mockAnalyzedReviews = mockGitHubData.issues.map(issue => ({
        text: issue.body,
        sentiment_label: issue.labels.includes("bug") ? "NEGATIVE" : "POSITIVE",
        sentiment_score: issue.labels.includes("bug") ? 0.2 : 0.8,
        category: issue.labels.includes("bug") ? "pain_point" :
                 issue.labels.includes("enhancement") ? "feature_request" : "positive_feedback",
        keywords: issue.labels,
        source: "github",
        issue_title: issue.title
      }));

      // Store the analyzed reviews
      setAnalyzedReviews(mockAnalyzedReviews);

      // Move to summary creation step
      setProcessingStep(4);

      // Generate summary from the analyzed reviews
      await generateSummary(mockAnalyzedReviews);

      // Switch to the summary view
      setActiveView('summary');
    } catch (err) {
      console.error('GitHub analysis error:', err);
      setError('Error analyzing GitHub repository');
    } finally {
      setLoading(false);
      setUploadProgress(0);
      setProcessingStep(0);
    }
  };

  const generateSummary = async (reviewsData) => {
    try {
      // Send the analyzed reviews to get a summary
      const response = await axios.post('/api/summary', reviewsData)
      setSummary(response.data)
    } catch (err) {
      console.error('Summary error:', err)
      setError(err.response?.data?.detail || 'Error generating summary')
    }
  }

  const downloadPDF = async () => {
    try {
      setLoading(true)

      // Send the analyzed reviews to generate a PDF
      const response = await axios.post('/api/summary/pdf', analyzedReviews, {
        responseType: 'blob'
      })

      // Create a download link for the PDF
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `product_review_summary_${new Date().toISOString().split('T')[0]}.pdf`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err) {
      console.error('PDF error:', err)
      setError(err.response?.data?.detail || 'Error downloading PDF')
    } finally {
      setLoading(false)
    }
  }

  // This function is now used directly in the onClick handlers

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <motion.header
            className="flex justify-between items-center mb-8"
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <h1 className="text-3xl font-bold text-gray-900">Product Review Analyzer</h1>

            {analyzedReviews.length > 0 && (
              <motion.div
                className="flex space-x-2"
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3 }}
              >
                <button
                  className={`btn ${activeView === 'reviews' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setActiveView('reviews')}
                >
                  <DocumentTextIcon className="w-5 h-5 inline-block mr-2" />
                  Reviews
                </button>
                <button
                  className={`btn ${activeView === 'summary' ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => setActiveView('summary')}
                >
                  <ChartPieIcon className="w-5 h-5 inline-block mr-2" />
                  Summary
                </button>
                {summary && (
                  <button
                    className="btn btn-primary"
                    onClick={downloadPDF}
                    disabled={loading}
                  >
                    {loading ? 'Generating...' : 'Download PDF'}
                  </button>
                )}
              </motion.div>
            )}
          </motion.header>

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
                  <ProcessingSteps steps={processingSteps} currentStep={processingStep} />
                  {estimatedTime && (
                    <p className="text-sm text-gray-600 mt-4 text-center">
                      Estimated time remaining: ~{estimatedTime} seconds
                    </p>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Data Input Section - Only show if no data or explicitly in input mode */}
          {analyzedReviews.length === 0 && !loading && (
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

                <Tab.Panel>
                  <motion.div
                    className="card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <h2 className="text-lg font-medium text-gray-800 mb-4">Analyze GitHub Repository</h2>
                    <GitHubRepoInput onSubmit={handleGitHubAnalysis} isLoading={loading} />
                  </motion.div>
                </Tab.Panel>
              </Tab.Panels>
            </Tab.Group>
          )}

          {/* Error Message */}
          <AnimatePresence>
            {error && (
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
            )}
          </AnimatePresence>

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
                <div className="overflow-x-auto">
                  <table className="min-w-full bg-white rounded-lg overflow-hidden shadow">
                    <thead className="bg-gray-100">
                      <tr>
                        {analyzedReviews[0].source === 'github' && (
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue</th>
                        )}
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Text</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Sentiment</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Keywords</th>
                        {analyzedReviews.some(r => r.rating) && (
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Rating</th>
                        )}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {analyzedReviews.map((review, index) => (
                        <motion.tr
                          key={index}
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ duration: 0.3, delay: index * 0.05 }}
                        >
                          {review.source === 'github' && (
                            <td className="px-6 py-4 whitespace-normal text-sm font-medium text-primary-600">
                              {review.issue_title}
                            </td>
                          )}
                          <td className="px-6 py-4 whitespace-normal text-sm text-gray-900">{review.text}</td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              review.sentiment_label === 'POSITIVE'
                                ? 'bg-green-100 text-green-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {review.sentiment_label} ({review.sentiment_score.toFixed(2)})
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              review.category === 'pain_point'
                                ? 'bg-red-100 text-red-800'
                                : review.category === 'feature_request'
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-green-100 text-green-800'
                            }`}>
                              {review.category.replace('_', ' ')}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-normal text-sm text-gray-500">
                            {Array.isArray(review.keywords) ? review.keywords.join(', ') : review.keywords}
                          </td>
                          {analyzedReviews.some(r => r.rating) && (
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {review.rating ? review.rating : '-'}
                            </td>
                          )}
                        </motion.tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* GitHub Repository Details - Show when GitHub data is available */}
          <AnimatePresence>
            {repoData && (
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
            )}
          </AnimatePresence>

          {/* Summary View */}
          <AnimatePresence>
            {summary && activeView === 'summary' && (
              <motion.div
                className="mt-8"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.5 }}
              >
                <h2 className="text-2xl font-bold text-gray-900 mb-6">Feedback Analysis Summary</h2>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <motion.div
                    className="card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3 }}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Pain Points</h3>
                    <div className="space-y-4">
                      {summary.pain_points.length > 0 ? (
                        summary.pain_points.map((item, index) => (
                          <motion.div
                            key={index}
                            className="p-4 bg-red-50 rounded-md"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.3, delay: index * 0.1 }}
                          >
                            <p className="text-sm text-gray-700">{item.text}</p>
                            <div className="mt-2 flex justify-between text-xs text-gray-500">
                              <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                              <span>Keywords: {item.keywords.join(', ')}</span>
                            </div>
                          </motion.div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500 italic">No pain points identified</p>
                      )}
                    </div>
                  </motion.div>

                  <motion.div
                    className="card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.1 }}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Feature Requests</h3>
                    <div className="space-y-4">
                      {summary.feature_requests.length > 0 ? (
                        summary.feature_requests.map((item, index) => (
                          <motion.div
                            key={index}
                            className="p-4 bg-blue-50 rounded-md"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.3, delay: index * 0.1 }}
                          >
                            <p className="text-sm text-gray-700">{item.text}</p>
                            <div className="mt-2 flex justify-between text-xs text-gray-500">
                              <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                              <span>Keywords: {item.keywords.join(', ')}</span>
                            </div>
                          </motion.div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500 italic">No feature requests identified</p>
                      )}
                    </div>
                  </motion.div>

                  <motion.div
                    className="card"
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.3, delay: 0.2 }}
                  >
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Positive Highlights</h3>
                    <div className="space-y-4">
                      {summary.positive_feedback.length > 0 ? (
                        summary.positive_feedback.map((item, index) => (
                          <motion.div
                            key={index}
                            className="p-4 bg-green-50 rounded-md"
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ duration: 0.3, delay: index * 0.1 }}
                          >
                            <p className="text-sm text-gray-700">{item.text}</p>
                            <div className="mt-2 flex justify-between text-xs text-gray-500">
                              <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                              <span>Keywords: {item.keywords.join(', ')}</span>
                            </div>
                          </motion.div>
                        ))
                      ) : (
                        <p className="text-sm text-gray-500 italic">No positive feedback identified</p>
                      )}
                    </div>
                  </motion.div>
                </div>

                <motion.div
                  className="mt-6"
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.3, delay: 0.3 }}
                >
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Suggested PM Priorities</h3>
                  <div className="card">
                    <ul className="space-y-3">
                      {summary.suggested_priorities.map((priority, index) => (
                        <motion.li
                          key={index}
                          className="flex items-start"
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ duration: 0.3, delay: 0.3 + index * 0.1 }}
                        >
                          <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                            {index + 1}
                          </span>
                          <span className="ml-3 text-gray-700">{priority}</span>
                        </motion.li>
                      ))}
                    </ul>
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  )
}

export default App