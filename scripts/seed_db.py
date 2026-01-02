#!/usr/bin/env python3
"""
Seed the database with historical incidents and initialize Pinecone vector index.
"""

import asyncio
import json
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.db.sqlite_storage import storage
from app.services.rag_engine import rag_engine


async def seed_historical_incidents():
    """Load historical incidents into Pinecone"""
    print("📚 Loading historical incidents...")
    
    with open("data/historical_incidents.json", "r") as f:
        incidents = json.load(f)
    
    for incident in incidents:
        print(f"  ✓ Indexing: {incident['title']}")
        await rag_engine.upsert_incident(
            incident_id=incident['id'],
            incident_data=incident
        )
    
    print(f"✅ Indexed {len(incidents)} historical incidents")


async def seed_runbooks():
    """Load runbooks into Pinecone"""
    print("📖 Loading runbooks...")
    
    with open("data/runbooks.json", "r") as f:
        runbooks = json.load(f)
    
    for runbook in runbooks:
        print(f"  ✓ Indexing: {runbook['title']}")
        await rag_engine.upsert_runbook(
            runbook_id=runbook['id'],
            runbook_data=runbook
        )
    
    print(f"✅ Indexed {len(runbooks)} runbooks")


async def main():
    print("🚀 Initializing AI Incident Commander database...")
    print()
    
    # Initialize database
    print("💾 Initializing SQLite database...")
    await storage.initialize()
    print("✅ Database initialized")
    print()
    
    # Initialize Pinecone
    print("🔍 Initializing Pinecone vector index...")
    await rag_engine.initialize()
    print("✅ Pinecone initialized")
    print()
    
    # Seed historical incidents
    await seed_historical_incidents()
    print()
    
    # Seed runbooks
    await seed_runbooks()
    print()
    
    # Get stats
    stats = await rag_engine.get_stats()
    print("📊 Pinecone Index Stats:")
    print(f"  Total vectors: {stats.get('total_vectors', 0)}")
    print(f"  Dimension: {stats.get('dimension', 0)}")
    print()
    
    print("✨ Database seeding complete!")
    print()
    print("Next steps:")
    print("  1. Generate synthetic logs: python scripts/generate_synthetic_logs.py")
    print("  2. Start the backend: cd backend && uvicorn app.main:app --reload")
    print("  3. Test the API: curl http://localhost:8000/health")


if __name__ == "__main__":
    asyncio.run(main())
