import { useState } from 'react';
import api from '../services/api';

/**
 * Custom hook for handling data processing operations
 */
const useDataProcessing = (processingHook) => {
  // Destructure processing hook values
  const {
    setLoading,
    setError,
    setProcessingStep,
    startProgressSimulation,
    completeProgress,
    resetProcessing,
    setRecordCount
  } = processingHook;

  // Data state
  const [analyzedReviews, setAnalyzedReviews] = useState([]);
  const [summary, setSummary] = useState(null);
  const [activeView, setActiveView] = useState('reviews');

  // Process file upload
  const processFileUpload = async (file) => {
    if (!file) return;

    try {
      setLoading(true);
      setError(null);
      setProcessingStep(0);

      // Start timing the upload operation
      const uploadStartTime = Date.now();

      // Simulate upload progress
      const uploadInterval = startProgressSimulation();

      // Upload and analyze the file
      const response = await api.uploadFile(file);

      // Clear upload interval and complete progress
      clearInterval(uploadInterval);
      completeProgress();

      // Record upload processing time
      await api.recordProcessingTime('upload', uploadStartTime, response.length, file.name);

      // Move to sentiment analysis step
      setProcessingStep(1);
      const sentimentStartTime = Date.now();

      // Perform sentiment analysis
      const sentimentResponse = await api.analyzeSentiment(
        response.map(review => review.text)
      );

      // Record sentiment analysis processing time
      await api.recordProcessingTime(
        'sentiment_analysis', 
        sentimentStartTime, 
        response.length, 
        file.name
      );

      // Update reviews with advanced sentiment data
      const reviewsWithSentiment = response.map((review, index) => ({
        ...review,
        advanced_sentiment: sentimentResponse.results[index]
      }));

      // Process categorization
      setProcessingStep(2);
      const categorizationStartTime = Date.now();
      await new Promise(resolve => setTimeout(resolve, 1000));
      await api.recordProcessingTime(
        'categorization', 
        categorizationStartTime, 
        response.length, 
        file.name
      );

      // Process keyword extraction
      setProcessingStep(3);
      const keywordStartTime = Date.now();
      await new Promise(resolve => setTimeout(resolve, 1000));
      await api.recordProcessingTime(
        'keyword_extraction', 
        keywordStartTime, 
        response.length, 
        file.name
      );

      // Store the analyzed reviews
      setAnalyzedReviews(reviewsWithSentiment);
      setRecordCount(reviewsWithSentiment.length);

      // Move to summary creation step
      setProcessingStep(4);

      // Generate summary
      await generateSummary(reviewsWithSentiment, file.name, 'csv');

      // Switch to the summary view
      setActiveView('summary');
    } catch (err) {
      console.error('Upload error:', err);
      if (err.response?.status === 400 && err.response?.data?.detail?.includes("'text' column")) {
        setError("CSV file must contain a 'text' column. Please check your file format.");
      } else {
        setError(err.response?.data?.detail || 'Error uploading file');
      }
    } finally {
      resetProcessing();
    }
  };

  // Process data scraping
  const processScraping = async (source, query, limit) => {
    try {
      setLoading(true);
      setError(null);
      setProcessingStep(0);

      // Start timing the scrape operation
      const scrapeStartTime = Date.now();

      // Simulate data collection progress
      const scrapeInterval = startProgressSimulation(200, 3);

      // Scrape and analyze the data
      const response = await api.scrapeData(source, query, limit);

      // Clear interval and complete progress
      clearInterval(scrapeInterval);
      completeProgress();

      // Record scrape processing time
      await api.recordProcessingTime(
        'scrape', 
        scrapeStartTime, 
        response.length, 
        null, 
        source, 
        query
      );

      // Process sentiment analysis
      setProcessingStep(1);
      const sentimentStartTime = Date.now();
      const sentimentResponse = await api.analyzeSentiment(
        response.map(review => review.text)
      );
      await api.recordProcessingTime(
        'sentiment_analysis', 
        sentimentStartTime, 
        response.length, 
        null, 
        source, 
        query
      );

      // Update reviews with advanced sentiment data
      const reviewsWithSentiment = response.map((review, index) => ({
        ...review,
        advanced_sentiment: sentimentResponse.results[index]
      }));

      // Process categorization and keyword extraction
      setProcessingStep(2);
      const categorizationStartTime = Date.now();
      await new Promise(resolve => setTimeout(resolve, 1000));
      await api.recordProcessingTime(
        'categorization', 
        categorizationStartTime, 
        response.length, 
        null, 
        source, 
        query
      );

      setProcessingStep(3);
      const keywordStartTime = Date.now();
      await new Promise(resolve => setTimeout(resolve, 1000));
      await api.recordProcessingTime(
        'keyword_extraction', 
        keywordStartTime, 
        response.length, 
        null, 
        source, 
        query
      );

      // Store the analyzed reviews
      setAnalyzedReviews(reviewsWithSentiment);
      setRecordCount(reviewsWithSentiment.length);

      // Move to summary creation step
      setProcessingStep(4);

      // Generate summary
      await generateSummary(reviewsWithSentiment, query, source);

      // Switch to the summary view
      setActiveView('summary');
    } catch (err) {
      console.error('Scrape error:', err);
      setError(err.response?.data?.detail || 'Error scraping data');
    } finally {
      resetProcessing();
    }
  };

  // Process GitHub repository analysis
  const processGitHubAnalysis = async (url) => {
    try {
      setLoading(true);
      setError(null);
      setProcessingStep(0);

      // Simulate data collection progress
      const fetchInterval = startProgressSimulation(150, 2);

      // Analyze GitHub repository
      const { repoData, analyzedReviews: githubReviews } = await api.analyzeGitHub(url);

      // Clear interval and complete progress
      clearInterval(fetchInterval);
      completeProgress();

      // Process sentiment, categorization, and keywords
      for (let step = 1; step <= 3; step++) {
        setProcessingStep(step);
        await new Promise(resolve => setTimeout(resolve, 1500));
      }

      // Store the analyzed reviews
      setAnalyzedReviews(githubReviews);
      setRecordCount(githubReviews.length);

      // Move to summary creation step
      setProcessingStep(4);

      // Generate summary
      await generateSummary(githubReviews, url, 'github');

      // Switch to the summary view
      setActiveView('summary');
    } catch (err) {
      console.error('GitHub analysis error:', err);
      setError('Error analyzing GitHub repository');
    } finally {
      resetProcessing();
    }
  };

  // Generate summary from analyzed reviews
  const generateSummary = async (reviewsData, sourceName, sourceType) => {
    const startTime = Date.now();

    try {
      // Send the analyzed reviews to get a summary
      const summaryData = await api.generateSummary(reviewsData);
      setSummary(summaryData);

      // Record processing time
      await api.recordProcessingTime('summary_generation', startTime, reviewsData.length);

      // Record analysis history
      try {
        await api.recordAnalysisHistory(sourceType, sourceName, reviewsData, summaryData);
        console.log('Recorded analysis history');
      } catch (historyError) {
        console.error('Error recording analysis history:', historyError);
      }
    } catch (err) {
      console.error('Summary error:', err);
      setError(err.response?.data?.detail || 'Error generating summary');
      throw err;
    }
  };

  // Download PDF report
  const downloadPDF = async () => {
    try {
      setLoading(true);
      await api.downloadPDF(analyzedReviews);
    } catch (err) {
      console.error('PDF error:', err);
      setError(err.response?.data?.detail || 'Error downloading PDF');
    } finally {
      setLoading(false);
    }
  };

  return {
    analyzedReviews,
    summary,
    activeView,
    setActiveView,
    processFileUpload,
    processScraping,
    processGitHubAnalysis,
    downloadPDF
  };
};

export default useDataProcessing;
