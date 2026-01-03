# AI Incident Commander - Quick Testing Guide

## Step 1: Generate Synthetic Incident Data

This creates realistic incident scenarios with logs and metrics.

```bash
cd /Users/apple/Documents/Production\ issue/ai-incident-commander
source backend/venv/bin/activate
export $(cat backend/.env | xargs)
python scripts/generate_synthetic_logs.py
```

**What this creates:**
- `data/synthetic_logs.json` - 1000+ log entries showing a database connection pool exhaustion
- `data/synthetic_metrics.json` - 500+ metric data points showing resource usage

## Step 2: Ingest the Synthetic Data

Load the generated logs and metrics into the database.

```bash
python scripts/ingest_synthetic_data.py
```

Or manually via API:
```bash
# Ingest logs
curl -X POST http://localhost:8000/ingest/logs/batch \
  -H "Content-Type: application/json" \
  -d @data/synthetic_logs.json

# Ingest metrics
curl -X POST http://localhost:8000/ingest/metrics/batch \
  -H "Content-Type: application/json" \
  -d @data/synthetic_metrics.json
```

## Step 3: Run Incident Analysis

### Option A: Via Dashboard (Recommended)
1. Open http://localhost:3000 in your browser
2. Select "Last 30 minutes" from the time window dropdown
3. Click "Run Analysis" button
4. Watch the AI analyze the incident in real-time!

### Option B: Via API
```bash
curl -X POST http://localhost:8000/analyze/incident \
  -H "Content-Type: application/json" \
  -d '{
    "time_window": "last_30_min",
    "services": ["payment-api"],
    "severity_threshold": "medium"
  }' | json_pp
```

## Step 4: View Results

The dashboard will show:
- **Incident detected**: Database Connection Pool Exhaustion
- **Root Cause**: Connection pool at max capacity (100/100)
- **Timeline**: When errors started, peaked, and recovered
- **Similar Past Incidents**: Historical matches from Pinecone
- **Mitigation Steps**: AI-generated fix suggestions
- **Confidence Score**: How certain the AI is

## Expected Output Example

```json
{
  "incidents_detected": [
    {
      "service": "payment-api",
      "severity": "critical",
      "title": "Database Connection Pool Exhaustion",
      "description": "Connection pool reached maximum capacity"
    }
  ],
  "rca_results": {
    "root_cause": "Database connection pool exhausted at 100 connections...",
    "confidence_score": 0.92,
    "timeline": [
      {
        "timestamp": "2026-01-02T10:00:00Z",
        "event": "Normal operation - 50 connections",
        "impact": "none"
      },
      {
        "timestamp": "2026-01-02T10:15:00Z",
        "event": "Traffic spike - connections climbing",
        "impact": "increasing latency"
      }
    ],
    "mitigation_steps": [
      "Immediate: Restart connection pool",
      "Short-term: Increase max connections to 200",
      "Long-term: Add connection pool monitoring"
    ]
  }
}
```

## Troubleshooting

**No incidents detected?**
- Check time window matches when synthetic data was generated
- Verify logs were ingested: `curl http://localhost:8000/analyze/incidents`

**Analysis fails?**
- Check backend logs in terminal
- Verify Groq API key is valid: `echo $GROQ_API_KEY`
- Ensure Pinecone is connected: `curl http://localhost:8000/health`

**Frontend not updating?**
- Check browser console for errors (F12)
- Verify API URL in frontend/.env.local
