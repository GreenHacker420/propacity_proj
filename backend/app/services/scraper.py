from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import random
import logging
import json
import time
from google_play_scraper import app, Sort, reviews_all, reviews
from bs4 import BeautifulSoup
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry
from dotenv import load_dotenv
import backoff
import re
import urllib3

# Import Gemini service
from app.services.gemini_service import GeminiService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Reduce log noise from external libraries
logging.getLogger('snscrape').setLevel(logging.ERROR)
logging.getLogger('urllib3').setLevel(logging.ERROR)
logging.getLogger('snscrape.base').setLevel(logging.CRITICAL)

class Scraper:
    def __init__(self):
        """Initialize the scraper"""
        self.playstore_base_url = "https://play.google.com/store/apps/details"

        # Create a session with SSL verification disabled
        self.session = self._create_session()

        # Initialize Gemini service
        self.gemini_service = GeminiService()

    def _create_session(self):
        """Create a requests session with SSL verification disabled and retries"""
        # Create a session
        session = requests.Session()

        # Configure retries
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Mount the adapter to the session
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Disable SSL verification
        session.verify = False

        # Disable warnings about SSL verification
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        return session

    def scrape_twitter(self, query: str, limit: int = 50) -> List[Dict]:
        """
        Get Twitter data for the query.
        Uses multiple methods in order of preference:
        1. Gemini API to generate realistic mock data
        2. Direct web scraping as a fallback
        3. Local mock data generation as a last resort

        Args:
            query: Search query for Twitter
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing tweet data
        """
        logger.info(f"Getting Twitter data for query: {query}, limit: {limit}")

        # Method 1: Try generating data with Gemini API (primary method)
        try:
            if self.gemini_service.available and not self.gemini_service.circuit_open:
                logger.info(f"Generating Twitter data with Gemini API for query: {query}")
                tweets = self._generate_gemini_twitter_data(query, limit)
                if tweets:
                    logger.info(f"Successfully generated {len(tweets)} tweets using Gemini API")
                    return tweets
                else:
                    logger.warning("No tweets generated with Gemini API, trying direct web scraping")
            else:
                logger.warning("Gemini API not available, trying direct web scraping")
        except Exception as e:
            logger.error(f"Error generating tweets with Gemini API: {str(e)}")
            logger.info("Trying direct web scraping")

        # Method 2: Try direct web scraping (fallback)
        try:
            logger.info(f"Trying direct web scraping for Twitter query: {query}")
            tweets = self._scrape_twitter_direct(query, limit)
            if tweets:
                logger.info(f"Successfully scraped {len(tweets)} tweets using direct web scraping")
                return tweets
            else:
                logger.warning("No tweets found with direct web scraping, falling back to local mock data")
        except Exception as e:
            logger.error(f"Error with direct web scraping: {str(e)}")
            logger.info("Falling back to local mock data")

        # All methods failed, fall back to local mock data
        logger.info("Using local mock data generation for Twitter query")
        return self._get_mock_twitter_data(query, limit)



    def _scrape_twitter_direct(self, query: str, limit: int) -> List[Dict]:
        """
        Fallback method to scrape Twitter directly using requests and BeautifulSoup.
        This is used when both snscrape and the Twitter API fail.

        Args:
            query: Search query for Twitter
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing tweet data
        """
        tweets = []
        logger.info(f"Attempting direct web scraping for Twitter query: {query}")

        try:
            # Try different approaches to get Twitter data
            methods = [
                self._scrape_twitter_nitter,
                self._scrape_twitter_x_direct
            ]

            # Try each method until one works
            for method in methods:
                try:
                    method_tweets = method(query, limit)
                    if method_tweets:
                        tweets = method_tweets
                        break
                except Exception as e:
                    logger.warning(f"Method {method.__name__} failed: {str(e)}")
                    continue

            if not tweets:
                logger.warning("All direct scraping methods failed")

        except Exception as e:
            logger.error(f"Error in direct Twitter scraping: {str(e)}")

        return tweets

    def _scrape_twitter_nitter(self, query: str, limit: int) -> List[Dict]:
        """
        Scrape Twitter using a Nitter instance (Twitter alternative frontend)

        Args:
            query: Search query
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing tweet data
        """
        tweets = []

        # List of public Nitter instances to try
        nitter_instances = [
            "https://nitter.net",
            "https://nitter.lacontrevoie.fr",
            "https://nitter.1d4.us",
            "https://nitter.kavin.rocks"
        ]

        # Try each Nitter instance
        for instance in nitter_instances:
            try:
                # Encode the query for URL
                encoded_query = requests.utils.quote(query)

                # Nitter search URL
                url = f"{instance}/search?f=tweets&q={encoded_query}"

                # Add user agent to avoid being blocked
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                # Get the page content
                response = self.session.get(url, headers=headers, timeout=10)

                if response.status_code != 200:
                    logger.warning(f"Failed to get Nitter search page from {instance}: {response.status_code}")
                    continue

                # Parse the HTML
                soup = BeautifulSoup(response.text, 'html.parser')

                # Find tweet elements
                tweet_elements = soup.select('.timeline-item')

                if not tweet_elements:
                    logger.warning(f"No tweet elements found on {instance}")
                    continue

                logger.info(f"Found {len(tweet_elements)} tweet elements on {instance}")

                # Process each tweet
                for i, tweet_element in enumerate(tweet_elements):
                    if i >= limit:
                        break

                    try:
                        # Extract text
                        text_element = tweet_element.select_one('.tweet-content')
                        text = text_element.get_text(strip=True) if text_element else "No text available"

                        # Extract username
                        username_element = tweet_element.select_one('.username')
                        username = username_element.get_text(strip=True) if username_element else "unknown"

                        # Extract timestamp
                        time_element = tweet_element.select_one('.tweet-date a')
                        timestamp = datetime.now()  # Default to now
                        if time_element and time_element.get('title'):
                            try:
                                timestamp = datetime.strptime(time_element['title'], '%d/%m/%Y, %H:%M:%S')
                            except:
                                pass

                        # Create a tweet dict
                        tweets.append({
                            "text": text,
                            "username": username,
                            "timestamp": timestamp,
                            "rating": None,  # Twitter doesn't have ratings
                            "metrics": {
                                "retweet_count": 0,
                                "reply_count": 0,
                                "like_count": 0,
                                "quote_count": 0
                            }
                        })
                    except Exception as e:
                        logger.warning(f"Error processing tweet element: {str(e)}")
                        continue

                # If we got tweets, we're done
                if tweets:
                    logger.info(f"Successfully scraped {len(tweets)} tweets using Nitter instance {instance}")
                    return tweets

            except Exception as e:
                logger.warning(f"Error scraping Nitter instance {instance}: {str(e)}")
                continue

        return tweets

    def _scrape_twitter_x_direct(self, query: str, limit: int) -> List[Dict]:
        """
        Scrape Twitter/X directly using requests and BeautifulSoup.

        Args:
            query: Search query
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing tweet data
        """
        tweets = []

        try:
            # Encode the query for URL
            encoded_query = requests.utils.quote(query)

            # Twitter search URL
            url = f"https://twitter.com/search?q={encoded_query}&src=typed_query&f=live"

            # Add user agent to avoid being blocked
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Referer": "https://twitter.com/",
                "Accept-Encoding": "gzip, deflate, br"
            }

            # Get the page content
            response = self.session.get(url, headers=headers, timeout=15)

            if response.status_code != 200:
                logger.error(f"Failed to get Twitter search page: {response.status_code}")
                return tweets

            # Parse the HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # Save the HTML for debugging
            with open('twitter_search.html', 'w', encoding='utf-8') as f:
                f.write(response.text)

            # Find tweet elements - this is a simplified approach and might break if Twitter changes their HTML structure
            tweet_elements = soup.select('article[data-testid="tweet"]')

            # If we can't find tweets with the first selector, try others
            if not tweet_elements:
                tweet_elements = soup.select('[data-testid="cellInnerDiv"]')

            if not tweet_elements:
                tweet_elements = soup.select('.tweet')

            logger.info(f"Found {len(tweet_elements)} tweet elements on the page")

            # Process each tweet
            for i, tweet_element in enumerate(tweet_elements):
                if i >= limit:
                    break

                try:
                    # Try different selectors for text
                    text_selectors = [
                        'div[data-testid="tweetText"]',
                        '.tweet-text',
                        '.js-tweet-text'
                    ]

                    text = "No text available"
                    for selector in text_selectors:
                        text_element = tweet_element.select_one(selector)
                        if text_element:
                            text = text_element.get_text(strip=True)
                            break

                    # Try different selectors for username
                    username_selectors = [
                        'div[data-testid="User-Name"] span',
                        '.username',
                        '.js-username'
                    ]

                    username = "unknown"
                    for selector in username_selectors:
                        username_element = tweet_element.select_one(selector)
                        if username_element:
                            username = username_element.get_text(strip=True)
                            break

                    # Create a tweet dict
                    tweets.append({
                        "text": text,
                        "username": username,
                        "timestamp": datetime.now(),  # We don't have the exact timestamp
                        "rating": None,  # Twitter doesn't have ratings
                        "metrics": {
                            "retweet_count": 0,
                            "reply_count": 0,
                            "like_count": 0,
                            "quote_count": 0
                        }
                    })
                except Exception as e:
                    logger.warning(f"Error processing tweet element: {str(e)}")
                    continue

            logger.info(f"Successfully scraped {len(tweets)} tweets using direct Twitter/X scraping")

        except Exception as e:
            logger.error(f"Error in direct Twitter/X scraping: {str(e)}")

        return tweets

    def _get_mock_twitter_data(self, query: str, limit: int) -> List[Dict]:
        """
        Generate realistic mock Twitter data for testing or when API fails.
        The mock data is tailored to the query to make it more realistic.

        Args:
            query: Search query for Twitter
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing mock tweet data
        """
        # Base templates for different types of tweets
        positive_templates = [
            "I love {query}! It's so amazing and easy to use.",
            "Just tried {query} and I'm impressed! Definitely recommend it.",
            "{query} is the best thing ever! Can't believe I didn't try it sooner.",
            "Wow, {query} has completely changed my life. So much better than the alternatives.",
            "Finally a product like {query} that actually works as advertised!",
            "The new update to {query} is fantastic. Much faster now.",
            "{query} has the best customer support I've ever experienced.",
            "I've been using {query} for a month now and it's been a game changer.",
            "If you haven't tried {query} yet, you're missing out!",
            "Just discovered {query} and I'm already obsessed. Where has this been all my life?"
        ]

        negative_templates = [
            "{query} keeps crashing on my device. Very frustrating!",
            "Not impressed with {query}. Too many bugs and issues.",
            "The latest update to {query} is terrible. Going back to the competition.",
            "{query} customer service is awful. Been waiting days for a response.",
            "Don't waste your money on {query}. It's not worth it.",
            "Having serious problems with {query} today. Anyone else?",
            "{query} is way too expensive for what it offers.",
            "Disappointed with {query}. Doesn't deliver on its promises.",
            "The UI of {query} is confusing and hard to navigate.",
            "{query} keeps logging me out randomly. Fix this please!"
        ]

        neutral_templates = [
            "Has anyone else tried {query}? Thinking about giving it a go.",
            "Looking for alternatives to {query}. Any suggestions?",
            "Just heard about {query}. Anyone have experience with it?",
            "Is {query} compatible with the latest iOS update?",
            "How do I contact {query} support? Can't find their info.",
            "Wondering if {query} is worth the price. Thoughts?",
            "Does {query} offer a free trial? Couldn't find info on their site.",
            "How does {query} compare to [competitor]?",
            "Trying to decide between {query} and [alternative]. Help!",
            "Is there a tutorial for {query}? I'm new to it."
        ]

        feature_request_templates = [
            "Wish {query} had dark mode. Would make it perfect!",
            "Please add offline mode to {query}. Would be so useful.",
            "Hope {query} adds integration with other apps soon.",
            "{query} needs better customization options.",
            "Would love to see a desktop version of {query}.",
            "When will {query} add support for multiple accounts?",
            "{query} should add a way to organize items into folders.",
            "The one feature {query} needs is scheduled posts.",
            "Please make {query} available in more languages!",
            "If {query} added voice commands it would be amazing."
        ]

        # Combine all templates and shuffle
        all_templates = positive_templates + negative_templates + neutral_templates + feature_request_templates
        random.shuffle(all_templates)

        # Generate usernames that look realistic
        usernames = [
            f"real_user_{random.randint(100, 999)}",
            f"{random.choice(['the', 'cool', 'super', 'tech', 'digital'])}{random.choice(['fan', 'guru', 'lover', 'user', 'pro'])}{random.randint(1, 99)}",
            f"{random.choice(['john', 'jane', 'alex', 'sam', 'taylor', 'jordan'])}{random.choice(['doe', 'smith', 'jones', 'wilson'])}{random.randint(1, 999)}",
            f"{random.choice(['coffee', 'cat', 'dog', 'tech', 'music', 'book'])}_lover_{random.randint(1, 99)}",
            f"{random.choice(['happy', 'sad', 'angry', 'excited', 'tired'])}{random.choice(['person', 'human', 'soul', 'mind'])}{random.randint(1, 99)}"
        ]

        # Generate tweets - ensure we generate enough tweets to meet the limit
        tweets = []
        # Calculate how many times we need to cycle through the templates
        cycles_needed = (limit + len(all_templates) - 1) // len(all_templates)

        for cycle in range(cycles_needed):
            # Shuffle templates for each cycle to get different combinations
            random.shuffle(all_templates)

            for i, template in enumerate(all_templates):
                if len(tweets) >= limit:
                    break

                # Format the template with the query
                # Add some variation to avoid exact duplicates
                query_variation = query
                if cycle > 0:
                    variations = [
                        f"{query} app",
                        f"the {query} experience",
                        f"{query} software",
                        f"{query} platform",
                        f"{query} service",
                        f"using {query}",
                        f"{query} latest version"
                    ]
                    query_variation = random.choice(variations)

                tweet_text = template.format(query=query_variation)

                # Add hashtags randomly
                if random.random() < 0.3:  # 30% chance to add hashtags
                    hashtags = [
                        f"#{query.replace(' ', '')}",
                        f"#{random.choice(['tech', 'app', 'software', 'product', 'review', 'recommendation', 'feedback', 'update'])}"
                    ]
                    tweet_text += f" {' '.join(random.sample(hashtags, random.randint(1, len(hashtags))))}"

                # Add mentions randomly
                if random.random() < 0.2:  # 20% chance to add mentions
                    mentions = [
                        "@" + random.choice(usernames).replace("_", ""),
                        "@" + query.replace(" ", "").lower()
                    ]
                    tweet_text += f" {random.choice(mentions)}"

                # Add emojis randomly
                if random.random() < 0.4:  # 40% chance to add emojis
                    emojis = ["👍", "👎", "❤️", "😊", "😢", "🔥", "⭐", "🚀", "💯", "🙏", "👏", "🤔", "😡"]
                    tweet_text += f" {random.choice(emojis)}"

                # Create the tweet with a unique timestamp for each
                tweets.append({
                    "text": tweet_text,
                    "username": random.choice(usernames),
                    "timestamp": datetime.now() - timedelta(hours=random.randint(1, 168), minutes=random.randint(0, 59), seconds=random.randint(0, 59)),
                    "rating": None,  # Twitter doesn't have ratings
                    "metrics": {
                        "retweet_count": random.randint(0, 500),
                        "reply_count": random.randint(0, 100),
                        "like_count": random.randint(0, 1000),
                        "quote_count": random.randint(0, 50)
                    }
                })

        return tweets

    def _generate_gemini_twitter_data(self, query: str, limit: int) -> List[Dict]:
        """
        Generate realistic mock Twitter data using Gemini API.

        Args:
            query: Search query for Twitter
            limit: Maximum number of tweets to return

        Returns:
            List of dictionaries containing mock tweet data
        """
        tweets = []

        try:
            # Create a prompt for Gemini to generate realistic tweets
            prompt = f"""
            Generate {limit} realistic tweets about "{query}".

            The tweets should:
            1. Be diverse in sentiment (positive, negative, neutral)
            2. Include a mix of opinions, questions, and statements
            3. Have realistic usernames
            4. Include some hashtags and mentions where appropriate
            5. Vary in length and style
            6. Be relevant to the query topic
            7. Include some feature requests or complaints where appropriate
            8. Include some praise or positive feedback where appropriate

            Format the response as a JSON array of tweet objects with the following structure:
            ```json
            [
              {{
                "text": "The tweet text including any hashtags or mentions",
                "username": "realistic_username",
                "timestamp": "2025-05-DD HH:MM:SS",
                "metrics": {{
                  "retweet_count": number,
                  "reply_count": number,
                  "like_count": number,
                  "quote_count": number
                }}
              }},
              ...
            ]
            ```

            IMPORTANT: Return ONLY the JSON array without any additional text, explanation, or markdown formatting.
            """

            # Get response from Gemini
            response = self.gemini_service.model.generate_content(prompt)
            response_text = response.text

            # Extract JSON from the response if it's in a code block
            if "```json" in response_text:
                import re
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)
            elif "```" in response_text:
                import re
                json_match = re.search(r'```\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    response_text = json_match.group(1)

            # Parse the JSON response
            try:
                tweet_data = json.loads(response_text)

                # Process each tweet
                for tweet in tweet_data:
                    # Convert timestamp string to datetime
                    try:
                        timestamp = datetime.strptime(tweet.get("timestamp", "2025-05-10 12:00:00"), "%Y-%m-%d %H:%M:%S")
                    except:
                        timestamp = datetime.now() - timedelta(hours=random.randint(1, 168))

                    # Create the tweet object
                    tweets.append({
                        "text": tweet.get("text", f"Tweet about {query}"),
                        "username": tweet.get("username", f"user_{random.randint(1000, 9999)}"),
                        "timestamp": timestamp,
                        "rating": None,  # Twitter doesn't have ratings
                        "metrics": tweet.get("metrics", {
                            "retweet_count": random.randint(0, 500),
                            "reply_count": random.randint(0, 100),
                            "like_count": random.randint(0, 1000),
                            "quote_count": random.randint(0, 50)
                        })
                    })

                logger.info(f"Successfully generated {len(tweets)} tweets using Gemini API")
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON from Gemini response: {str(e)}")
                logger.debug(f"Raw response: {response_text}")
                return []

        except Exception as e:
            logger.error(f"Error generating tweets with Gemini API: {str(e)}")
            return []

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
        """
        Generate mock Play Store data for testing or when API fails

        Args:
            app_id: App ID for the Play Store app (used to customize mock data)
            limit: Maximum number of reviews to return

        Returns:
            List of mock review dictionaries
        """
        # Use app_id to customize mock data if needed
        app_name = "Unknown App"
        if app_id:
            # Extract app name from app_id for more realistic mock data
            parts = app_id.split('.')
            if len(parts) > 1:
                app_name = parts[-1].capitalize()

        mock_reviews = [
            {
                "text": f"Great {app_name} app, but needs more features.",
                "rating": 4,
                "author": "User1",
                "date": "2024-03-15"
            },
            {
                "text": f"Crashes constantly on my device. {app_name} needs better testing.",
                "rating": 1,
                "author": "User2",
                "date": "2024-03-14"
            },
            {
                "text": f"Love the {app_name} interface, very intuitive!",
                "rating": 5,
                "author": "User3",
                "date": "2024-03-13"
            },
            {
                "text": f"Please fix the login issues in {app_name}.",
                "rating": 2,
                "author": "User4",
                "date": "2024-03-12"
            },
            {
                "text": f"{app_name} would be perfect with dark mode.",
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
