from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import random
import logging
import json
import os
import time
import tweepy
from google_play_scraper import app, Sort, reviews_all, reviews
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import backoff
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scraper:
    def __init__(self):
        """Initialize the scraper with Twitter API credentials"""
        # Twitter API credentials
        self.twitter_client = None
        self.setup_twitter_client()
        self.playstore_base_url = "https://play.google.com/store/apps/details"
        self.twitter_base_url = "https://api.twitter.com/2/tweets/search/recent"

    def setup_twitter_client(self):
        """Set up Twitter API client with credentials from environment variables"""
        try:
            bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
            if bearer_token:
                self.twitter_client = tweepy.Client(
                    bearer_token=bearer_token,
                    wait_on_rate_limit=True
                )
                logger.info("Twitter client initialized successfully")
            else:
                logger.warning("Twitter bearer token not found in environment variables")
        except Exception as e:
            logger.error(f"Error setting up Twitter client: {str(e)}")

    def scrape_twitter(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Scrape Twitter for tweets matching the query using Twitter API v2.

        Args:
            query: Search query for Twitter
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing tweet data
        """
        logger.info(f"Scraping Twitter for query: {query}, limit: {limit}")

        if not self.twitter_client:
            logger.warning("Twitter client not initialized, falling back to mock data")
            return self._get_mock_twitter_data(query, limit)

        try:
            # Search tweets using Twitter API v2
            tweets = []
            for tweet in tweepy.Paginator(
                self.twitter_client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                max_results=min(100, limit)  # Twitter API limit per request
            ).flatten(limit=limit):

                tweets.append({
                    "text": tweet.text,
                    "username": tweet.author_id,  # We only get author_id in basic access
                    "timestamp": tweet.created_at,
                    "rating": None,  # Twitter doesn't have ratings
                    "metrics": tweet.public_metrics
                })

            logger.info(f"Successfully scraped {len(tweets)} tweets")
            return tweets

        except Exception as e:
            logger.error(f"Error scraping Twitter: {str(e)}")
            logger.warning("Falling back to mock Twitter data")
            return self._get_mock_twitter_data(query, limit)

    def _get_mock_twitter_data(self, query: str, limit: int) -> List[Dict]:
        """Generate mock Twitter data for testing or when API fails"""
        mock_tweets = [
            "I love this app! It's so intuitive and easy to use.",
            "The app keeps crashing whenever I try to upload photos. Please fix this!",
            "Would love to have dark mode in the next update!",
            "Login with Google fails randomly. Very frustrating.",
            "Please add offline mode for travel. It would be so useful.",
            "Best app ever – beautiful UI and fast loading times.",
            "The search function is too slow. Takes forever to find anything.",
            "Can you add more customization options? Would make it perfect!",
            "Notifications are not working properly on my device.",
            "Love the new update! Much faster now.",
            "This app is a game changer for my productivity.",
            "The UI is confusing and hard to navigate.",
            "Wish there was a way to organize items into folders.",
            "App crashes every time I try to save my progress.",
            "Great customer support! They resolved my issue quickly."
        ]

        tweets = []
        for i in range(min(limit, len(mock_tweets))):
            tweets.append({
                "text": f"{query}: {mock_tweets[i]}",
                "username": f"user{i+1}",
                "timestamp": datetime.now() - timedelta(hours=random.randint(1, 72)),
                "rating": None,  # Twitter doesn't have ratings
                "metrics": {
                    "retweet_count": random.randint(0, 100),
                    "reply_count": random.randint(0, 50),
                    "like_count": random.randint(0, 200),
                    "quote_count": random.randint(0, 20)
                }
            })

        return tweets

    def extract_app_id(self, url_or_id: str) -> str:
        """
        Extract app ID from a Google Play Store URL or return the ID if it's already in the correct format

        Args:
            url_or_id: Either a full Google Play Store URL or an app ID

        Returns:
            The extracted app ID
        """
        # If it's already just an app ID, return it
        if not url_or_id.startswith('http'):
            return url_or_id

        # Try to extract app ID from URL
        match = re.search(r'id=([^&]+)', url_or_id)
        if match:
            return match.group(1)

        raise ValueError("Invalid Google Play Store URL format")

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def scrape_playstore(self, app_id_or_url: str, limit: int = 500, sort_by: str = 'newest') -> List[Dict]:
        """
        Scrape reviews from Google Play Store

        Args:
            app_id_or_url: Either a full Google Play Store URL or an app ID
            limit: Maximum number of reviews to fetch (default increased to 500)
            sort_by: Sort order ('newest', 'rating', 'helpfulness')

        Returns:
            List of review dictionaries
        """
        try:
            # Extract app ID from URL if needed
            app_id = self.extract_app_id(app_id_or_url)
            logger.info(f"Scraping Play Store reviews for app ID: {app_id}, limit: {limit}")

            # Limit the maximum number of reviews to prevent timeouts
            max_safe_limit = 5000
            if limit > max_safe_limit:
                logger.warning(f"Requested limit {limit} exceeds safe limit. Using {max_safe_limit} instead.")
                limit = max_safe_limit

            # Map sort_by to google_play_scraper Sort enum
            sort_mapping = {
                'newest': Sort.NEWEST,
                'rating': Sort.RATING,
                'helpfulness': Sort.MOST_RELEVANT,  # closest match to helpfulness
            }
            sort_option = sort_mapping.get(sort_by.lower(), Sort.NEWEST)

            # Use google_play_scraper to get reviews
            start_time = time.time()

            # Use the regular reviews method with pagination for better reliability
            logger.info(f"Using regular reviews method with pagination for limit: {limit}")
            result = []
            continuation_token = None
            batch_size = 100  # Max batch size for reviews method


            # Add counters for empty batches and maximum scraping time
            empty_batch_count = 0
            MAX_EMPTY_BATCHES = 5  # Stop after 5 consecutive empty batches
            max_scrape_time = 60  # Maximum 60 seconds for scraping
            start_scrape_time = time.time()



            # Keep fetching batches until we reach the limit or run out of reviews
            while len(result) < limit:
                try:
                    # Check if we've exceeded the maximum scraping time
                    if time.time() - start_scrape_time > max_scrape_time:
                        logger.warning(f"Scraping timed out after {max_scrape_time} seconds")
                        break

                    logger.info(f"Fetching batch of up to {min(batch_size, limit - len(result))} reviews (total so far: {len(result)})")
                    batch, continuation_token = reviews(
                        app_id=app_id,
                        lang='en',
                        country='us',
                        sort=sort_option,
                        count=min(batch_size, limit - len(result)),
                        continuation_token=continuation_token
                    )

                    logger.info(f"Fetched {len(batch)} reviews in this batch")

                    # Check for empty batch
                    if len(batch) == 0:
                        empty_batch_count += 1
                        logger.warning(f"Empty batch #{empty_batch_count}")
                        if empty_batch_count >= MAX_EMPTY_BATCHES:
                            logger.warning(f"Stopping after {MAX_EMPTY_BATCHES} consecutive empty batches")
                            break
                    else:
                        # Reset counter if we got some reviews
                        empty_batch_count = 0

                    result.extend(batch)

                    # If no more reviews or we've reached the limit, break
                    if not continuation_token or len(result) >= limit:
                        break

                    # Add a small delay to avoid rate limiting
                    time.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error fetching batch: {str(e)}")
                    # If we have some results already, return them
                    if result:
                        logger.warning(f"Returning partial results ({len(result)} reviews)")
                        break
                    else:
                        # If we have no results, re-raise to fall back to mock data
                        raise




            processing_time = time.time() - start_time
            logger.info(f"Play Store scraping completed in {processing_time:.2f} seconds, fetched {len(result)} reviews")

            # Format the results
            formatted_reviews = []
            for review in result:
                formatted_reviews.append({
                    "text": review['content'],
                    "rating": review['score'],
                    "author": review['userName'],
                    "date": review['at'],
                    "app_version": review.get('reviewCreatedVersion', 'Unknown'),
                    "thumbs_up": review.get('thumbsUpCount', 0),
                    "reply": review.get('replyContent', None),
                    "reply_date": review.get('repliedAt', None)
                })

            return formatted_reviews

        except Exception as e:
            logger.error(f"Error scraping Google Play Store: {str(e)}")
            logger.warning("Falling back to mock Play Store data")
            return self._get_mock_playstore_data(app_id, limit)

    def _get_mock_playstore_data(self, app_id: str, limit: int) -> List[Dict]:
        """Generate mock Play Store data for testing or when API fails"""
        mock_reviews = [
            {
                "text": "Great app, but needs more features.",
                "rating": 4,
                "author": "User1",
                "date": "2024-03-15"
            },
            {
                "text": "Crashes constantly on my device.",
                "rating": 1,
                "author": "User2",
                "date": "2024-03-14"
            },
            {
                "text": "Love the interface, very intuitive!",
                "rating": 5,
                "author": "User3",
                "date": "2024-03-13"
            },
            {
                "text": "Please fix the login issues.",
                "rating": 2,
                "author": "User4",
                "date": "2024-03-12"
            },
            {
                "text": "Would be perfect with dark mode.",
                "rating": 4,
                "author": "User5",
                "date": "2024-03-11"
            }
        ]

        # Return limited number of reviews
        return mock_reviews[:limit]

    def scrape(self, source: str, query: Optional[str] = None,
              app_id: Optional[str] = None, limit: int = 500,
              sort_by: Optional[str] = None) -> List[Dict]:
        """
        Scrape data from the specified source.

        Args:
            source: The source to scrape ("twitter" or "playstore")
            query: Search query for Twitter
            app_id: App ID for Google Play Store
            limit: Maximum number of results to return
            sort_by: Sort order for Play Store reviews ('newest', 'rating', 'helpfulness')

        Returns:
            List of dictionaries containing scraped data

        Raises:
            ValueError: If required parameters are missing or source is invalid
        """
        logger.info(f"Scraping from {source} with limit {limit}")

        if source.lower() == "twitter":
            if not query:
                raise ValueError("Query parameter is required for Twitter scraping")
            return self.scrape_twitter(query, limit)

        elif source.lower() == "playstore":
            if not app_id:
                raise ValueError("App ID parameter is required for Play Store scraping")
            return self.scrape_playstore(app_id, limit, sort_by or 'newest')

        else:
            raise ValueError("Invalid source. Supported sources are 'twitter' and 'playstore'")
