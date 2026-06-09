# Groww Weekly Review Pulse

An automated AI-operations system that ingests public Google Play Store reviews for the Groww app, processes them through an advanced NLP pipeline (Embeddings + Density-based clustering + Google Gemini LLM), and delivers a structured insight report to stakeholders via Google Workspace using Model Context Protocol (MCP).

## Architecture

See [Architecture.md](Architecture.md) for detailed system flow and diagrams.

## Setup

1. Create a Python virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` (if applicable) and fill in your API keys (like `GEMINI_API_KEY`) and MCP Server URLs.

## Usage

To run the pipeline manually via CLI:
```bash
python main.py --app com.nextbillion.groww --weeks 8
```
