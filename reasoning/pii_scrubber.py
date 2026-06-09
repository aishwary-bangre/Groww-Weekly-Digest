import re
import logging
from typing import List
from ingestion.models import RawReview, ProcessedReview

logger = logging.getLogger("groww_pulse.reasoning.scrubber")

class PIIScrubber:
    """Uses Regex to remove PII (Phone numbers, Emails) from raw review text."""
    
    # Matches common email formats
    EMAIL_REGEX = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    
    # Matches phone numbers (10-14 digits, optional + prefix, optional spaces/dashes)
    PHONE_REGEX = r'(\+?\d{1,3}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}'
    
    def scrub(self, reviews: List[RawReview]) -> List[ProcessedReview]:
        processed = []
        scrubbed_count = 0
        
        for review in reviews:
            original_text = review.text
            
            # Simple regex scrubbing
            text = re.sub(self.EMAIL_REGEX, '[EMAIL REDACTED]', original_text)
            text = re.sub(self.PHONE_REGEX, '[PHONE REDACTED]', text)
            
            if text != original_text:
                scrubbed_count += 1
                
            processed.append(ProcessedReview(
                review_id=review.review_id,
                score=review.score,
                text=original_text,
                at=review.at,
                app_version=review.app_version,
                scrubbed_text=text
            ))
            
        logger.info(f"PII Scrubbing complete. Redacted PII in {scrubbed_count} out of {len(reviews)} reviews.")
        
        # Save cleaned data to workspace
        import json
        import os
        dump_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cleaned_reviews.json")
        try:
            with open(dump_path, "w", encoding="utf-8") as f:
                json.dump([r.model_dump(mode='json') for r in processed], f, indent=4)
            logger.info(f"Cleaned data saved to {dump_path}")
        except Exception as e:
            logger.error(f"Failed to save cleaned data: {e}")
            
        return processed
