# Project Complete: Groww Weekly Digest AI Ops Automator

The system is now fully operational, split into two decoupled architectures that securely process data and interact with Google Workspace.

## 1. The Main AI Pipeline (Local)
Located in `Groww Weekly Digest AI Ops Automator/`

This is the core engine you run once a week. 
- **Ingestion:** Scrapes the Google Play Store for the requested number of weeks (`google-play-scraper`).
- **Sanitization:** Strips out PII (emails, phone numbers) using RegEx to protect user privacy before AI processing.
- **Clustering:** Uses `all-MiniLM-L6-v2` to vectorize text, `UMAP` to reduce dimensions, and `HDBSCAN` to group identical feature requests together (dropping noise).
- **LLM Summary:** Passes the clean, dense clusters to Gemini to extract actionable themes and verbatim quotes.
- **Idempotency:** A local SQLite database tracks the `ISO_Week`. If you accidentally run the script twice in one week, it safely exits to prevent duplicate reports.

## 2. The MCP Server (Cloud)
Located at `https://mcp-server-production-c5df.up.railway.app`

Instead of giving the Main Pipeline direct access to your Google Account, we built an isolated MCP-style server.
- **Deployment:** Running on a Dockerized FastAPI container on Railway.
- **Security:** Locked behind your `MCP_API_KEY`.
- **Tools:**
  - `/append_to_doc`: Takes the Markdown insights and injects them into your Google Doc.
  - `/create_email_draft`: Generates an HTML email with a deep-link to the Doc and places it in your Gmail Drafts folder for review.

## How to Run It Every Week
Open your terminal in the Main Project folder and run:

```bash
python main.py --app com.nextbillion.groww --weeks 1 --doc-id <YOUR_REAL_GOOGLE_DOC_ID>
```
*(Make sure to use your real Gemini API key in the `.env` file instead of the Mock Summarizer when you want the real AI outputs!)*
