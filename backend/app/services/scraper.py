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

    @backoff.on_exception(backoff.expo, Exception, max_tries=3)
    def scrape_playstore(self, app_id: str, limit: int = 50, sort_by: str = 'newest') -> List[Dict]:
        """
        Scrape Google Play Store reviews for a specific app.

        Args:
            app_id: The Google Play Store app ID
            limit: Maximum number of reviews to return
            sort_by: Sort order for reviews ('newest', 'rating', 'helpfulness')

        Returns:
            List of dictionaries containing review data
        """
        logger.info(f"Scraping Google Play Store for app_id: {app_id}, limit: {limit}, sort: {sort_by}")

        try:
            # Get app details with retry logic
            app_info = app(app_id)
            app_name = app_info.get('title', app_id)
            logger.info(f"Found app: {app_name}")

            # Map sort_by parameter to Sort enum
            sort_mapping = {
                'newest': Sort.NEWEST,
                'rating': Sort.RATING,
                'helpfulness': Sort.HELPFULNESS
            }
            sort_order = sort_mapping.get(sort_by.lower(), Sort.NEWEST)

            # Get reviews with pagination
            reviews_list = []
            continuation_token = None
            count = 0

            while count < limit:
                # Get a batch of reviews
                result, continuation_token = reviews(
                    app_id,
                    lang='en',  # English reviews
                    country='us',  # US store
                    sort=sort_order,
                    count=min(100, limit - count),  # Get up to 100 reviews per request
                    continuation_token=continuation_token
                )

                # Process reviews
                for review in result:
                    if count >= limit:
                        break

                    # Convert timestamp from milliseconds to datetime
                    timestamp = datetime.fromtimestamp(review['at'])

                    reviews_list.append({
                        "text": review['content'],
                        "username": review['userName'],
                        "timestamp": timestamp,
                        "rating": review['score'],  # Rating from 1-5
                        "thumbs_up": review.get('thumbsUpCount', 0),
                        "reply_content": review.get('replyContent'),
                        "app_version": review.get('reviewCreatedVersion'),
                        "app_name": app_name,
                        "app_developer": app_info.get('developer'),
                        "app_category": app_info.get('genre'),
                        "app_rating": app_info.get('score', 0),
                        "app_installs": app_info.get('installs', '0+')
                    })
                    count += 1

                # If no more reviews or no continuation token, break
                if not continuation_token or not result:
                    break

                # Add a small delay to avoid rate limiting
                time.sleep(1)

            logger.info(f"Successfully scraped {len(reviews_list)} reviews")
            return reviews_list

        except Exception as e:
            logger.error(f"Error scraping Google Play Store: {str(e)}")
            logger.warning("Falling back to mock Play Store data")
            return self._get_mock_playstore_data(app_id, limit)

    def _get_mock_playstore_data(self, app_id: str, limit: int) -> List[Dict]:
        """Generate mock Play Store data for testing or when API fails"""
        mock_reviews = [
            "Great app, but needs more features.",
            "Crashes constantly on my device.",
            "Love the interface, very intuitive!",
            "Please fix the login issues.",
            "Would be perfect with dark mode.",
            "Can't sync my data between devices.",
            "Best app in its category!",
            "Too many ads, considering uninstalling.",
            "Latest update fixed all my issues.",
            "Wish it had better offline support.",
            "The search functionality is broken.",
            "Amazing customer service!",
            "App is slow to load on older devices.",
            "Need more customization options.",
            "Worth every penny, highly recommend!"
        ]

        reviews_list = []
        for i in range(min(limit, len(mock_reviews))):
            reviews_list.append({
                "text": f"{app_id}: {mock_reviews[i]}",
                "username": f"user{i+1}",
                "timestamp": datetime.now() - timedelta(days=random.randint(1, 30)),
                "rating": random.randint(1, 5),
                "thumbs_up": random.randint(0, 100),
                "reply_content": random.choice([None, "Thank you for your feedback!", "We're working on this issue."]),
                "app_version": f"1.{random.randint(0, 9)}.{random.randint(0, 9)}",
                "app_name": f"Mock App {app_id}",
                "app_developer": "Mock Developer",
                "app_category": random.choice(["Games", "Productivity", "Social", "Tools"]),
                "app_rating": round(random.uniform(3.5, 5.0), 1),
                "app_installs": f"{random.randint(1, 10)}M+"
            })

        return reviews_list

    def scrape(self, source: str, query: Optional[str] = None,
              app_id: Optional[str] = None, limit: int = 50,
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