import logging
import time
from datetime import datetime, timedelta
from typing import List, Optional

from google_play_scraper import Sort, reviews
from pydantic import ValidationError

from .models import RawReview

logger = logging.getLogger("groww_pulse.ingestion")

class GooglePlayScraper:
    def __init__(self, app_id: str):
        self.app_id = app_id

    def fetch_recent_reviews(self, weeks_back: int, max_retries: int = 3) -> List[RawReview]:
        """
        Fetches reviews from the Play Store going back the specified number of weeks.
        Handles pagination, network retries, and strictly validates the schema using Pydantic.
        """
        cutoff_date = datetime.now() - timedelta(weeks=weeks_back)
        logger.info(f"Fetching reviews for '{self.app_id}' since {cutoff_date.date()}")
        
        all_reviews: List[RawReview] = []
        continuation_token = None
        
        while True:
            batch_reviews = None
            for attempt in range(max_retries):
                try:
                    result, continuation_token = reviews(
                        self.app_id,
                        lang='en', 
                        country='in', # Targeting the Indian store for Groww
                        sort=Sort.NEWEST,
                        count=199, # Max allowed by the library per batch
                        continuation_token=continuation_token
                    )
                    batch_reviews = result
                    break # Success, exit retry loop
                except Exception as e:
                    logger.warning(f"Scraping attempt {attempt + 1} failed: {e}")
                    time.sleep(2 ** attempt) # Exponential backoff
                    
            if batch_reviews is None:
                logger.error("Max retries reached. Stopping pagination.")
                break
                
            if not batch_reviews:
                logger.info("Received empty batch. Stopping pagination.")
                break 
                
            earliest_date_in_batch = datetime.now()
            
            for review_dict in batch_reviews:
                review_date = review_dict.get('at')
                if review_date:
                    if review_date < earliest_date_in_batch:
                        earliest_date_in_batch = review_date
                        
                    # Filter by date explicitly
                    if review_date >= cutoff_date:
                        text = review_dict.get('content', '').strip()
                        # Filter out low-value generic reviews (e.g., 'good', 'worst app') by enforcing a minimum word count
                        if not text or len(text.split()) < 4:
                            continue
                            
                        # Strict Pydantic validation
                        try:
                            raw_review = RawReview(
                                review_id=review_dict.get('reviewId'),
                                score=review_dict.get('score'),
                                text=text,
                                at=review_date,
                                app_version=review_dict.get('reviewCreatedVersion')
                            )
                            all_reviews.append(raw_review)
                        except ValidationError as ve:
                            logger.debug(f"Skipping invalid review {review_dict.get('reviewId')} due to schema error: {ve}")
                            
            logger.info(f"Fetched {len(all_reviews)} valid reviews so far. Earliest in this batch: {earliest_date_in_batch.date()}")
            
            # If the earliest review in this batch is older than our cutoff, we have gone back far enough in time.
            if earliest_date_in_batch < cutoff_date:
                logger.info("Reached chronological cutoff date. Stopping pagination.")
                break
                
            if not continuation_token:
                logger.info("No continuation token returned. Reached end of available reviews.")
                break
                
        logger.info(f"Finished ingestion. Total valid reviews extracted: {len(all_reviews)}")
        
        # Save raw data to workspace
        import json
        import os
        dump_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw_scraped_reviews.json")
        try:
            with open(dump_path, "w", encoding="utf-8") as f:
                json.dump([r.model_dump(mode='json') for r in all_reviews], f, indent=4)
            logger.info(f"Raw scraped data saved to {dump_path}")
        except Exception as e:
            logger.error(f"Failed to save raw data: {e}")
            
        return all_reviews
