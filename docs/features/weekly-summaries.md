# Weekly Summaries

The Product Review Analyzer includes a powerful weekly summary feature that aggregates and analyzes user feedback over time periods to help product managers identify trends, prioritize issues, and make data-driven decisions.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![React](https://img.shields.io/badge/React-Latest-blue)
![MongoDB](https://img.shields.io/badge/MongoDB-Atlas-green)
![AI](https://img.shields.io/badge/AI-Gemini_API-red)
![NLP](https://img.shields.io/badge/NLP-Sentiment_Analysis-yellow)
![Deployment](https://img.shields.io/badge/Deployment-AWS_EC2-orange)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

## Overview

The weekly summary feature:

1. Aggregates reviews and feedback over a specified time period (default: 7 days)
2. Analyzes sentiment trends and changes over time
3. Identifies emerging issues and recurring problems
4. Extracts top keywords and topics from the period
5. Generates actionable recommendations for product managers
6. Provides visualizations of key metrics and trends
7. Allows customizable date ranges for flexible reporting

## Key Features

- **Time Range Selection**: Filter summaries by custom date ranges
- **Sentiment Trend Analysis**: Track sentiment changes over time
- **Top Issues Identification**: Automatically identify most impactful problems
- **Feature Request Prioritization**: Rank feature requests by frequency and impact
- **Positive Feedback Highlights**: Showcase what users love about the product
- **Keyword Trend Analysis**: Track emerging topics and terms
- **Actionable Recommendations**: AI-generated suggestions for product priorities
- **Visualization Components**: Interactive charts and graphs of key metrics
- **PDF Export**: Generate shareable PDF reports of weekly summaries

## Implementation Details

### Data Aggregation

The system aggregates data from multiple sources:

```python
async def generate_weekly_summary(
    self,
    source_type: str,
    source_name: str,
    start_date: datetime,
    end_date: datetime
) -> WeeklySummary:
    """
    Generate a weekly summary for the specified source and date range.
    
    Args:
        source_type: Type of source (e.g., 'csv', 'play_store', 'github')
        source_name: Name of the source
        start_date: Start date for the summary
        end_date: End date for the summary
        
    Returns:
        WeeklySummary object with aggregated insights
    """
    # Query reviews within the date range
    query = {
        "source_type": source_type,
        "source_name": source_name,
        "timestamp": {
            "$gte": start_date,
            "$lte": end_date
        }
    }
    
    # Fetch reviews from database
    reviews = await self.db.reviews.find(query).to_list(length=None)
    
    # Process reviews and generate summary
    # ...
```

### Trend Analysis

The system analyzes trends by comparing current data with historical data:

```python
def _analyze_trends(self, reviews: List[Dict]) -> Dict[str, Any]:
    """
    Analyze trends in the reviews.
    
    Args:
        reviews: List of review dictionaries
        
    Returns:
        Dictionary with trend analysis
    """
    # Group reviews by day
    reviews_by_day = {}
    for review in reviews:
        day = review["timestamp"].date()
        if day not in reviews_by_day:
            reviews_by_day[day] = []
        reviews_by_day[day].append(review)
    
    # Calculate daily sentiment averages
    daily_sentiment = {}
    for day, day_reviews in reviews_by_day.items():
        total_sentiment = sum(r["sentiment_score"] for r in day_reviews)
        avg_sentiment = total_sentiment / len(day_reviews)
        daily_sentiment[day.isoformat()] = avg_sentiment
    
    # Identify sentiment trend
    sentiment_values = list(daily_sentiment.values())
    if len(sentiment_values) >= 2:
        sentiment_trend = sentiment_values[-1] - sentiment_values[0]
    else:
        sentiment_trend = 0
    
    # Return trend analysis
    return {
        "daily_sentiment": daily_sentiment,
        "sentiment_trend": sentiment_trend,
        "trend_direction": "improving" if sentiment_trend > 0.05 else 
                          "declining" if sentiment_trend < -0.05 else "stable"
    }
```

### Recommendation Generation

The system generates actionable recommendations based on the analyzed data:

```python
def _generate_recommendations(
    self,
    pain_points: List[PriorityItem],
    feature_requests: List[PriorityItem],
    positive_feedback: List[PriorityItem],
    trend_analysis: Dict[str, Any]
) -> List[str]:
    """
    Generate recommendations based on the analyzed data.
    
    Args:
        pain_points: List of pain point items
        feature_requests: List of feature request items
        positive_feedback: List of positive feedback items
        trend_analysis: Dictionary with trend analysis
        
    Returns:
        List of recommendation strings
    """
    recommendations = []
    
    # Add high-priority pain points
    high_priority_issues = [p for p in pain_points if p.priority_score > 0.7]
    if high_priority_issues:
        recommendations.append(
            f"Address high-priority issues: {', '.join(i.text for i in high_priority_issues[:3])}"
        )
    
    # Add trending feature requests
    top_features = sorted(feature_requests, key=lambda x: x.priority_score, reverse=True)
    if top_features:
        recommendations.append(
            f"Consider implementing requested features: {', '.join(i.text for i in top_features[:3])}"
        )
    
    # Add recommendations based on sentiment trend
    if trend_analysis["trend_direction"] == "declining":
        recommendations.append(
            "Investigate causes of declining sentiment and address user concerns promptly"
        )
    
    # Add recommendations to maintain positive aspects
    if positive_feedback:
        recommendations.append(
            f"Maintain strengths in: {', '.join(i.text for i in positive_feedback[:3])}"
        )
    
    return recommendations
```

## Frontend Integration

The weekly summary feature is integrated into the frontend with a dedicated view:

```jsx
import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import { DateRangePicker } from '../components/DateRangePicker';
import { SentimentTrendChart } from '../components/SentimentTrendChart';
import { PriorityList } from '../components/PriorityList';
import { KeywordCloud } from '../components/KeywordCloud';
import { RecommendationsList } from '../components/RecommendationsList';

const WeeklySummaryView = () => {
  const [dateRange, setDateRange] = useState({
    startDate: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000),
    endDate: new Date()
  });
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(false);
  const api = useApi();
  
  const fetchSummary = async () => {
    setLoading(true);
    try {
      const response = await api.getWeeklySummary({
        source_type: 'all',
        source_name: 'all',
        start_date: dateRange.startDate.toISOString(),
        end_date: dateRange.endDate.toISOString()
      });
      setSummaryData(response.data);
    } catch (error) {
      console.error('Error fetching weekly summary:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchSummary();
  }, [dateRange]);
  
  return (
    <div className="weekly-summary-container">
      <h1>Weekly Summary</h1>
      
      <DateRangePicker
        startDate={dateRange.startDate}
        endDate={dateRange.endDate}
        onChange={setDateRange}
      />
      
      {loading ? (
        <div className="loading-spinner">Loading...</div>
      ) : summaryData ? (
        <>
          <div className="summary-stats">
            <div className="stat-card">
              <h3>Total Reviews</h3>
              <p>{summaryData.total_reviews}</p>
            </div>
            <div className="stat-card">
              <h3>Average Sentiment</h3>
              <p>{summaryData.avg_sentiment_score.toFixed(2)}</p>
            </div>
          </div>
          
          <SentimentTrendChart data={summaryData.trend_analysis.daily_sentiment} />
          
          <div className="summary-sections">
            <div className="section">
              <h2>Top Pain Points</h2>
              <PriorityList items={summaryData.pain_points} />
            </div>
            
            <div className="section">
              <h2>Feature Requests</h2>
              <PriorityList items={summaryData.feature_requests} />
            </div>
            
            <div className="section">
              <h2>Positive Feedback</h2>
              <PriorityList items={summaryData.positive_feedback} />
            </div>
          </div>
          
          <div className="section">
            <h2>Top Keywords</h2>
            <KeywordCloud keywords={summaryData.top_keywords} />
          </div>
          
          <div className="section">
            <h2>Recommendations</h2>
            <RecommendationsList items={summaryData.recommendations} />
          </div>
        </>
      ) : (
        <div className="no-data">No summary data available for the selected period.</div>
      )}
    </div>
  );
};

export default WeeklySummaryView;
```

## API Endpoints

### Generate Weekly Summary

```
POST /api/summary/weekly
```

**Request Body:**
```json
{
  "source_type": "play_store",
  "source_name": "com.example.app",
  "start_date": "2023-05-01T00:00:00Z",
  "end_date": "2023-05-07T23:59:59Z"
}
```

**Response:**
```json
{
  "id": "60f1e5b3a7c8b9e1d2f3a4b5",
  "source_type": "play_store",
  "source_name": "com.example.app",
  "start_date": "2023-05-01T00:00:00Z",
  "end_date": "2023-05-07T23:59:59Z",
  "total_reviews": 1250,
  "avg_sentiment_score": 0.65,
  "pain_points": [
    {
      "text": "App crashes during photo upload",
      "count": 45,
      "priority_score": 0.85
    },
    // More pain points...
  ],
  "feature_requests": [
    {
      "text": "Dark mode option",
      "count": 78,
      "priority_score": 0.75
    },
    // More feature requests...
  ],
  "positive_feedback": [
    {
      "text": "Great user interface",
      "count": 120,
      "priority_score": 0.90
    },
    // More positive feedback...
  ],
  "top_keywords": {
    "crash": 67,
    "dark": 82,
    "mode": 79,
    "interface": 145,
    "login": 56,
    "fast": 112,
    "battery": 43,
    "responsive": 89,
    "slow": 38,
    "beautiful": 76
  },
  "trend_analysis": {
    "daily_sentiment": {
      "2023-05-01": 0.62,
      "2023-05-02": 0.64,
      "2023-05-03": 0.63,
      "2023-05-04": 0.65,
      "2023-05-05": 0.67,
      "2023-05-06": 0.66,
      "2023-05-07": 0.68
    },
    "sentiment_trend": 0.06,
    "trend_direction": "improving"
  },
  "recommendations": [
    "Address high-priority issues: App crashes during photo upload, Login failures after update",
    "Consider implementing requested features: Dark mode option, Offline mode, Custom notifications",
    "Maintain strengths in: Great user interface, Fast performance, Intuitive navigation"
  ],
  "created_at": "2023-05-08T09:15:30Z"
}
```

## Best Practices

For optimal use of the weekly summary feature:

1. **Regular Reviews**: Schedule weekly review sessions with your product team
2. **Consistent Time Periods**: Use consistent time periods for better trend analysis
3. **Multiple Sources**: Combine data from different sources for a complete picture
4. **Actionable Insights**: Focus on the recommendations and prioritize accordingly
5. **Share Reports**: Use the PDF export to share insights with stakeholders
6. **Track Changes**: Compare summaries over time to measure improvement
7. **Customize Date Ranges**: Use different time ranges for different insights

## Troubleshooting

Common issues and solutions:

### No Data Available

**Symptoms**:
- "No summary data available" message
- Empty charts and lists

**Solutions**:
- Verify the date range contains reviews
- Check that the source type and name are correct
- Ensure reviews are being properly stored in the database

### Incomplete Recommendations

**Symptoms**:
- Few or generic recommendations
- Missing important insights

**Solutions**:
- Increase the date range to include more data
- Ensure sentiment analysis is working correctly
- Check that reviews are properly categorized

### Performance Issues

**Symptoms**:
- Slow loading of weekly summary page
- Timeout errors when generating summaries

**Solutions**:
- Limit the date range for large datasets
- Optimize database queries with proper indexes
- Implement caching for frequently accessed summaries
