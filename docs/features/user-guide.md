# User Guide

This guide provides instructions for using the Product Review Analyzer effectively.

## Getting Started

### Logging In

1. Navigate to the application URL
2. Enter your username and password
3. Click "Log In"

If you don't have an account, contact your administrator to create one.

### Dashboard Overview

The dashboard provides an overview of:

- Recent analyses
- Sentiment distribution
- Top topics
- Weekly summaries

## Analyzing Reviews

### Uploading CSV Files

1. Click the "Upload" button in the navigation menu
2. Select a CSV file containing reviews
   - The file should have columns for review text
   - Optional columns: ID, category, source
3. Click "Upload and Analyze"
4. Wait for the analysis to complete
   - You'll see a progress bar with estimated completion time
   - The page will update automatically when analysis is complete

### CSV File Format

The system supports various CSV formats, but at minimum should contain review text. Example formats:

**Simple Format:**
```
text
"This product is amazing!"
"I had issues with the battery life."
```

**Detailed Format:**
```
id,category,text
1001,hardware,"The build quality is excellent."
1002,software,"The app crashes frequently."
```

### Scraping Reviews

1. Click the "Scrape" button in the navigation menu
2. Select the source (Twitter, Play Store)
3. Enter search query or app URL
4. Set the maximum number of reviews to fetch
5. Click "Scrape and Analyze"
6. Wait for scraping and analysis to complete

### Manual Input

1. Click the "Analyze" button in the navigation menu
2. Enter reviews in the text area (one per line)
3. Click "Analyze"
4. View the results

## Understanding Results

### Sentiment Analysis

The sentiment analysis classifies reviews as:

- **Positive**: Favorable opinions (score > 0.3)
- **Neutral**: Balanced or factual statements (-0.3 to 0.3)
- **Negative**: Unfavorable opinions (score < -0.3)

Each review includes a sentiment score from -1.0 (very negative) to 1.0 (very positive).

### Key Insights

The system extracts several types of insights:

- **Pain Points**: Issues or problems mentioned in reviews
- **Feature Requests**: Suggestions for new features
- **Positive Feedback**: Aspects that users appreciate

These insights are grouped by topic and ranked by frequency.

### Topic Clustering

Reviews are clustered by common topics to identify patterns:

- Each topic shows the number of reviews
- Topics are color-coded by average sentiment
- Click on a topic to see all related reviews

### Summary

The summary section provides:

- Overall sentiment distribution
- Key takeaways from the analysis
- Recommended actions based on insights
- Most impactful issues to address

## Working with History

### Viewing Past Analyses

1. Click the "History" button in the navigation menu
2. Browse the list of past analyses
3. Click on any analysis to view details
4. Filter by date range or source

### Comparing Analyses

1. Select two analyses from the history
2. Click "Compare"
3. View side-by-side comparison of:
   - Sentiment changes
   - Topic shifts
   - New or resolved issues

## Weekly Summaries

### Generating Weekly Summaries

1. Click the "Weekly" button in the navigation menu
2. Select the date range (default: last 7 days)
3. Click "Generate Summary"
4. View the aggregated insights

### Understanding Weekly Reports

The weekly summary includes:

- Sentiment trends over the week
- Top emerging topics
- Recurring issues
- Recommendations for prioritization

## Batch Processing Features

### Progress Tracking

When processing large datasets:

1. A progress bar shows completion percentage
2. Estimated time remaining is displayed
3. Processing speed is shown (items per second)
4. Current batch and total batches are indicated

### Circuit Breaker Status

The system uses a circuit breaker pattern to handle API limitations:

- **Closed**: Normal operation using Gemini API
- **Open**: Using local processing due to API issues
- **Half-Open**: Testing if API has recovered

The status is displayed during processing.

## Exporting Data

### Export Options

1. Click the "Export" button on any analysis
2. Select the export format:
   - CSV: For spreadsheet analysis
   - JSON: For programmatic use
   - PDF: For reporting
3. Choose what to include:
   - Raw reviews
   - Sentiment analysis
   - Insights
   - Summary
4. Click "Export" to download the file

## Account Management

### Updating Profile

1. Click your username in the top-right corner
2. Select "Profile"
3. Update your information
4. Click "Save Changes"

### Changing Password

1. Click your username in the top-right corner
2. Select "Change Password"
3. Enter your current password
4. Enter and confirm your new password
5. Click "Update Password"

## Tips for Best Results

1. **Provide Context**: Include metadata like product category for better insights
2. **Use Consistent Format**: Maintain consistent CSV structure for batch uploads
3. **Process in Batches**: For very large datasets, split into multiple files
4. **Review Summaries**: Always check the generated summaries for accuracy
5. **Combine Sources**: Analyze reviews from multiple sources for comprehensive insights
