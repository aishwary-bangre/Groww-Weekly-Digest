# Implementation Plan: Groww Weekly Review Pulse

This plan outlines the phase-by-phase implementation of the Groww Weekly Review Pulse automation. It covers everything from initial repository setup to the final MCP integrations for Google Docs and Gmail delivery.

## Proposed Phases

### Phase 1: Project Foundation & Architecture Skeleton
Set up the core repository structure, dependencies, and centralized configuration.

```text
groww-weekly-pulse/
├── config.py                 # Loads variables from .env, defines constants, logging setup
├── main.py                   # CLI entry point, scheduler logic, and pipeline orchestration
├── ingestion/
│   ├── scraper.py            # Logic to handle Google Play pagination and rate limits
│   └── models.py             # Pydantic data models for strict validation (RawReview, ProcessedReview)
├── reasoning/
│   ├── pii_scrubber.py       # Regex patterns to sanitize phone numbers, emails, etc.
│   ├── clusterer.py          # UMAP + HDBSCAN hyperparameters and distance metrics
│   └── summarizer.py         # Gemini LLM prompts, context stuffing, and JSON extraction
├── output/
│   ├── generator.py          # Logic to construct the final payload combining all insights
│   └── templates/            # Jinja2/Markdown templates for Doc sections and Emails
├── mcp_client/
│   ├── docs_client.py        # JSON-RPC payloads for Google Docs MCP tool execution
│   └── gmail_client.py       # JSON-RPC payloads for Gmail MCP tool execution
├── data/                     
│   └── idempotency.db        # SQLite database tracking ISO_Week -> Doc_Heading_Link mapping
├── requirements.txt          # Pinned project dependencies
├── .env                      # API keys (Gemini API), MCP URLs (Not committed to Git)
└── README.md                 # Setup and run instructions
```

### Phase 2: Data Ingestion (Google Play)
Focus on building a fault-tolerant ingestion pipeline that can handle dynamic date windows.
- **Library Integration:** Utilize `google-play-scraper` to pull reviews. Implement retry logic for network timeouts.
- **Date Filtering:** Write logic to filter the scraped reviews explicitly to the configured window (e.g., `datetime.now() - timedelta(weeks=8)`).
- **Data Validation:** Use strict validation (e.g., Pydantic models) to ensure every scraped review has the required fields (`id`, `score`, `text`, `at`) before passing it downstream. Discard empty reviews.

### Phase 3: Processing & Reasoning (The Core AI Engine)
Transform raw, noisy text into structured, mathematically backed insights.
- **PII Scrubbing:** Implement a fast regex pass to remove emails, phone numbers, and standard PII from the `text` field.
- **Vectorization:** Pass the scrubbed text through a lightweight local embedding model (e.g., `all-MiniLM-L6-v2` via `sentence-transformers`) to generate high-dimensional vectors.
- **Clustering Pipeline:** 
  - Apply `UMAP` to reduce the dimensionality of the vectors (making clustering faster and more accurate).
  - Apply `HDBSCAN` to find dense clusters of similar reviews. Unclustered noise will be flagged as `-1` and ignored.
- **LLM Summarization (Gemini):** Pass the raw text of the top 5 largest clusters into Google Gemini. The prompt will enforce strict JSON output: `{"theme_name": "...", "verbatim_quotes": ["..."], "action_ideas": ["..."]}`.
- **Anti-Hallucination Gate:** Write a strict Python validation function that takes every quote returned by Gemini and checks `if quote in original_review.text`. If it fails, the quote is rejected and logged.

### Phase 4: Output Rendering
Transform the verified JSON insights into the final human-readable artifacts.
- **Markdown Templating:** Use Jinja2 (or standard Python f-strings if simple enough) to populate the `templates/` with the weekly data.
- **Payload Construction:** Build the exact JSON schema required by the MCP servers. 
  - For Docs: A batch update payload structure.
  - For Gmail: An HTML formatted string containing the deep-link.

### Phase 5: MCP Integration & Orchestration
Connect the pipeline to the outside world and manage execution state.
- **MCP Client Implementations:** Write the JSON-RPC HTTP clients that send the payloads to the predefined MCP server URLs.
- **Idempotency Store:** Implement a lightweight SQLite table (`runs(iso_week_id, app_id, doc_link, status)`). Before `main.py` starts scraping, it checks this table. If the week is marked 'SUCCESS', it exits cleanly without re-running the ML models.
- **CLI Wrapper:** Wrap `main.py` in `argparse` so it can be run easily via scheduled cron jobs (e.g., `python main.py --app groww --weeks 8`).

### Phase 6: Testing & End-to-End Validation
Ensure reliability before putting the system on a cron schedule.
- **Mocked Run:** Run the entire pipeline with mocked MCP endpoints to verify the output formatting and LLM logic.
- **Quote Validation Tests:** Write Pytest unit tests specifically for the Anti-Hallucination logic.
- **Live Integration:** Perform one live run against a staging Google Doc and a test Gmail inbox to verify end-to-end delivery.

## Verification Plan

### Automated Tests
- Unit tests for the `google-play-scraper` wrapper.
- Tests ensuring `hdbscan` clusters return expected data structures.
- Tests for quote validation logic (ensuring mismatched quotes throw errors or are discarded).

### Manual Verification
- Execute a dry run of the CLI for the current week and manually review the generated Markdown narrative.
- Trigger the MCP endpoints and verify:
  1. A new section is appended to a staging Google Doc.
  2. A draft email is created (or sent to a test inbox) with the correct Deep Link.
  3. Re-running the exact same command immediately after results in an "already processed" idempotency skip.
