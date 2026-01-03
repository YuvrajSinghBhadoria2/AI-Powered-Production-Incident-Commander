import asyncpg
import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any


class PostgresStorage:
    def __init__(self, connection_url: Optional[str] = None):
        self.connection_url = connection_url or os.getenv("DATABASE_URL")
        self.pool = None

    async def initialize(self):
        """Initialize connection pool and create tables"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(self.connection_url)
        
        async with self.pool.acquire() as conn:
            # Logs table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    service TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    trace_id TEXT,
                    metadata JSONB,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Metrics table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    service TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value DOUBLE PRECISION NOT NULL,
                    unit TEXT,
                    tags JSONB,
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Incidents table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    service TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detected_by TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Postmortems table
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS postmortems (
                    incident_id TEXT PRIMARY KEY REFERENCES incidents(id),
                    summary TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    root_cause TEXT NOT NULL,
                    action_items JSONB NOT NULL,
                    monitoring_recommendations JSONB NOT NULL,
                    similar_incidents JSONB,
                    created_at TIMESTAMPTZ NOT NULL
                )
            """)
            
            # Create indexes
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_service ON logs(service)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp)")

    async def insert_log(self, log_data: Dict[str, Any]) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO logs (timestamp, service, level, message, trace_id, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """, 
                log_data['timestamp'],
                log_data['service'],
                log_data['level'],
                log_data['message'],
                log_data.get('trace_id'),
                log_data.get('metadata')
            )
            return row['id']

    async def insert_metric(self, metric_data: Dict[str, Any]) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                INSERT INTO metrics (timestamp, service, metric_name, value, unit, tags)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id
            """,
                metric_data['timestamp'],
                metric_data['service'],
                metric_data['metric_name'],
                metric_data['value'],
                metric_data.get('unit', 'count'),
                metric_data.get('tags')
            )
            return row['id']

    async def insert_incident(self, incident_data: Dict[str, Any]) -> str:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO incidents (id, timestamp, service, severity, title, description, detected_by, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                ON CONFLICT (id) DO UPDATE SET
                    timestamp = EXCLUDED.timestamp,
                    severity = EXCLUDED.severity,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    status = EXCLUDED.status
            """,
                incident_data['id'],
                incident_data['timestamp'],
                incident_data['service'],
                incident_data['severity'],
                incident_data['title'],
                incident_data['description'],
                incident_data.get('detected_by', 'anomaly_detection'),
                incident_data.get('status', 'open')
            )
            return incident_data['id']

    async def insert_postmortem(self, postmortem_data: Dict[str, Any]) -> str:
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO postmortems 
                (incident_id, summary, impact, root_cause, action_items, monitoring_recommendations, similar_incidents, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                postmortem_data['incident_id'],
                postmortem_data['summary'],
                postmortem_data['impact'],
                postmortem_data['root_cause'],
                postmortem_data['action_items'],
                postmortem_data['monitoring_recommendations'],
                postmortem_data.get('similar_incidents', []),
                postmortem_data['created_at']
            )
            return postmortem_data['incident_id']

    async def get_logs(self, start_time: datetime, end_time: datetime, service: Optional[str] = None) -> List[Dict]:
        async with self.pool.acquire() as conn:
            if service:
                rows = await conn.fetch("""
                    SELECT * FROM logs 
                    WHERE timestamp BETWEEN $1 AND $2 AND service = $3
                    ORDER BY timestamp DESC
                """, start_time, end_time, service)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM logs 
                    WHERE timestamp BETWEEN $1 AND $2
                    ORDER BY timestamp DESC
                """, start_time, end_time)
            return [dict(row) for row in rows]

    async def get_metrics(self, start_time: datetime, end_time: datetime, service: Optional[str] = None) -> List[Dict]:
        async with self.pool.acquire() as conn:
            if service:
                rows = await conn.fetch("""
                    SELECT * FROM metrics 
                    WHERE timestamp BETWEEN $1 AND $2 AND service = $3
                    ORDER BY timestamp DESC
                """, start_time, end_time, service)
            else:
                rows = await conn.fetch("""
                    SELECT * FROM metrics 
                    WHERE timestamp BETWEEN $1 AND $2
                    ORDER BY timestamp DESC
                """, start_time, end_time)
            return [dict(row) for row in rows]

    async def get_incident(self, incident_id: str) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM incidents WHERE id = $1", incident_id)
            if row:
                data = dict(row)
                # Convert back to ISO format string for consistency with SQLite implementation if needed
                # Actually, the models handle datetime objects, so keeping them as datetime is fine.
                return data
            return None

    async def get_postmortem(self, incident_id: str) -> Optional[Dict]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("SELECT * FROM postmortems WHERE incident_id = $1", incident_id)
            return dict(row) if row else None

    async def get_all_incidents(self, limit: int = 50) -> List[Dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM incidents ORDER BY timestamp DESC LIMIT $1", limit)
            return [dict(row) for row in rows]

    async def clear_all_data(self):
        async with self.pool.acquire() as conn:
            await conn.execute("TRUNCATE logs, metrics, incidents, postmortems RESTART IDENTITY CASCADE")
