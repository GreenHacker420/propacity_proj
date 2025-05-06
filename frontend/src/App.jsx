import React, { useState } from 'react'
import { Tab } from '@headlessui/react'
import {
  ArrowUpTrayIcon,
  MagnifyingGlassIcon,
  DocumentTextIcon,
  ChartPieIcon
} from '@heroicons/react/24/outline'
import axios from 'axios'

// Configure axios base URL
axios.defaults.baseURL = 'http://localhost:8080';

function classNames(...classes) {
  return classes.filter(Boolean).join(' ')
}

function App() {
  // Tab state
  const [selectedTab, setSelectedTab] = useState(0)

  // File upload state
  const [file, setFile] = useState(null)

  // Scraping state
  const [scrapeSource, setScrapeSource] = useState('twitter')
  const [scrapeQuery, setScrapeQuery] = useState('')
  const [scrapeLimit, setScrapeLimit] = useState(50)

  // Data state
  const [reviews, setReviews] = useState([])
  const [analyzedReviews, setAnalyzedReviews] = useState([])
  const [summary, setSummary] = useState(null)

  // UI state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [activeView, setActiveView] = useState('reviews') // 'reviews' or 'summary'

  const handleFileUpload = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    setFile(file)
    const formData = new FormData()
    formData.append('file', file)

    try {
      setLoading(true)
      setError(null)

      // Upload and analyze the file
      console.log('Sending upload request to:', axios.defaults.baseURL + '/api/upload')
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      // Store the analyzed reviews
      setAnalyzedReviews(response.data)

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
    }
  }

  const handleScrape = async () => {
    try {
      setLoading(true)
      setError(null)

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

      // Scrape and analyze the data
      const response = await axios.get('/api/scrape', { params })

      // Store the analyzed reviews
      setAnalyzedReviews(response.data)

      // Generate summary from the analyzed reviews
      await generateSummary(response.data)

      // Switch to the summary view
      setActiveView('summary')
    } catch (err) {
      console.error('Scrape error:', err)
      setError(err.response?.data?.detail || 'Error scraping data')
    } finally {
      setLoading(false)
    }
  }

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

  // Toggle between reviews and summary views
  const toggleView = () => {
    setActiveView(activeView === 'reviews' ? 'summary' : 'reviews')
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div className="px-4 py-6 sm:px-0">
          <header className="flex justify-between items-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Product Review Analyzer</h1>

            {analyzedReviews.length > 0 && (
              <div className="flex space-x-2">
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
              </div>
            )}
          </header>

          {/* Data Input Section - Only show if no data or explicitly in input mode */}
          {analyzedReviews.length === 0 && (
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
                <Tab.Panel>
                  <div className="card">
                    <div className="flex items-center justify-center w-full">
                      <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-gray-300 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
                        <div className="flex flex-col items-center justify-center pt-5 pb-6">
                          <ArrowUpTrayIcon className="w-8 h-8 mb-4 text-gray-500" />
                          <p className="mb-2 text-sm text-gray-500">
                            <span className="font-semibold">Click to upload</span> or drag and drop
                          </p>
                          <p className="text-xs text-gray-500">CSV files only</p>
                          <p className="text-xs text-gray-400 mt-2">Must contain 'text' column. Optional: username, timestamp, rating</p>
                        </div>
                        <input
                          type="file"
                          className="hidden"
                          accept=".csv"
                          onChange={handleFileUpload}
                          disabled={loading}
                        />
                      </label>
                    </div>
                  </div>
                </Tab.Panel>

                <Tab.Panel>
                  <div className="card">
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
                        {loading ? 'Loading...' : 'Scrape Data'}
                      </button>
                    </div>
                  </div>
                </Tab.Panel>
              </Tab.Panels>
            </Tab.Group>
          )}

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 text-red-700 rounded-md">
              {error}
            </div>
          )}

          {/* Reviews View */}
          {analyzedReviews.length > 0 && activeView === 'reviews' && (
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Analyzed Reviews</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full bg-white rounded-lg overflow-hidden shadow">
                  <thead className="bg-gray-100">
                    <tr>
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
                      <tr key={index}>
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
                          {review.keywords.join(', ')}
                        </td>
                        {analyzedReviews.some(r => r.rating) && (
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {review.rating ? review.rating : '-'}
                          </td>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Summary View */}
          {summary && activeView === 'summary' && (
            <div className="mt-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Weekly Review Summary</h2>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Pain Points</h3>
                  <div className="space-y-4">
                    {summary.pain_points.length > 0 ? (
                      summary.pain_points.map((item, index) => (
                        <div key={index} className="p-4 bg-red-50 rounded-md">
                          <p className="text-sm text-gray-700">{item.text}</p>
                          <div className="mt-2 flex justify-between text-xs text-gray-500">
                            <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                            <span>Keywords: {item.keywords.join(', ')}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500 italic">No pain points identified</p>
                    )}
                  </div>
                </div>

                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Top Feature Requests</h3>
                  <div className="space-y-4">
                    {summary.feature_requests.length > 0 ? (
                      summary.feature_requests.map((item, index) => (
                        <div key={index} className="p-4 bg-blue-50 rounded-md">
                          <p className="text-sm text-gray-700">{item.text}</p>
                          <div className="mt-2 flex justify-between text-xs text-gray-500">
                            <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                            <span>Keywords: {item.keywords.join(', ')}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500 italic">No feature requests identified</p>
                    )}
                  </div>
                </div>

                <div className="card">
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Positive Highlights</h3>
                  <div className="space-y-4">
                    {summary.positive_feedback.length > 0 ? (
                      summary.positive_feedback.map((item, index) => (
                        <div key={index} className="p-4 bg-green-50 rounded-md">
                          <p className="text-sm text-gray-700">{item.text}</p>
                          <div className="mt-2 flex justify-between text-xs text-gray-500">
                            <span>Sentiment: {item.sentiment_score.toFixed(2)}</span>
                            <span>Keywords: {item.keywords.join(', ')}</span>
                          </div>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500 italic">No positive feedback identified</p>
                    )}
                  </div>
                </div>
              </div>

              <div className="mt-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Suggested PM Priorities</h3>
                <div className="card">
                  <ul className="space-y-3">
                    {summary.suggested_priorities.map((priority, index) => (
                      <li key={index} className="flex items-start">
                        <span className="flex-shrink-0 h-6 w-6 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold">
                          {index + 1}
                        </span>
                        <span className="ml-3 text-gray-700">{priority}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default App