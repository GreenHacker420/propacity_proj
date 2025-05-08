import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line
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
  const [timeRange, setTimeRange] = useState('all');
  const [selectedGame, setSelectedGame] = useState('all');

  useEffect(() => {
    if (data) {
      try {
        const summary = data.summary || data;

        if (!summary) {
          console.error('Summary data is missing');
          setDefaultChartData();
          return;
        }

        // Initialize distributions with default empty objects
        const distributions = {
          sentiment: summary.sentiment_distribution || {},
          classification: summary.classification_distribution || {},
          game: summary.game_distribution || {},
          keywords: summary.top_keywords || {},
          timeBased: summary.time_based_distribution || {},
          userSegments: summary.user_segments || {},
          featureRequests: summary.feature_requests || {},
          painPoints: summary.pain_points || {}
        };

        // Calculate additional metrics
        const metrics = {
          averageResponseTime: calculateAverageResponseTime(data.reviews),
          userSatisfactionScore: calculateUserSatisfactionScore(distributions.sentiment),
          featureAdoptionRate: calculateFeatureAdoptionRate(data.reviews),
          bugReportRate: calculateBugReportRate(data.reviews),
          userRetentionScore: calculateUserRetentionScore(data.reviews)
        };

        // Prepare chart data with enhanced metrics
        const chartData = {
          sentimentData: prepareChartData(distributions.sentiment),
          classificationData: prepareChartData(distributions.classification),
          gameData: prepareChartData(distributions.game, 8),
          keywordData: prepareChartData(distributions.keywords, 15),
          timeBasedData: prepareTimeBasedData(distributions.timeBased),
          userSegmentData: prepareUserSegmentData(distributions.userSegments),
          featureRequestData: prepareFeatureRequestData(distributions.featureRequests),
          painPointData: preparePainPointData(distributions.painPoints),
          metrics: metrics,
          summary: {
            ...summary,
            total_reviews: data.reviews ? data.reviews.length : calculateTotalReviews(distributions.sentiment),
            average_sentiment: summary.average_sentiment || calculateAverageSentiment(distributions.sentiment),
            sentiment_distribution: distributions.sentiment,
            classification_distribution: distributions.classification,
            game_distribution: distributions.game,
            top_keywords: distributions.keywords,
            time_based_distribution: distributions.timeBased,
            user_segments: distributions.userSegments,
            feature_requests: distributions.featureRequests,
            pain_points: distributions.painPoints
          }
        };

        setChartData(chartData);
      } catch (error) {
        console.error('Error processing visualization data:', error);
        setDefaultChartData();
      }
    }
  }, [data, timeRange, selectedGame]);

  // Helper functions for new metrics
  const calculateAverageResponseTime = (reviews) => {
    if (!Array.isArray(reviews)) return 0;
    const responseTimes = reviews
      .filter(review => review.response_time)
      .map(review => review.response_time);
    return responseTimes.length > 0
      ? responseTimes.reduce((a, b) => a + b, 0) / responseTimes.length
      : 0;
  };

  const calculateUserSatisfactionScore = (sentimentDistribution) => {
    const total = Object.values(sentimentDistribution).reduce((a, b) => a + b, 0);
    if (total === 0) return 0;
    const positiveWeight = sentimentDistribution.positive || 0;
    const neutralWeight = (sentimentDistribution.neutral || 0) * 0.5;
    return ((positiveWeight + neutralWeight) / total) * 100;
  };

  const calculateFeatureAdoptionRate = (reviews) => {
    if (!Array.isArray(reviews)) return 0;
    const featureMentions = reviews.filter(review => 
      review.classification === 'feature_request' || 
      review.classification === 'positive_feedback'
    ).length;
    return (featureMentions / reviews.length) * 100;
  };

  const calculateBugReportRate = (reviews) => {
    if (!Array.isArray(reviews)) return 0;
    const bugReports = reviews.filter(review => 
      review.classification === 'bug_report' || 
      review.classification === 'pain_point'
    ).length;
    return (bugReports / reviews.length) * 100;
  };

  const calculateUserRetentionScore = (reviews) => {
    if (!Array.isArray(reviews)) return 0;
    const returningUsers = reviews.filter(review => review.is_returning_user).length;
    return (returningUsers / reviews.length) * 100;
  };

  // New helper functions for data preparation
  const prepareTimeBasedData = (timeBasedDistribution) => {
    return Object.entries(timeBasedDistribution || {}).map(([time, value]) => ({
      time,
      value
    }));
  };

  const prepareUserSegmentData = (userSegments) => {
    return Object.entries(userSegments || {}).map(([segment, value]) => ({
      segment,
      value
    }));
  };

  const prepareFeatureRequestData = (featureRequests) => {
    return Object.entries(featureRequests || {}).map(([feature, value]) => ({
      feature,
      value
    }));
  };

  const preparePainPointData = (painPoints) => {
    return Object.entries(painPoints || {}).map(([point, value]) => ({
      point,
            value
          }));
  };

  // Helper function to prepare chart data
  const prepareChartData = (distribution, limit = null) => {
    const data = Object.entries(distribution)
          .filter(([_, value]) => value > 0)
          .map(([name, value]) => ({
            name: name.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
            value
          }));

    return limit ? data.sort((a, b) => b.value - a.value).slice(0, limit) : data;
  };

  // Helper function to calculate total reviews
  const calculateTotalReviews = (sentimentDistribution) => {
    return Object.values(sentimentDistribution).reduce((sum, val) => sum + val, 0);
  };

  // Helper function to calculate average sentiment
  const calculateAverageSentiment = (sentimentDistribution) => {
    const weights = { positive: 1.0, neutral: 0.5, negative: 0.0 };
    const totalSentiment = Object.entries(sentimentDistribution)
      .reduce((sum, [key, val]) => sum + (weights[key] || 0.5) * val, 0);
    const totalItems = calculateTotalReviews(sentimentDistribution);
    return totalItems > 0 ? totalSentiment / totalItems : 0.5;
  };

  // Helper function to set default chart data
  const setDefaultChartData = () => {
        setChartData({
          sentimentData: [],
          classificationData: [],
          gameData: [],
          keywordData: [],
      timeBasedData: [],
      userSegmentData: [],
      featureRequestData: [],
      painPointData: [],
      metrics: {
        averageResponseTime: 0,
        userSatisfactionScore: 0,
        featureAdoptionRate: 0,
        bugReportRate: 0,
        userRetentionScore: 0
      },
          summary: {
            total_reviews: 0,
            average_sentiment: 0,
        sentiment_distribution: {},
        classification_distribution: {},
            game_distribution: {},
        top_keywords: {},
        time_based_distribution: {},
        user_segments: {},
        feature_requests: {},
        pain_points: {}
      }
    });
  };

  if (!chartData) return null;

  const { sentimentData, classificationData, gameData, keywordData, timeBasedData, userSegmentData, featureRequestData, painPointData, metrics, summary } = chartData;

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
      {/* Filters */}
      <div className="flex space-x-4 mb-6">
        <select
          value={timeRange}
          onChange={(e) => setTimeRange(e.target.value)}
          className="px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Time</option>
          <option value="week">Last Week</option>
          <option value="month">Last Month</option>
          <option value="quarter">Last Quarter</option>
          <option value="year">Last Year</option>
        </select>

        <select
          value={selectedGame}
          onChange={(e) => setSelectedGame(e.target.value)}
          className="px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="all">All Games</option>
          {gameData.map((game) => (
            <option key={game.name} value={game.name}>
              {game.name}
            </option>
          ))}
        </select>
      </div>

      {/* Navigation Tabs */}
      <div className="flex space-x-4 mb-6">
        {['overview', 'sentiment', 'classification', 'games', 'keywords', 'trends', 'segments'].map((tab) => (
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
            {/* Enhanced Summary Statistics */}
            <motion.div
              className="bg-white rounded-lg shadow-lg p-6 col-span-2"
              variants={itemVariants}
            >
              <h3 className="text-xl font-semibold mb-6">Key Metrics</h3>
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
                      value={metrics.userSatisfactionScore}
                      suffix="%"
                      duration={2}
                    />
                  </p>
                  <p className="text-gray-600 mt-2">User Satisfaction</p>
                </motion.div>
                <motion.div
                  className="text-center p-4 bg-purple-50 rounded-lg"
                  variants={itemVariants}
                >
                  <p className="text-3xl font-bold text-purple-600">
                    <AnimatedNumber
                      value={metrics.featureAdoptionRate}
                      suffix="%"
                      duration={2}
                    />
                  </p>
                  <p className="text-gray-600 mt-2">Feature Adoption</p>
                </motion.div>
                <motion.div
                  className="text-center p-4 bg-orange-50 rounded-lg"
                  variants={itemVariants}
                >
                  <p className="text-3xl font-bold text-orange-600">
                    <AnimatedNumber
                      value={metrics.userRetentionScore}
                      suffix="%"
                      duration={2}
                    />
                  </p>
                  <p className="text-gray-600 mt-2">User Retention</p>
                </motion.div>
              </div>
            </motion.div>

            {/* Additional Metrics */}
            <motion.div
              className="bg-white rounded-lg shadow-lg p-6"
              variants={itemVariants}
            >
              <h3 className="text-xl font-semibold mb-6">Response Time Analysis</h3>
              <div className="text-center">
                <p className="text-4xl font-bold text-blue-600">
                  {metrics.averageResponseTime.toFixed(1)}h
                </p>
                <p className="text-gray-600 mt-2">Average Response Time</p>
              </div>
            </motion.div>

            <motion.div
              className="bg-white rounded-lg shadow-lg p-6"
              variants={itemVariants}
            >
              <h3 className="text-xl font-semibold mb-6">Bug Report Rate</h3>
              <div className="text-center">
                <p className="text-4xl font-bold text-red-600">
                  {metrics.bugReportRate.toFixed(1)}%
                </p>
                <p className="text-gray-600 mt-2">Bug Reports</p>
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

        {/* New Trends Tab */}
        {activeTab === 'trends' && (
          <motion.div
            key="trends"
            variants={itemVariants}
            className="space-y-6"
          >
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-6">Time-Based Trends</h3>
              <ResponsiveContainer width="100%" height={400}>
                <LineChart data={timeBasedData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <Tooltip content={<CustomTooltip />} />
                  <Line type="monotone" dataKey="value" stroke="#8884d8" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}

        {/* New Segments Tab */}
        {activeTab === 'segments' && (
          <motion.div
            key="segments"
            variants={itemVariants}
            className="space-y-6"
          >
            <div className="bg-white rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold mb-6">User Segments</h3>
              <ResponsiveContainer width="100%" height={400}>
                <PieChart>
                  <Pie
                    data={userSegmentData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                    outerRadius={150}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {userSegmentData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default DataVisualization;