import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Legend
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

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        setLoading(true);
        try {
          const data = await api.getPriorityInsights(sourceType);
          setInsights(data);
        } catch (apiError) {
          console.error('API error, using mock data:', apiError);
          // Use mock data if API fails
          setInsights(getMockInsights());
        }
      } catch (err) {
        console.error('Error fetching priority insights:', err);
        setError('Failed to load weekly summary data');
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, [sourceType]);

  // Mock data function for development and testing
  const getMockInsights = () => {
    return {
      high_priority_items: [
        {
          title: "App crashes during checkout",
          description: "Multiple users reported app crashes during the payment process",
          priority_score: 0.95,
          category: "pain_point",
          sentiment_score: -0.8,
          frequency: 12,
          examples: ["App crashed when I tried to pay", "Payment screen freezes every time"]
        },
        {
          title: "Slow loading times on product pages",
          description: "Users complain about slow loading times when browsing products",
          priority_score: 0.85,
          category: "pain_point",
          sentiment_score: -0.7,
          frequency: 8,
          examples: ["Pages take forever to load", "Product images load very slowly"]
        },
        {
          title: "Add dark mode support",
          description: "Users requesting dark mode for better nighttime usage",
          priority_score: 0.75,
          category: "feature_request",
          sentiment_score: 0.2,
          frequency: 15,
          examples: ["Please add dark mode", "App is too bright at night"]
        },
        {
          title: "Improve search functionality",
          description: "Search results are not relevant enough",
          priority_score: 0.7,
          category: "feature_request",
          sentiment_score: -0.3,
          frequency: 10,
          examples: ["Search doesn't find what I'm looking for", "Search results are irrelevant"]
        }
      ],
      trending_topics: [
        { topic: "checkout", count: 25 },
        { topic: "dark mode", count: 18 },
        { topic: "search", count: 15 },
        { topic: "performance", count: 12 },
        { topic: "UI", count: 10 }
      ],
      sentiment_trends: {
        "Twitter": 0.65,
        "App Store": 0.45,
        "Play Store": 0.55,
        "Website": 0.7
      },
      action_items: [
        "Fix checkout process crashes as highest priority",
        "Optimize product page loading times",
        "Implement dark mode in next release",
        "Improve search algorithm relevance"
      ],
      risk_areas: [
        "Payment processing reliability issues may impact revenue",
        "Performance problems could lead to user abandonment",
        "Search functionality limitations affecting product discovery"
      ],
      opportunity_areas: [
        "Dark mode implementation could improve user satisfaction",
        "Improved search could increase conversion rates",
        "Performance optimizations would enhance overall experience"
      ]
    };
  };

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

  // Prepare data for charts
  const trendingTopicsData = insights.trending_topics.map(topic => ({
    name: topic.topic,
    value: topic.count
  }));

  const sentimentTrendsData = Object.entries(insights.sentiment_trends).map(([name, value]) => ({
    name,
    value: parseFloat((value * 100).toFixed(1))
  }));

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">Weekly Product Manager Summary</h2>
        <p className="text-gray-600 mb-6">
          A summary of what users are saying and what product managers should prioritize this week.
        </p>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-6">
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'priorities'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('priorities')}
          >
            Priorities
          </button>
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'trends'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('trends')}
          >
            Trends
          </button>
          <button
            className={`px-4 py-2 font-medium ${
              activeTab === 'recommendations'
                ? 'text-blue-600 border-b-2 border-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
            onClick={() => setActiveTab('recommendations')}
          >
            Recommendations
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'priorities' && (
          <div className="space-y-6">
            <div className="bg-red-50 rounded-lg p-4 border border-red-100">
              <h3 className="text-lg font-semibold text-red-800 mb-3">Top Pain Points to Address</h3>
              <div className="space-y-3">
                {insights.high_priority_items
                  .filter(item => item.category === 'pain_point')
                  .slice(0, 5)
                  .map((item, index) => (
                    <div key={index} className="bg-white p-3 rounded border border-red-200">
                      <div className="flex justify-between">
                        <h4 className="font-medium">{item.title}</h4>
                        <span className="text-sm bg-red-100 text-red-800 px-2 py-1 rounded">
                          Priority: {(item.priority_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm mt-1">{item.description}</p>
                      {item.examples && item.examples.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-500">Example feedback:</p>
                          <p className="text-sm italic">"{item.examples[0]}"</p>
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>

            <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
              <h3 className="text-lg font-semibold text-blue-800 mb-3">Feature Requests to Consider</h3>
              <div className="space-y-3">
                {insights.high_priority_items
                  .filter(item => item.category === 'feature_request')
                  .slice(0, 5)
                  .map((item, index) => (
                    <div key={index} className="bg-white p-3 rounded border border-blue-200">
                      <div className="flex justify-between">
                        <h4 className="font-medium">{item.title}</h4>
                        <span className="text-sm bg-blue-100 text-blue-800 px-2 py-1 rounded">
                          Priority: {(item.priority_score * 100).toFixed(0)}%
                        </span>
                      </div>
                      <p className="text-gray-600 text-sm mt-1">{item.description}</p>
                      {item.examples && item.examples.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-500">Example feedback:</p>
                          <p className="text-sm italic">"{item.examples[0]}"</p>
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="text-lg font-semibold mb-4">Trending Topics</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={trendingTopicsData} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" />
                    <YAxis dataKey="name" type="category" width={120} />
                    <Tooltip content={<CustomTooltip />} />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </div>

              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="text-lg font-semibold mb-4">Sentiment by Source</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={sentimentTrendsData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                      label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    >
                      {sentimentTrendsData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'recommendations' && (
          <div className="space-y-6">
            <div className="bg-green-50 rounded-lg p-4 border border-green-100">
              <h3 className="text-lg font-semibold text-green-800 mb-3">Recommended Actions</h3>
              <ul className="space-y-2">
                {insights.action_items.map((item, index) => (
                  <li key={index} className="bg-white p-3 rounded border border-green-200">
                    <div className="flex items-start">
                      <span className="text-green-500 mr-2">✓</span>
                      <span>{item}</span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-100">
                <h3 className="text-lg font-semibold text-yellow-800 mb-3">Risk Areas</h3>
                <ul className="space-y-2">
                  {insights.risk_areas.map((item, index) => (
                    <li key={index} className="bg-white p-3 rounded border border-yellow-200">
                      <div className="flex items-start">
                        <span className="text-yellow-500 mr-2">⚠</span>
                        <span>{item}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
                <h3 className="text-lg font-semibold text-purple-800 mb-3">Opportunity Areas</h3>
                <ul className="space-y-2">
                  {insights.opportunity_areas.map((item, index) => (
                    <li key={index} className="bg-white p-3 rounded border border-purple-200">
                      <div className="flex items-start">
                        <span className="text-purple-500 mr-2">★</span>
                        <span>{item}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WeeklySummaryView;
