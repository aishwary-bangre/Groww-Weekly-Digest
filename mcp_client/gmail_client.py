import requests
import logging

logger = logging.getLogger("groww_pulse.mcp_client.gmail")

class GmailClient:
    def __init__(self, mcp_url: str = "https://mcp-server-production-c5df.up.railway.app"):
        self.mcp_url = mcp_url
        self.draft_endpoint = f"{mcp_url}/create_email_draft?api_key=my-super-secret-key-123"
        self.send_endpoint = f"{mcp_url}/send_email?api_key=my-super-secret-key-123"
        
    def create_draft(self, to_email: str, subject: str, html_body: str):
        logger.info(f"Sending create_draft request to MCP server for: {to_email}")
        payload = {
            "to": to_email,
            "subject": subject,
            "body": html_body
        }
        try:
            response = requests.post(self.draft_endpoint, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Successfully pushed draft to Gmail MCP.")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to push to Gmail MCP: {e}")
            raise

    def send_email(self, to_email: str, subject: str, html_body: str):
        logger.info(f"Sending send_email request to MCP server for: {to_email}")
        payload = {
            "to": to_email,
            "subject": subject,
            "body": html_body
        }
        try:
            response = requests.post(self.send_endpoint, json=payload, timeout=10)
            response.raise_for_status()
            logger.info("Successfully sent email via Gmail MCP.")
            return response.json()
        except Exception as e:
            logger.error(f"Failed to send email via Gmail MCP: {e}")
            raise
