import argparse
import logging
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("groww_pulse")

from ingestion.scraper import GooglePlayScraper
from reasoning.pii_scrubber import PIIScrubber
from reasoning.clusterer import Clusterer
from db import check_if_week_processed, mark_week_processed
from output.generator import OutputGenerator
from mcp_client.docs_client import DocsClient
from mcp_client.gmail_client import GmailClient
import config
from reasoning.summarizer import ThemeInsight, Summarizer

def main():
    parser = argparse.ArgumentParser(description="Groww Weekly Review Pulse")
    parser.add_argument("--app", type=str, default="com.nextbillion.groww", help="The Google Play App ID")
    parser.add_argument("--weeks", type=int, default=1, help="Number of weeks of reviews to fetch")
    parser.add_argument("--doc-id", type=str, required=True, help="The target Google Document ID to write the report to")
    parser.add_argument("--email", type=str, required=True, help="Recipient email address for the Weekly Digest report")
    args = parser.parse_args()

    # Calculate ISO week for idempotency
    current_iso_week = datetime.now().strftime("%Y-W%W")
    
    logger.info(f"Starting Pulse Pipeline for {args.app} (Week: {current_iso_week})")
    
    if check_if_week_processed(current_iso_week):
        logger.info(f"Week {current_iso_week} already processed. Exiting cleanly.")
        sys.exit(0)
    
    # 2. Ingest
    logger.info("--- PHASE 2: INGESTION ---")
    scraper = GooglePlayScraper(app_id=args.app)
    raw_reviews = scraper.fetch_recent_reviews(weeks_back=args.weeks)
    
    if not raw_reviews:
        logger.warning("No reviews found. Exiting.")
        sys.exit(0)
        
    # 3. Reason (Scrub & Cluster)
    logger.info("--- PHASE 3: REASONING (Scrubbing & Clustering) ---")
    scrubber = PIIScrubber()
    cleaned_reviews = scrubber.scrub(raw_reviews)
    
    clusterer = Clusterer()
    clustered_dict = clusterer.cluster(cleaned_reviews)
    
    import os
    logger.info("--- PHASE 3.5: SUMMARIZATION ---")
    summarizer = Summarizer(api_key=os.getenv("GROQ_API_KEY"))
    insights = summarizer.summarize_clusters(clustered_dict)
    
    logger.info("--- PHASE 4: OUTPUT GENERATION ---")
    generator = OutputGenerator()
    markdown_content = generator._render_markdown_report(insights)
    email_payload_dict = generator.generate_email_payload(insights, "https://docs.google.com/document/d/" + args.doc_id, [args.email])
    
    logger.info("--- PHASE 5: MCP INTEGRATION ---")
    docs_client = DocsClient()
    docs_client.append_to_doc(args.doc_id, markdown_content)
    
    gmail_client = GmailClient()
    gmail_client.send_email(args.email, f"Groww Weekly Review Pulse: {current_iso_week}", email_payload_dict["body"])
    
    # Mark Success
    mark_week_processed(current_iso_week)
    logger.info("Pipeline completed successfully!")

if __name__ == "__main__":
    main()
