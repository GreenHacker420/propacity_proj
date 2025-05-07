import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer
} from 'recharts';
import { motion, AnimatePresence } from 'framer-motion';
import { useInView } from 'react-intersection-observer';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#FF6B6B', '#4ECDC4', '#45B7D1'];

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

const AnimatedNumber = ({ value, prefix = '', suffix = '', duration = 1 }) => {
  const [displayValue, setDisplayValue] = useState(0);
  const [ref, inView] = useInView({
    triggerOnce: true,
    threshold: 0.1,
  });

  useEffect(() => {
    if (inView) {
      let start = 0;
      const end = value;
      const increment = end / (duration * 60);
      const timer = setInterval(() => {
        start += increment;
        if (start >= end) {
          setDisplayValue(end);
          clearInterval(timer);
        } else {
          setDisplayValue(Math.floor(start));
        }
      }, 1000 / 60);
      return () => clearInterval(timer);
    }
  }, [inView, value, duration]);

  return (
    <span ref={ref}>
      {prefix}{displayValue.toLocaleString()}{suffix}
    </span>
  );
};

const DataVisualization = ({ data }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [chartData, setChartData] = useState(null);

  useEffect(() => {
    if (data) {
      try {
        // Handle the case where data is the summary itself or contains a summary property
        const summary = data.summary || data;

        if (!summary) {
          console.error('Summary data is missing');
          // Instead of returning, set default empty data
          setChartData({
            sentimentData: [],
            classificationData: [],
            gameData: [],
            keywordData: [],
            summary: {
              total_reviews: 0,
              average_sentiment: 0,
              sentiment_distribution: {},
              classification_distribution: {},
              game_distribution: {},
              top_keywords: {}
            }
          });
          return;
        }

        // Log the summary structure to help with debugging
        console.log('Summary structure:', Object.keys(summary));

        // Safely access properties with fallbacks
        // Handle both normal summary structure and fallback structure from local processing
        const sentimentDistribution = summary.sentiment_distribution || {};
        const classificationDistribution = summary.classification_distribution || {};
        const gameDistribution = summary.game_distribution || {};
        const topKeywords = summary.top_keywords || {};

        // If we're in fallback mode, we might have a different structure
        // Check if we have the expected properties, if not, create default values
        if (Object.keys(sentimentDistribution).length === 0 &&
            summary.pain_points && summary.feature_requests && summary.positive_aspects) {
          // We're likely in fallback mode with a different data structure
          console.log('Using fallback data structure for visualization');

          // Create sentiment distribution from pain points and positive aspects
          const painPointCount = Array.isArray(summary.pain_points) ? summary.pain_points.length : 0;
          const featureRequestCount = Array.isArray(summary.feature_requests) ? summary.feature_requests.length : 0;
          const positiveCount = Array.isArray(summary.positive_aspects) ? summary.positive_aspects.length : 0;

          // Create synthetic distributions for visualization
          Object.assign(sentimentDistribution, {
            negative: painPointCount,
            neutral: featureRequestCount,
            positive: positiveCount
          });

          // Create classification distribution
          Object.assign(classificationDistribution, {
            pain_point: painPointCount,
            feature_request: featureRequestCount,
            positive_feedback: positiveCount
          });

          // Create keyword distribution from all points
          const allPoints = [
            ...(Array.isArray(summary.pain_points) ? summary.pain_points : []),
            ...(Array.isArray(summary.feature_requests) ? summary.feature_requests : []),
            ...(Array.isArray(summary.positive_aspects) ? summary.positive_aspects : [])
          ];

          // Extract some keywords from the points
          allPoints.forEach(point => {
            if (typeof point === 'string') {
              const words = point.split(' ');
              words.forEach(word => {
                if (word.length > 4) {
                  topKeywords[word] = (topKeywords[word] || 0) + 1;
                }
              });
            }
          });
        }

        // Prepare sentiment data for pie chart
        const sentimentData = Object.entries(sentimentDistribution).map(([name, value]) => ({
          name: name.charAt(0).toUpperCase() + name.slice(1),
          value
        }));

        // Prepare classification data for bar chart
        const classificationData = Object.entries(classificationDistribution).map(([name, value]) => ({
          name: name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
          value
        }));

        // Prepare game distribution data
        const gameData = Object.entries(gameDistribution)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 10)
          .map(([name, value]) => ({
            name,
            value
          }));

        // Prepare keyword data
        const keywordData = Object.entries(topKeywords)
          .slice(0, 10)
          .map(([keyword, count]) => ({
            name: keyword,
            value: count
          }));

        // Make sure summary has all required properties for the UI
        const enhancedSummary = {
          ...summary,
          // Ensure these properties exist with default values if missing
          total_reviews: summary.total_reviews ||
                        (summary.pain_points?.length || 0) +
                        (summary.feature_requests?.length || 0) +
                        (summary.positive_aspects?.length || 0) || 0,
          average_sentiment: summary.average_sentiment || 0.5,
          game_distribution: summary.game_distribution || gameDistribution,
          top_keywords: summary.top_keywords || topKeywords
        };

        setChartData({
          sentimentData,
          classificationData,
          gameData,
          keywordData,
          summary: enhancedSummary
        });
      } catch (error) {
        console.error('Error processing visualization data:', error);
        // Set minimal chart data to prevent rendering errors
        setChartData({
          sentimentData: [],
          classificationData: [],
          gameData: [],
          keywordData: [],
          summary: {
            total_reviews: 0,
            average_sentiment: 0,
            game_distribution: {},
            top_keywords: {}
          }
        });
      }
    }
  }, [data]);

  if (!chartData) return null;

  const { sentimentData, classificationData, gameData, keywordData, summary } = chartData;

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: {
        duration: 0.5
      }
    }
  };

  return (
    <motion.div
      className="space-y-8 p-4"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-6">
        {['overview', 'sentiment', 'classification', 'games', 'keywords'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 rounded-lg transition-all duration-200 ${
              activeTab === tab
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      <AnimatePresence mode="wait">
        {activeTab === 'overview' && (
          <motion.div
            key="overview"
            variants={itemVariants}
            className="grid grid-cols-1 md:grid-cols-2 gap-8"
          >
            {/* Summary Statistics */}
            <motion.div
              className="bg-white rounded-lg shadow-lg p-6 col-span-2"
              variants={itemVariants}
            >
              <h3 className="text-xl font-semibold mb-6">Summary Statistics</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                <motion.div
                  className="text-center p-4 bg-blue-50 rounded-lg"
                  variants={itemVariants}
                >
                  <p className="text-3xl font-bold text-blue-600">
                    <AnimatedNumber value={summary.total_reviews} />
                  </p>
                  <p className="text-gray-600 mt-2">Total Reviews</p>
                </motion.div>
                <motion.div
                  className="text-center p-4 bg-green-50 rounded-lg"
                  variants={itemVariants}
                >
                  <p className="text-3xl font-bold text-green-600">
                    <AnimatedNumber
                      value={summary.average_sentiment * 100}
                      suffix="%"
                      duration={2}
                    />
                  </p>
                  <p className="text-gray-600 mt-2">Average Sentiment</p>
                </motion.div>
                <motion.div
                  className="text-center p-4 bg-purple-50 rounded-lg"
                  variants={itemVariants}
                >
                  <p className="text-3xl font-bold text-purple-600">
                    <AnimatedNumber
                      value={Object.keys(summary.game_distribution).length}
                    />
                  </p>
                  <p className="text-gray-600 mt-2">Games Analyzed</p>
                </motion.div>
                <motion.div
                  className="text-center p-4 bg-orange-50 rounded-lg"
                  variants={itemVariants}
                >
                  <p className="text-3xl font-bold text-orange-600">
                    <AnimatedNumber
                      value={Object.keys(summary.top_keywords).length}
                    />
                  </p>
                  <p className="text-gray-600 mt-2">Unique Keywords</p>
                </motion.div>
              </div>
            </motion.div>
          </motion.div>
        )}

        {activeTab === 'sentiment' && (
          <motion.div
            key="sentiment"
            variants={itemVariants}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <h3 className="text-xl font-semibold mb-6">Sentiment Distribution</h3>
            <ResponsiveContainer width="100%" height={400}>
              <PieChart>
                <Pie
                  data={sentimentData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  outerRadius={150}
                  fill="#8884d8"
                  dataKey="value"
                  animationDuration={1000}
                >
                  {sentimentData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </motion.div>
        )}

        {activeTab === 'classification' && (
          <motion.div
            key="classification"
            variants={itemVariants}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <h3 className="text-xl font-semibold mb-6">Feedback Classification</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={classificationData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="name"
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  tick={{ fontSize: 12 }}
                />
                <YAxis />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="value"
                  fill="#8884d8"
                  animationDuration={1000}
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}

        {activeTab === 'games' && (
          <motion.div
            key="games"
            variants={itemVariants}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <h3 className="text-xl font-semibold mb-6">Top Games</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={gameData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={200}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="value"
                  fill="#82ca9d"
                  animationDuration={1000}
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}

        {activeTab === 'keywords' && (
          <motion.div
            key="keywords"
            variants={itemVariants}
            className="bg-white rounded-lg shadow-lg p-6"
          >
            <h3 className="text-xl font-semibold mb-6">Top Keywords</h3>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart data={keywordData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis
                  dataKey="name"
                  type="category"
                  width={150}
                  tick={{ fontSize: 12 }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Bar
                  dataKey="value"
                  fill="#ffc658"
                  animationDuration={1000}
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default DataVisualization;