from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime
import re


class ContextCompressor:
    """
    Reduces 10k+ logs to ~30 critical signals using:
    - Error clustering by service and type
    - Temporal correlation analysis
    - Severity-based filtering
    """
    
    def __init__(self, target_signals: int = 30):
        self.target_signals = target_signals
    
    async def compress(self, logs: List[Dict[str, Any]], metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compress logs and metrics into critical signals.
        Returns compressed context suitable for LLM input.
        """
        # Step 1: Filter by severity
        critical_logs = self._filter_by_severity(logs)
        
        # Step 2: Cluster errors by type
        error_clusters = self._cluster_errors(critical_logs)
        
        # Step 3: Extract temporal patterns
        temporal_patterns = self._extract_temporal_patterns(critical_logs, metrics)
        
        # Step 4: Identify anomalous metrics
        anomalous_metrics = self._identify_anomalous_metrics(metrics)
        
        # Step 5: Create compressed summary
        compressed = {
            'total_logs_analyzed': len(logs),
            'critical_log_count': len(critical_logs),
            'error_clusters': error_clusters[:10],  # Top 10 error types
            'temporal_patterns': temporal_patterns,
            'anomalous_metrics': anomalous_metrics[:10],  # Top 10 anomalies
            'time_window': self._get_time_window(logs),
            'affected_services': list(set(log.get('service') for log in critical_logs))
        }
        
        return compressed
    
    def _filter_by_severity(self, logs: List[Dict]) -> List[Dict]:
        """Keep only ERROR and CRITICAL level logs"""
        return [log for log in logs if log.get('level') in ['error', 'critical']]
    
    def _cluster_errors(self, logs: List[Dict]) -> List[Dict[str, Any]]:
        """
        Group similar errors together.
        Returns list of error clusters with count and representative message.
        """
        # Group by service and error pattern
        clusters = defaultdict(list)
        
        for log in logs:
            service = log.get('service', 'unknown')
            message = log.get('message', '')
            
            # Extract error pattern (remove numbers, IDs, timestamps)
            pattern = self._extract_error_pattern(message)
            key = f"{service}::{pattern}"
            clusters[key].append(log)
        
        # Convert to sorted list
        cluster_list = []
        for key, cluster_logs in clusters.items():
            service, pattern = key.split('::', 1)
            cluster_list.append({
                'service': service,
                'error_pattern': pattern,
                'count': len(cluster_logs),
                'first_seen': min(log['timestamp'] for log in cluster_logs),
                'last_seen': max(log['timestamp'] for log in cluster_logs),
                'sample_message': cluster_logs[0]['message'][:200]
            })
        
        # Sort by count (most frequent first)
        cluster_list.sort(key=lambda x: x['count'], reverse=True)
        return cluster_list
    
    def _extract_error_pattern(self, message: str) -> str:
        """
        Extract error pattern by removing variable parts.
        E.g., "Connection timeout after 30s" -> "Connection timeout after Xs"
        """
        # Remove numbers
        pattern = re.sub(r'\d+', 'X', message)
        # Remove UUIDs and IDs
        pattern = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', pattern, flags=re.IGNORECASE)
        # Remove hex values
        pattern = re.sub(r'0x[a-f0-9]+', '0xHEX', pattern, flags=re.IGNORECASE)
        # Truncate to first 100 chars
        return pattern[:100]
    
    def _extract_temporal_patterns(self, logs: List[Dict], metrics: List[Dict]) -> Dict[str, Any]:
        """
        Identify temporal correlations between events.
        """
        if not logs:
            return {}
        
        # Sort logs by timestamp
        sorted_logs = sorted(logs, key=lambda x: x.get('timestamp', ''))
        
        # Find time of first error
        first_error_time = sorted_logs[0].get('timestamp') if sorted_logs else None
        
        # Count errors per minute
        error_timeline = defaultdict(int)
        for log in sorted_logs:
            timestamp = log.get('timestamp', '')
            if isinstance(timestamp, str):
                minute = timestamp[:16]  # YYYY-MM-DDTHH:MM
                error_timeline[minute] += 1
        
        # Find peak error time
        peak_time = max(error_timeline.items(), key=lambda x: x[1]) if error_timeline else (None, 0)
        
        return {
            'first_error_timestamp': str(first_error_time) if first_error_time else None,
            'peak_error_time': peak_time[0],
            'peak_error_count': peak_time[1],
            'error_duration_minutes': len(error_timeline),
            'total_error_events': sum(error_timeline.values())
        }
    
    def _identify_anomalous_metrics(self, metrics: List[Dict]) -> List[Dict[str, Any]]:
        """
        Identify metrics with unusual values.
        """
        if not metrics:
            return []
        
        # Group metrics by name
        metrics_by_name = defaultdict(list)
        for metric in metrics:
            metrics_by_name[metric.get('metric_name', 'unknown')].append(metric)
        
        anomalies = []
        for metric_name, metric_list in metrics_by_name.items():
            if len(metric_list) < 5:
                continue
            
            values = [m['value'] for m in metric_list]
            avg = sum(values) / len(values)
            max_val = max(values)
            min_val = min(values)
            
            # Check for spikes (max > 2x average)
            if avg > 0 and max_val / avg > 2.0:
                anomalies.append({
                    'metric_name': metric_name,
                    'service': metric_list[0].get('service', 'unknown'),
                    'anomaly_type': 'spike',
                    'baseline_avg': round(avg, 2),
                    'peak_value': round(max_val, 2),
                    'spike_multiplier': round(max_val / avg, 2),
                    'timestamp': max((m for m in metric_list if m['value'] == max_val), key=lambda x: x['timestamp'])['timestamp']
                })
            
            # Check for drops (min < 0.5x average and avg > 0)
            elif avg > 0 and min_val / avg < 0.5:
                anomalies.append({
                    'metric_name': metric_name,
                    'service': metric_list[0].get('service', 'unknown'),
                    'anomaly_type': 'drop',
                    'baseline_avg': round(avg, 2),
                    'min_value': round(min_val, 2),
                    'drop_percentage': round((1 - min_val / avg) * 100, 1),
                    'timestamp': min((m for m in metric_list if m['value'] == min_val), key=lambda x: x['timestamp'])['timestamp']
                })
        
        # Sort by severity (spike multiplier or drop percentage)
        anomalies.sort(key=lambda x: x.get('spike_multiplier', 0) + x.get('drop_percentage', 0) / 100, reverse=True)
        return anomalies
    
    def _get_time_window(self, logs: List[Dict]) -> Dict[str, str]:
        """Get start and end time of log window"""
        if not logs:
            return {'start': None, 'end': None}
        
        timestamps = [log.get('timestamp') for log in logs if log.get('timestamp')]
        if not timestamps:
            return {'start': None, 'end': None}
        
        return {
            'start': str(min(timestamps)),
            'end': str(max(timestamps))
        }


# Global instance
context_compressor = ContextCompressor()
