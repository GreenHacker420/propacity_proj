import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend, LineChart, Line
} from 'recharts';
import api from '../services/api';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#FF6B6B'];

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white p-3 rounded-lg shadow-lg border border-gray-200">
        <p className="font-semibold">{label}</p>
        <p className="text-blue-600">{`Value: ${payload[0].value}`}</p>
      </div>
    );
  }
  return null;
};

/**
 * Component for displaying the weekly summary of user feedback for product managers
 */
const WeeklySummaryView = ({ sourceType = null }) => {
  const [insights, setInsights] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('priorities');
  const [timeRange, setTimeRange] = useState('week');

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        const data = await api.getPriorityInsights(sourceType, timeRange);
        setInsights(data);
      } catch (err) {
        console.error('Error fetching priority insights:', err);
        setError('Failed to load weekly summary data. Please try analyzing some data first.');
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, [sourceType, timeRange]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-800 rounded-lg p-4 mt-4">
        <p className="font-medium">{error}</p>
      </div>
    );
  }

  if (!insights) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 rounded-lg p-4 mt-4">
        <p className="font-medium">No weekly summary data available. Try analyzing some reviews first.</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Time Range Filter */}
      <div className="flex justify-between items-center mb-6">
        <div className="flex space-x-4">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value)}
            className="px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="week">Last Week</option>
            <option value="month">Last Month</option>
            <option value="quarter">Last Quarter</option>
            <option value="year">Last Year</option>
          </select>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-6">
        {['priorities', 'trends', 'action_items', 'opportunities'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg transition-all duration-200 ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            {tab.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
          </button>
        ))}
      </div>

      {/* Priorities Tab */}
      {activeTab === 'priorities' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-6">High Priority Items</h3>
            <div className="space-y-4">
              {insights.high_priority_items.map((item, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-medium text-gray-900">{item.title}</h4>
                      <p className="text-gray-600 mt-1">{item.description}</p>
                      <div className="mt-2 flex items-center space-x-4">
                        <span className="text-sm text-gray-500">
                          Priority Score: {item.priority_score.toFixed(2)}
                        </span>
                        <span className="text-sm text-gray-500">
                          Category: {item.category}
                        </span>
                      </div>
                      {item.examples && item.examples.length > 0 && (
                        <div className="mt-2">
                          <p className="text-sm text-gray-500 font-medium">Examples:</p>
                          <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                            {item.examples.map((example, i) => (
                              <li key={i}>{example}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                    <div className="flex flex-col items-end">
                      <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                        Sentiment: {item.sentiment_score.toFixed(2)}
                      </span>
                      <span className="mt-2 text-sm text-gray-500">
                        Frequency: {item.frequency}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Trends Tab */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-6">Trending Topics</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={insights.trending_topics}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="volume" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-6">Sentiment Trends</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={Object.entries(insights.sentiment_trends).map(([category, score]) => ({ 
                category: category.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '), 
                score 
              }))}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="category" />
                <YAxis domain={[0, 1]} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="score" fill="#8884d8" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* Action Items Tab */}
      {activeTab === 'action_items' && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h3 className="text-xl font-semibold mb-6">Action Items</h3>
          <div className="space-y-4">
            {insights.action_items.map((item, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <p className="text-gray-800">{item}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Opportunities Tab */}
      {activeTab === 'opportunities' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-6">Opportunity Areas</h3>
            <div className="space-y-4">
              {insights.opportunity_areas.map((item, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-gray-800">{item}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-xl font-semibold mb-6">Risk Areas</h3>
            <div className="space-y-4">
              {insights.risk_areas.map((item, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-gray-800">{item}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default WeeklySummaryView;
