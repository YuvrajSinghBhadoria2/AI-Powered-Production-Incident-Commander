# AI-Powered-Production-Incident-Commander

A production-grade AI system that detects, analyzes, and mitigates real production incidents using LLM-powered root cause analysis, acting like a junior SRE on-call.

## 🚀 Features

- **Intelligent Incident Detection**: Sliding window anomaly detection with pattern matching
- **Root Cause Analysis**: Multi-step LLM reasoning for timeline reconstruction and hypothesis validation
- **Context Compression**: Reduces 10k+ logs to ~30 critical signals
- **RAG-Powered Insights**: Retrieves historical incidents and runbooks using Pinecone vector search
- **Auto-Generated Postmortems**: Structured incident reports with impact analysis and action items
- **Real-Time Dashboard**: Interactive timeline visualization and chat-style RCA interface

## 🏗️ Architecture

```
┌─────────────────┐
│   Next.js UI    │ ← Timeline + RCA Chat + Filters
└────────┬────────┘
         │
    ┌────▼─────────────────────────────────────┐
    │         FastAPI Backend                  │
    ├──────────────────────────────────────────┤
    │ • Log/Metrics Ingestion                  │
    │ • Incident Detection (Anomaly)           │
    │ • Context Compression (10k→30 signals)   │
    │ • RAG Engine (Pinecone Vector Search)    │
    │ • LLM RCA (Groq/Mixtral)                 │
    │ • Postmortem Generator                   │
    └──┬───────────────────┬──────────────┬────┘
       │                   │              │
   ┌───▼────┐         ┌────▼─────┐   ┌───▼──────┐
   │ SQLite │         │ Pinecone │   │   Groq   │
   │  Logs  │         │  Vectors │   │   LLM    │
   └────────┘         └──────────┘   └──────────┘
```

## 🛠️ Tech Stack

**Backend**: FastAPI, Python 3.11+, aiosqlite  
**Frontend**: Next.js 14 (App Router), TailwindCSS, Recharts  
**AI Stack**:
- LLM: Groq (Mixtral-8x7B) - Free tier
- Embeddings: sentence-transformers/all-MiniLM-L6-v2
- Vector Store: Pinecone (Serverless) - Free tier

**Storage**: SQLite (local dev) / PostgreSQL (production)  
**Observability**: OpenTelemetry

## 📋 Prerequisites

- Python 3.11+
- Node.js 18+
- Groq API Key (free): https://console.groq.com/
- Pinecone API Key (free): https://www.pinecone.io/

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="your-groq-api-key"
export PINECONE_API_KEY="your-pinecone-api-key"
export PINECONE_ENVIRONMENT="us-east-1"  # or your region

# Initialize database and seed data
python scripts/seed_db.py

# Run server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Visit http://localhost:3000

## 📊 API Endpoints

### Ingest Logs
```http
POST /ingest/logs
Content-Type: application/json

{
  "timestamp": "2026-01-02T10:00:00Z",
  "service": "payment-api",
  "level": "error",
  "message": "DB connection timeout"
}
```

### Analyze Incident
```http
POST /analyze/incident
Content-Type: application/json

{
  "time_window": "last_30_min",
  "services": ["payment-api"]
}
```

### Get Postmortem
```http
GET /postmortem/{incident_id}
```

## 🧪 Testing with Synthetic Data

Generate realistic incidents for testing:

```bash
python scripts/generate_synthetic_logs.py
```

This creates incidents like:
- Memory leaks
- Database connection exhaustion
- API latency spikes
- Network timeouts

## 🐳 Docker Deployment

```bash
docker-compose up -d
```

Services:
- Backend: http://localhost:8000
- Frontend: http://localhost:3000

## 📈 Performance

- Log ingestion: < 100ms per batch (100 logs)
- Incident detection: < 2s for 30-minute window
- Context compression: 10k logs → 30 signals in < 5s
- RAG retrieval (Pinecone): < 100ms
- LLM RCA generation: < 10s
- **End-to-end analysis: < 15s**

## 🔒 Security

- Strict system prompts prevent prompt injection
- Rate limiting on API endpoints
- No user input directly passed to LLM without sanitization
- Environment-based secrets management

## 🎯 Use Case Example

**Question**: "Why did API latency spike at 10:42 PM?"

**AI Response**:
1. **What broke**: Payment API response time increased from 200ms to 5s
2. **Why it broke**: Database connection pool exhausted (max 100 connections reached)
3. **How to fix**: 
   - Immediate: Restart DB connection pool
   - Short-term: Increase max connections to 200
   - Long-term: Implement connection pooling with retry logic
4. **Monitor**: Set alert on DB connections > 80

## 📝 Project Structure

```
ai-incident-commander/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/         # API endpoints
│   │   ├── models/         # Pydantic models
│   │   ├── services/       # Business logic
│   │   └── db/            # Database layer
│   └── requirements.txt
├── frontend/
│   ├── app/
│   │   ├── page.tsx
│   │   └── components/
│   └── package.json
├── data/                  # Historical incidents & runbooks
├── scripts/               # Utilities & seed scripts
└── prompts/              # LLM prompt templates
```

## 📄 License

MIT

