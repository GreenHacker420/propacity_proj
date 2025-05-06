import snscrape.modules.twitter as sntwitter
from ..api.models import Review

async def scrape_twitter(query: str, limit: int = 10) -> list[Review]:
    reviews = []
    for i, tweet in enumerate(sntwitter.TwitterSearchScraper(query).get_items()):
        if i >= limit:
            break
        reviews.append(Review(
            text=tweet.rawContent,
            rating=0.0  # Twitter doesn't have ratings, default to 0
        ))
    return reviews 