import requests
import logging

logger = logging.getLogger("groww_pulse.mcp_client.docs")

class DocsClient:
    def __init__(self, mcp_url: str = "https://mcp-server-production-c5df.up.railway.app"):
        self.mcp_url = mcp_url
        self.endpoint = f"{mcp_url}/append_to_doc?api_key=my-super-secret-key-123"
        
    def append_to_doc(self, doc_id: str, markdown_content: str):
        logger.info(f"Sending append request to MCP server for Doc ID: {doc_id}")
        payload = {
            "doc_id": doc_id,
            "content": markdown_content
        }
        try:
            response = requests.post(self.endpoint, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Successfully pushed content to Google Docs MCP.")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to push to Docs MCP: {e}")
            raise
