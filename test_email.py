import logging
from mcp_client.gmail_client import GmailClient

# Setup basic logging to see the output
logging.basicConfig(level=logging.INFO)

print("Testing the Auto-Send feature...")

try:
    client = GmailClient()
    response = client.send_email(
        to_email="aishwarybangre@gmail.com",
        subject="🚀 Groww AI Automator: Auto-Send Test!",
        html_body="""
        <h2>It Works!</h2>
        <p>This email was sent directly by the MCP Server using the new <b>/send_email</b> endpoint.</p>
        <p>The system completely bypassed the drafts folder and sent this straight to your inbox.</p>
        """
    )
    print("Success! Check your inbox.")
except Exception as e:
    print(f"Error sending test email: {e}")
