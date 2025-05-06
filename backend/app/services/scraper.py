from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import random
import logging
import json
import os
import time
import subprocess
import tempfile
from google_play_scraper import app, Sort, reviews_all
from bs4 import BeautifulSoup
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Scraper:
    def scrape_twitter(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Scrape Twitter for tweets matching the query using snscrape.

        Args:
            query: Search query for Twitter
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing tweet data
        """
        logger.info(f"Scraping Twitter for query: {query}, limit: {limit}")

        try:
            # Create a temporary file to store the JSON output
            with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as tmp_file:
                tmp_filename = tmp_file.name

            # Build the snscrape command
            # Format: snscrape --jsonl --max-results {limit} twitter-search "{query}"
            cmd = [
                "snscrape",
                "--jsonl",
                f"--max-results={limit}",
                "twitter-search",
                f"{query}"
            ]

            # Execute the command and capture output
            logger.info(f"Executing command: {' '.join(cmd)}")
            with open(tmp_filename, 'w') as f:
                subprocess.run(cmd, stdout=f, check=True)

            # Read the results
            tweets = []
            with open(tmp_filename, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            tweet_data = json.loads(line)
                            tweets.append({
                                "text": tweet_data.get('content', ''),
                                "username": tweet_data.get('user', {}).get('username', 'unknown'),
                                "timestamp": datetime.fromisoformat(tweet_data.get('date', '').replace('Z', '+00:00')),
                                "rating": None  # Twitter doesn't have ratings
                            })
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing tweet JSON: {e}")
                        except Exception as e:
                            logger.error(f"Error processing tweet: {e}")

            # Clean up the temporary file
            os.unlink(tmp_filename)

            logger.info(f"Successfully scraped {len(tweets)} tweets")
            return tweets

        except Exception as e:
            logger.error(f"Error scraping Twitter: {str(e)}")
            logger.warning("Falling back to mock Twitter data")

            # Mock Twitter data as fallback
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
                    "timestamp": datetime.now(),
                    "rating": None  # Twitter doesn't have ratings
                })

            return tweets

    def scrape_playstore(self, app_id: str, limit: int = 50) -> List[Dict]:
        """
        Scrape Google Play Store reviews for a specific app.

        Args:
            app_id: The Google Play Store app ID
            limit: Maximum number of reviews to return

        Returns:
            List of dictionaries containing review data
        """
        logger.info(f"Scraping Google Play Store for app_id: {app_id}, limit: {limit}")

        try:
            # Get app details
            app_info = app(app_id)
            app_name = app_info.get('title', app_id)
            logger.info(f"Found app: {app_name}")

            # Get reviews
            result = reviews_all(
                app_id,
                lang='en',  # English reviews
                country='us'  # US store
            )

            # Process reviews
            reviews_list = []
            for i, review in enumerate(result):
                if i >= limit:
                    break

                # Convert timestamp from milliseconds to datetime
                timestamp = datetime.fromtimestamp(review['at'])

                reviews_list.append({
                    "text": review['content'],
                    "username": review['userName'],
                    "timestamp": timestamp,
                    "rating": review['score']  # Rating from 1-5
                })

            logger.info(f"Successfully scraped {len(reviews_list)} reviews")
            return reviews_list

        except Exception as e:
            logger.error(f"Error scraping Google Play Store: {str(e)}")
            logger.warning("Falling back to mock Play Store data")

            # Mock Play Store data as fallback
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
                    "timestamp": datetime.now(),
                    "rating": random.randint(1, 5)
                })

            return reviews_list

    def scrape(self, source: str, query: Optional[str] = None,
              app_id: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """
        Scrape data from the specified source.

        Args:
            source: The source to scrape ("twitter" or "playstore")
            query: Search query for Twitter
            app_id: App ID for Google Play Store
            limit: Maximum number of results to return

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
            return self.scrape_playstore(app_id, limit)

        else:
            raise ValueError("Invalid source. Supported sources are 'twitter' and 'playstore'")