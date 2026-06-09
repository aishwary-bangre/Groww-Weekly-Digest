# Context: Groww Weekly Review Pulse

## 1. Executive Summary
We are building an automated AI-operations (AIOps) system called the "Weekly Review Pulse." This system automatically ingests public customer reviews from the Google Play Store for the **Groww** app, processes them through an advanced NLP pipeline (Embeddings + Density-based clustering + LLM), and delivers a structured, one-page insight report directly to stakeholders.

The entire delivery mechanism is built on the **Model Context Protocol (MCP)**. Instead of the agent making direct, hard-coded API calls to Google Workspace, it communicates with dedicated MCP servers that securely handle the final writes to Google Docs and Gmail.

## 2. The Problem Statement & Objectives
Currently, product managers, customer support leads, and executives lack a fast, automated, and mathematically rigorous way to understand the thousands of reviews submitted on the Play Store every week.
- **Manual Effort:** Copy-pasting reviews into spreadsheets and trying to manually tag themes is slow and prone to bias.
- **Fragmented Insights:** Existing BI tools often provide raw sentiment scores (positive/negative) but fail to extract actionable narrative themes (e.g., "The app freezes exactly when the market opens").
- **Delivery Friction:** Reports often get lost in email attachments or Slack threads.

**Objective:** Give the Groww team a repeatable, weekly snapshot of what customers are saying: core themes, verified representative quotes, and actionable product ideas. This is delivered automatically to a canonical Google Doc, with an email "teaser" pointing to the new section.

## 3. System Workflow (The "Pulse" Lifecycle)

1. **Ingestion (The Data Funnel):**
   - The system wakes up on a schedule (e.g., Monday 8:00 AM IST).
   - It scrapes the Google Play Store for all reviews of the Groww app posted within the last 8–12 weeks.
   - It normalizes this data into a standard schema (Review ID, Rating, Text, Timestamp).

2. **Reasoning (The AI Brain):**
   - **Vectorization:** Reviews are converted into high-dimensional embeddings using `sentence-transformers`.
   - **Clustering:** To find organic topics without pre-defining them, we use `UMAP` (dimensionality reduction) and `HDBSCAN` (density-based clustering). This groups semantically similar complaints or praises together.
   - **LLM Synthesis:** We pass these clusters to an LLM (Google Gemini) to:
     - Name the theme (e.g., "Login Timeouts").
     - Extract verbatim quotes.
     - Propose actionable product/engineering solutions.
   - **Anti-Hallucination:** A strict verification step ensures any quote output by the LLM exists character-for-character in the original scraped data.

3. **Rendering & MCP Delivery:**
   - The insights are formatted into a clean Markdown payload.
   - The agent calls the **Google Docs MCP Server** to append this payload as a new, dated section to the living *Weekly Review Pulse — Groww* document.
   - The agent then calls the **Gmail MCP Server** to draft and send an email containing a high-level summary and a deep-link directly to that specific heading in the Doc.

## 4. Key Engineering Requirements
- **Strict MCP Boundary:** The agent codebase contains NO Google OAuth secrets. It relies 100% on the MCP protocol for delivery.
- **Idempotency:** If the pipeline is run twice for ISO Week 42, it will recognize that the data has already been processed and will immediately exit without duplicating Doc sections or emails.
- **Data Privacy:** PII (Personally Identifiable Information) must be scrubbed from review text *before* it is sent to external LLM APIs for summarization.

## 5. Target Audience & Value Proposition
| Audience | Value Delivered | Example Use Case |
| :--- | :--- | :--- |
| **Product Team** | Roadmap prioritization | Discovering a sudden spike in requests for advanced options chains. |
| **Customer Support** | Issue spotting | Identifying a bug causing OTP failures before it floods the support desk. |
| **Leadership** | Health snapshot | A 60-second read on general customer sentiment and app stability. |

## 6. Explicit Non-Goals
- We are **not** building a real-time streaming dashboard. The Google Doc is the living artifact.
- We are **not** scraping Twitter, Reddit, or the Apple App Store in this initial release.
- We are **not** building a generic Google Workspace integration tool; this is highly specific to the Weekly Pulse use case.
