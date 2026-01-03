import aiosqlite
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


class SQLiteStorage:
    def __init__(self, db_path: Optional[str] = None):
        if db_path is None:
            # Set default path relative to project root
            base_dir = Path(__file__).parent.parent.parent.parent
            self.db_path = str(base_dir / "backend" / "data" / "incidents.db")
        else:
            self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """Create tables if they don't exist"""
        async with aiosqlite.connect(self.db_path) as db:
            # Logs table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    service TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL,
                    trace_id TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Metrics table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    service TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Incidents table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    service TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    detected_by TEXT,
                    status TEXT DEFAULT 'open',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Postmortems table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS postmortems (
                    incident_id TEXT PRIMARY KEY,
                    summary TEXT NOT NULL,
                    impact TEXT NOT NULL,
                    root_cause TEXT NOT NULL,
                    action_items TEXT NOT NULL,
                    monitoring_recommendations TEXT NOT NULL,
                    similar_incidents TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (incident_id) REFERENCES incidents(id)
                )
            """)
            
            # Create indexes for performance
            await db.execute("CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_logs_service ON logs(service)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_incidents_timestamp ON incidents(timestamp)")
            
            await db.commit()
    
    async def insert_log(self, log_data: Dict[str, Any]) -> int:
        """Insert a log entry"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO logs (timestamp, service, level, message, trace_id, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                log_data['timestamp'].isoformat(),
                log_data['service'],
                log_data['level'],
                log_data['message'],
                log_data.get('trace_id'),
                json.dumps(log_data.get('metadata')) if log_data.get('metadata') else None
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def insert_metric(self, metric_data: Dict[str, Any]) -> int:
        """Insert a metric entry"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                INSERT INTO metrics (timestamp, service, metric_name, value, unit, tags)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metric_data['timestamp'].isoformat(),
                metric_data['service'],
                metric_data['metric_name'],
                metric_data['value'],
                metric_data.get('unit', 'count'),
                json.dumps(metric_data.get('tags')) if metric_data.get('tags') else None
            ))
            await db.commit()
            return cursor.lastrowid
    
    async def insert_incident(self, incident_data: Dict[str, Any]) -> str:
        """Insert an incident (idempotent)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT OR REPLACE INTO incidents (id, timestamp, service, severity, title, description, detected_by, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                incident_data['id'],
                incident_data['timestamp'].isoformat(),
                incident_data['service'],
                incident_data['severity'],
                incident_data['title'],
                incident_data['description'],
                incident_data.get('detected_by', 'anomaly_detection'),
                incident_data.get('status', 'open')
            ))
            await db.commit()
            return incident_data['id']
    
    async def insert_postmortem(self, postmortem_data: Dict[str, Any]) -> str:
        """Insert a postmortem"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO postmortems 
                (incident_id, summary, impact, root_cause, action_items, monitoring_recommendations, similar_incidents, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                postmortem_data['incident_id'],
                postmortem_data['summary'],
                postmortem_data['impact'],
                postmortem_data['root_cause'],
                json.dumps(postmortem_data['action_items']),
                json.dumps(postmortem_data['monitoring_recommendations']),
                json.dumps(postmortem_data.get('similar_incidents', [])),
                postmortem_data['created_at'].isoformat()
            ))
            await db.commit()
            return postmortem_data['incident_id']
    
    async def get_logs(self, start_time: datetime, end_time: datetime, service: Optional[str] = None) -> List[Dict]:
        """Retrieve logs within time window"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM logs WHERE timestamp BETWEEN ? AND ?"
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if service:
                query += " AND service = ?"
                params.append(service)
            
            query += " ORDER BY timestamp DESC"
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_metrics(self, start_time: datetime, end_time: datetime, service: Optional[str] = None) -> List[Dict]:
        """Retrieve metrics within time window"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            query = "SELECT * FROM metrics WHERE timestamp BETWEEN ? AND ?"
            params = [start_time.isoformat(), end_time.isoformat()]
            
            if service:
                query += " AND service = ?"
                params.append(service)
            
            query += " ORDER BY timestamp DESC"
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def get_incident(self, incident_id: str) -> Optional[Dict]:
        """Get incident by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None
    
    async def get_postmortem(self, incident_id: str) -> Optional[Dict]:
        """Get postmortem by incident ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM postmortems WHERE incident_id = ?", (incident_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    data = dict(row)
                    # Parse JSON fields
                    data['action_items'] = json.loads(data['action_items'])
                    data['monitoring_recommendations'] = json.loads(data['monitoring_recommendations'])
                    data['similar_incidents'] = json.loads(data.get('similar_incidents', '[]'))
                    return data
                return None
    
    async def get_all_incidents(self, limit: int = 50) -> List[Dict]:
        """Get recent incidents"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM incidents ORDER BY timestamp DESC LIMIT ?", 
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]


    async def clear_all_data(self):
        """Clear all tables (logs, metrics, incidents, postmortems)"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DELETE FROM logs")
            await db.execute("DELETE FROM metrics")
            await db.execute("DELETE FROM incidents")
            await db.execute("DELETE FROM postmortems")
            await db.commit()


# Global instance
storage = SQLiteStorage()
