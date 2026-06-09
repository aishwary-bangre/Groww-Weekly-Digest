# System Architecture: Groww Weekly Review Pulse

This document outlines the architecture, data flow, component boundaries, and security model for the Groww Weekly Review Pulse. 

## 1. High-Level Architecture & Data Flow

The system is designed as a unidirectional, fault-tolerant data pipeline. It extracts unstructured data, enforces structure through ML, and delegates external side-effects (like emails) to isolated Model Context Protocol (MCP) servers.

```mermaid
flowchart TD
    subgraph Data Sources
        GP[Google Play Store API / Scraper]
    end

    subgraph The Pulse Agent Pipeline
        Ingest[Ingestion Module<br><i>google-play-scraper</i>]
        Clean[Data Sanitization<br><i>Regex / PII Scrubbing</i>]
        
        subgraph Reasoning Engine
            Embed[Vectorization<br><i>sentence-transformers</i>]
            Cluster[Density Clustering<br><i>UMAP + HDBSCAN</i>]
            LLM[Theme & Quote Extraction<br><i>Google Gemini</i>]
        end
        
        Validate[Quote Verifier<br><i>Anti-Hallucination Gate</i>]
        Render[Markdown/JSON Renderer]
    end

    subgraph MCP Boundary - Isolated
        DocsMCP[Google Docs MCP Server]
        GmailMCP[Gmail MCP Server]
    end

    subgraph Final Artifacts
        Doc[Groww Weekly Pulse Google Doc]
        Email[Stakeholder Notification Email]
    end

    GP --> Ingest
    Ingest --> Clean
    Clean --> Embed
    Embed --> Cluster
    Cluster --> LLM
    LLM --> Validate
    Validate --> Render
    
    Render -->|JSON RPC: Call Docs Tool| DocsMCP
    Render -->|JSON RPC: Call Gmail Tool| GmailMCP
    
    DocsMCP -->|REST API: docs.append| Doc
    GmailMCP -->|REST API: messages.send| Email
```

## 2. Component Design & Responsibilities

The codebase is strictly modular to ensure that swapping out an LLM provider or an ingestion source does not require a complete rewrite.

```mermaid
classDiagram
    class IngestionModule {
        +fetchPlayStoreReviews(appId, windowWeeks) List~Review~
        -normalizeData(rawData) List~Review~
    }
    class ReasoningModule {
        +scrubPII(reviews) List~Review~
        +generateEmbeddings(texts) Tensor
        +clusterReviews(embeddings) Dict~ClusterID, List~Review~~
        +extractThemes(clusters) Insights
        -validateQuotes(quotes, originalText) bool
    }
    class OutputGenerator {
        +buildDocPayload(insights) str
        +buildEmailPayload(insights, docLink) dict
    }
    class MCPClient {
        +callDocsAppend(payload) str~HeadingID~
        +callGmailSend(payload) str~MessageID~
    }
    
    IngestionModule --> ReasoningModule : Raw Review Data Classes
    ReasoningModule --> OutputGenerator : Validated Insight Data Classes
    OutputGenerator --> MCPClient : Formatted JSON/Markdown
```

## 3. Technology Stack & Rationale

| Component | Technology Choice | Rationale |
| :--- | :--- | :--- |
| **Ingestion** | `google-play-scraper` (Python) | Robust, open-source library that handles pagination and API limits effectively without requiring direct Google Developer Console credentials. |
| **Embeddings** | `sentence-transformers` | Runs locally, incredibly fast, and avoids token costs for simply clustering data prior to the heavy LLM lifting. |
| **Clustering** | `UMAP` + `HDBSCAN` | UMAP reduces high-dimensional vector space so HDBSCAN can find dense clusters of similar reviews. This is far superior to K-Means because it doesn't force outliers into clusters (HDBSCAN has a concept of "noise"). |
| **LLM Synthesis** | Google Gemini (1.5 Flash/Pro) | Chosen specifically for its massive context window (1M+ tokens), allowing us to pass entire clusters of reviews in a single prompt for accurate theme naming. |
| **Delivery** | Model Context Protocol (MCP) | Ensures the core reasoning agent is completely decoupled from Google Workspace authentication. |

## 4. MCP Integration & Security Sequence

The agent operates in a "Zero Trust" model regarding Google Workspace. It does not hold OAuth tokens.

```mermaid
sequenceDiagram
    participant Scheduler as CRON Job
    participant Agent as Pulse Agent
    participant DB as Idempotency DB (SQLite)
    participant DocsMCP as Docs MCP Server
    participant GmailMCP as Gmail MCP Server

    Scheduler->>Agent: Trigger(Groww, ISO_Week_42)
    Agent->>DB: Check if ISO_Week_42 processed
    DB-->>Agent: Not Processed
    
    Note over Agent: Executes Ingestion & Reasoning
    
    Agent->>DocsMCP: Call Tool: AppendSection(Markdown Payload)
    DocsMCP-->>Agent: Return: Success (Heading Link)
    
    Agent->>Agent: Generate Email Payload with Heading Link
    
    Agent->>GmailMCP: Call Tool: SendEmail(Recipients, HTML Payload)
    GmailMCP-->>Agent: Return: Success (Message ID)
    
    Agent->>DB: Record Success(ISO_Week_42, Heading Link, Message ID)
```
