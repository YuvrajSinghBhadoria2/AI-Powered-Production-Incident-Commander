from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import defaultdict
import statistics
import uuid


class IncidentDetector:
    """
    Sliding window anomaly detection with pattern matching.
    Detects incidents based on:
    - CPU/Memory spikes
    - API latency increases
    - Database connection exhaustion
    - Error rate thresholds
    """
    
    def __init__(self):
        self.thresholds = {
            'error_rate': 0.05,  # 5% error rate
            'latency_spike_multiplier': 3.0,  # 3x normal latency
            'cpu_threshold': 85.0,  # 85% CPU
            'memory_threshold': 90.0,  # 90% memory
            'db_connections_threshold': 90,  # 90% of max connections
        }
    
    async def detect_incidents(
        self, 
        logs: List[Dict[str, Any]], 
        metrics: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Analyze logs and metrics to detect incidents.
        Returns list of detected incidents.
        """
        incidents = []
        
        # Group logs by service
        logs_by_service = self._group_by_service(logs)
        metrics_by_service = self._group_by_service(metrics)
        
        for service in set(list(logs_by_service.keys()) + list(metrics_by_service.keys())):
            service_logs = logs_by_service.get(service, [])
            service_metrics = metrics_by_service.get(service, [])
            
            # Check error rate
            error_incident = self._detect_error_spike(service, service_logs)
            if error_incident:
                incidents.append(error_incident)
            
            # Check latency spike
            latency_incident = self._detect_latency_spike(service, service_metrics)
            if latency_incident:
                incidents.append(latency_incident)
            
            # Check resource exhaustion
            resource_incident = self._detect_resource_exhaustion(service, service_metrics)
            if resource_incident:
                incidents.append(resource_incident)
            
            # Check database issues
            db_incident = self._detect_db_issues(service, service_logs, service_metrics)
            if db_incident:
                incidents.append(db_incident)
        
        return incidents
    
    def _group_by_service(self, data: List[Dict]) -> Dict[str, List[Dict]]:
        """Group data by service"""
        grouped = defaultdict(list)
        for item in data:
            grouped[item.get('service', 'unknown')].append(item)
        return dict(grouped)
    
    def _detect_error_spike(self, service: str, logs: List[Dict]) -> Optional[Dict]:
        """Detect abnormal error rates"""
        if not logs:
            return None
        
        error_count = sum(1 for log in logs if log.get('level') in ['error', 'critical'])
        error_rate = error_count / len(logs)
        
        if error_rate > self.thresholds['error_rate']:
            # Find most common error message
            error_messages = [log['message'] for log in logs if log.get('level') in ['error', 'critical']]
            most_common = max(set(error_messages), key=error_messages.count) if error_messages else "Unknown error"
            
            import hashlib
            incident_id = f"inc_{hashlib.md5(f'{service}:{most_common}'.encode()).hexdigest()[:12]}"
            
            return {
                'id': incident_id,
                'timestamp': datetime.now(),
                'service': service,
                'severity': 'critical' if error_rate > 0.2 else 'high',
                'title': f'High Error Rate in {service}',
                'description': f'Error rate: {error_rate:.1%} ({error_count}/{len(logs)} logs). Most common: {most_common[:100]}',
                'detected_by': 'error_rate_detector'
            }
        return None
    
    def _detect_latency_spike(self, service: str, metrics: List[Dict]) -> Optional[Dict]:
        """Detect API latency spikes"""
        latency_metrics = [
            m for m in metrics 
            if 'latency' in m.get('metric_name', '').lower() or 'response_time' in m.get('metric_name', '').lower()
        ]
        
        if len(latency_metrics) < 10:
            return None
        
        # Calculate baseline (first half) vs current (second half)
        mid = len(latency_metrics) // 2
        baseline_values = [m['value'] for m in latency_metrics[:mid]]
        current_values = [m['value'] for m in latency_metrics[mid:]]
        
        if not baseline_values or not current_values:
            return None
        
        baseline_avg = statistics.mean(baseline_values)
        current_avg = statistics.mean(current_values)
        
        if baseline_avg > 0 and current_avg / baseline_avg > self.thresholds['latency_spike_multiplier']:
            import hashlib
            title = f'API Latency Spike in {service}'
            incident_id = f"inc_{hashlib.md5(f'{service}:{title}'.encode()).hexdigest()[:12]}"
            return {
                'id': incident_id,
                'timestamp': datetime.now(),
                'service': service,
                'severity': 'critical' if current_avg / baseline_avg > 5 else 'high',
                'title': title,
                'description': f'Latency increased from {baseline_avg:.0f}ms to {current_avg:.0f}ms ({current_avg/baseline_avg:.1f}x increase)',
                'detected_by': 'latency_spike_detector'
            }
        return None
    
    def _detect_resource_exhaustion(self, service: str, metrics: List[Dict]) -> Optional[Dict]:
        """Detect CPU/Memory exhaustion"""
        cpu_metrics = [m for m in metrics if 'cpu' in m.get('metric_name', '').lower()]
        memory_metrics = [m for m in metrics if 'memory' in m.get('metric_name', '').lower()]
        
        # Check CPU
        if cpu_metrics:
            recent_cpu = [m['value'] for m in cpu_metrics[-5:]]  # Last 5 readings
            avg_cpu = statistics.mean(recent_cpu)
            
            if avg_cpu > self.thresholds['cpu_threshold']:
                import hashlib
                title = f'High CPU Usage in {service}'
                incident_id = f"inc_{hashlib.md5(f'{service}:{title}'.encode()).hexdigest()[:12]}"
                return {
                    'id': incident_id,
                    'timestamp': datetime.now(),
                    'service': service,
                    'severity': 'critical' if avg_cpu > 95 else 'high',
                    'title': title,
                    'description': f'CPU usage at {avg_cpu:.1f}% (threshold: {self.thresholds["cpu_threshold"]}%)',
                    'detected_by': 'resource_exhaustion_detector'
                }
        
        # Check Memory
        if memory_metrics:
            recent_memory = [m['value'] for m in memory_metrics[-5:]]
            avg_memory = statistics.mean(recent_memory)
            
            if avg_memory > self.thresholds['memory_threshold']:
                import hashlib
                title = f'High Memory Usage in {service}'
                incident_id = f"inc_{hashlib.md5(f'{service}:{title}'.encode()).hexdigest()[:12]}"
                return {
                    'id': incident_id,
                    'timestamp': datetime.now(),
                    'service': service,
                    'severity': 'critical' if avg_memory > 95 else 'high',
                    'title': title,
                    'description': f'Memory usage at {avg_memory:.1f}% (threshold: {self.thresholds["memory_threshold"]}%)',
                    'detected_by': 'resource_exhaustion_detector'
                }
        
        return None
    
    def _detect_db_issues(self, service: str, logs: List[Dict], metrics: List[Dict]) -> Optional[Dict]:
        """Detect database connection issues"""
        # Check logs for DB-related errors
        db_errors = [
            log for log in logs 
            if any(keyword in log.get('message', '').lower() 
                   for keyword in ['connection', 'timeout', 'database', 'db', 'pool'])
            and log.get('level') in ['error', 'critical']
        ]
        
        # Check metrics for connection pool exhaustion
        connection_metrics = [
            m for m in metrics 
            if 'connection' in m.get('metric_name', '').lower()
        ]
        
        if db_errors and len(db_errors) > 3:
            most_common_error = max(
                set(e['message'] for e in db_errors),
                key=lambda x: sum(1 for e in db_errors if e['message'] == x)
            )
            
            import hashlib
            title = f'Database Connection Issues in {service}'
            incident_id = f"inc_{hashlib.md5(f'{service}:{title}'.encode()).hexdigest()[:12]}"
            return {
                'id': incident_id,
                'timestamp': datetime.now(),
                'service': service,
                'severity': 'critical',
                'title': title,
                'description': f'{len(db_errors)} DB-related errors detected. Common error: {most_common_error[:150]}',
                'detected_by': 'db_issue_detector'
            }
        
        if connection_metrics:
            recent_connections = [m['value'] for m in connection_metrics[-5:]]
            avg_connections = statistics.mean(recent_connections)
            
            if avg_connections > self.thresholds['db_connections_threshold']:
                import hashlib
                title = f'Database Connection Pool Exhaustion in {service}'
                incident_id = f"inc_{hashlib.md5(f'{service}:{title}'.encode()).hexdigest()[:12]}"
                return {
                    'id': incident_id,
                    'timestamp': datetime.now(),
                    'service': service,
                    'severity': 'critical',
                    'title': title,
                    'description': f'Connection pool at {avg_connections:.0f}% capacity',
                    'detected_by': 'db_issue_detector'
                }
        
        return None


# Global instance
incident_detector = IncidentDetector()
