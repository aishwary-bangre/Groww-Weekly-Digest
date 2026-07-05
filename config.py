import os
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Basic application configuration
class Config:
    # Target Application
    TARGET_APP_ID = os.getenv("TARGET_APP_ID", "com.nextbillion.groww")
    TARGET_APP_NAME = "Groww"
    
    # Ingestion settings
    REVIEW_WINDOW_WEEKS = int(os.getenv("REVIEW_WINDOW_WEEKS", 8))
    
    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq") # groq, gemini
    
    # MCP Server Connections (placeholder URLs)
    DOCS_MCP_SERVER_URL = os.getenv("DOCS_MCP_SERVER_URL", "http://localhost:8001")
    GMAIL_MCP_SERVER_URL = os.getenv("GMAIL_MCP_SERVER_URL", "http://localhost:8002")

# Set up global logger
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("groww_pulse")

logger = setup_logging()
