# Inbox To Task Operator

## Overview

This project is a Relationship-Aware Reply Operator that generates context-aware replies by retrieving and aggregating conversation history across multiple communication channels.

Instead of treating each message independently, the system attempts to understand:

- Who the sender is
- Where interactions happened previously
- What topics were discussed
- The user's communication style with that person
- Relevant historical context before generating a reply

The MVP focuses on:

- Cross-channel person resolution
- Retrieval-Augmented Generation (RAG)
- Context aggregation
- Tone-aware reply generation
- Human-in-the-loop review
- Learning from user edits

---

# Supported Data Sources

The system currently supports mocked historical data from:

- Email
- LinkedIn
- WhatsApp
- SMS/Text Messages

Each source has its own JSON dataset and normalization pipeline.

---

# High-Level Architecture

```text
Incoming Message
       |
       v
Source Loader
       |
       v
Normalizer
       |
       v
Person Resolution
       |
       v
Chunking + Vector Search (RAG)
       |
       v
Context Aggregation
       |
       v
Tone Profile Loader
       |
       v
Reply Generator (LLM)
       |
       v
Human Review / Edit
       |
       v
Feedback Learning
```

---

# Core Components

## 1. Source Loader

Loads communication history from all supported sources.

Responsibilities:

- Read JSON source files
- Provide raw historical communication data
- Keep source-specific formats isolated

---

## 2. Normalizer

Converts source-specific records into a common internal schema.

This allows downstream modules to work with a unified message structure regardless of source.

Example:

- Email body
- LinkedIn message
- WhatsApp text

All become:

```text
NormalizedMessage
```

---

## 3. Person Resolution

Attempts to identify whether records from different sources belong to the same person.

Signals used:

Strong signals:
- Email
- Phone number
- LinkedIn handle

Medium signals:
- Company
- Email domain

Weak signals:
- Similar names

Important behavior:

The resolver intentionally avoids merging identities based only on name similarity.

This prevents wrong-person context leakage.

---

## 4. Chunking + Retrieval (RAG)

Resolved messages are converted into searchable chunks.

The system currently uses:

- TF-IDF vectorization
- Cosine similarity search

Retrieved context is ranked using similarity scores.

Only the matched person's history is included in retrieval.

---

## 5. Context Aggregation

Builds a structured relationship summary using:

- Timeline of conversations
- Relevant retrieved context
- Open commitments
- Source information

This becomes the grounding context for reply generation.

---

## 6. Tone-Aware Reply Generation

The system sends aggregated context into an LLM provider abstraction.

Current implementation:

- Claude via Anthropic API
- Automatic fallback response if provider fails

Design goal:

Keep the rest of the architecture provider-agnostic.

---

## 7. Human-in-the-Loop Review

Generated replies are never auto-sent.

The user can:

- Approve
- Edit
- Reject

This improves reliability and trust.

---

## 8. Feedback Learning

When the user edits a reply:

- Original draft is stored
- Edited version is stored
- Tone memory is updated

Future generations can adapt toward user preferences.

---

# Logging and Observability

The operator logs every major step:

- Source loading
- Normalization
- Person resolution
- Retrieval
- Context aggregation
- Reply generation
- Human feedback

Logs are saved to:

```text
logs/run_logs.json
```

This improves:

- Debugging
- Explainability
- Reliability
- Demo visibility

---

# Test Scenarios

The system includes multiple test cases:

## HealthAI Recruiter

Demonstrates:

- Cross-channel identity resolution
- RAG retrieval
- Context-aware reply generation

---

## Same-Name Conflict

Two people share the same name:

```text
Jane Doe
```

The system avoids incorrect identity merging using stronger signals like:

- Company
- Handle
- Email
- Phone number

---

## Unknown Sender

If no reliable identity match exists:

- The system avoids retrieving unrelated history
- Falls back to using only incoming message context

This prevents privacy and context leakage issues.

---

# Running the Project

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Configure Environment Variables

Create a `.env` file:

```env
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_MODEL=claude-sonnet-4-5
```

---

## Run

```bash
python main.py
```

---

# Current Limitations

This is an MVP implementation.

Current limitations:

- Mock data sources
- No real OAuth integrations
- Local TF-IDF retrieval instead of production vector DB
- Simple tone-learning memory
- No long-term user memory
- No streaming or async orchestration

---

# Future Scalability

## Real Integrations

Potential future integrations:

- Gmail API
- LinkedIn APIs
- Slack
- Discord
- CRM systems
- Calendar systems

---

## Production Retrieval Stack

Possible upgrades:

- FAISS
- ChromaDB
- Pinecone
- pgvector
- Hybrid retrieval

---

## Multi-Agent Architecture

The current MVP uses a single orchestrator with modular components.

Future architecture could introduce specialized agents:

- Identity Agent
- Retrieval Agent
- Context Agent
- Tone Agent
- Scheduling Agent
- Negotiation Agent

---

## Better Learning Systems

Future learning improvements:

- Per-contact tone adaptation
- Reinforcement from edits
- Communication preference modeling
- Long-term memory systems
- Personalized retrieval ranking

---

## Reliability Improvements

Potential production improvements:

- Retry policies
- Multi-provider routing
- Provider failover
- Confidence scoring
- Hallucination detection
- Context filtering
- PII protection

---

# Design Philosophy

This project intentionally avoids using LLMs for deterministic operations.

LLMs are only used where reasoning and generation are valuable.

Deterministic components:

- Person resolution
- Retrieval
- Context aggregation

LLM-driven component:

- Reply generation

This hybrid design improves:

- Reliability
- Cost efficiency
- Explainability
- Scalability

---

# Summary

This project demonstrates how a relationship-aware communication operator can:

- Understand relationships across channels
- Retrieve relevant historical context
- Generate grounded replies
- Learn from user edits
- Maintain human oversight
- Avoid wrong-person context leakage

