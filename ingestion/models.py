from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class RawReview(BaseModel):
    """Represents a raw review extracted from the Google Play Store."""
    review_id: str = Field(..., description="Unique identifier for the review")
    score: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    text: str = Field(..., description="The textual content of the review")
    at: datetime = Field(..., description="Timestamp of the review")
    app_version: Optional[str] = None

class ProcessedReview(RawReview):
    """Represents a review that has been scrubbed of PII and is ready for ML processing."""
    scrubbed_text: str = Field(..., description="Text with PII removed")
    cluster_id: Optional[int] = Field(default=None, description="HDBSCAN cluster assignment (-1 means noise)")
