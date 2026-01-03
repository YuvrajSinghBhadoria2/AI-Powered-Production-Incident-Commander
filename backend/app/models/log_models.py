from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ServiceName(str, Enum):
    PAYMENT_API = "payment-api"
    USER_SERVICE = "user-service"
    AUTH_SERVICE = "auth-service"
    DATABASE = "database"
    CACHE = "cache"
    GATEWAY = "gateway"
    # OpenTelemetry Demo services
    AD_SERVICE = "adservice"
    CART_SERVICE = "cartservice"
    CHECKOUT_SERVICE = "checkoutservice"
    CURRENCY_SERVICE = "currencyservice"
    EMAIL_SERVICE = "emailservice"
    FRONTEND = "frontend"
    PAYMENT_SERVICE = "paymentservice"
    PRODUCT_CATALOG_SERVICE = "productcatalogservice"
    RECOMMENDATION_SERVICE = "recommendationservice"
    SHIPPING_SERVICE = "shippingservice"


class LogEntry(BaseModel):
    timestamp: datetime
    service: str
    level: LogLevel
    message: str
    trace_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-02T10:00:00Z",
                "service": "payment-api",
                "level": "error",
                "message": "DB connection timeout",
                "trace_id": "abc123",
                "metadata": {"retry_count": 3}
            }
        }


class MetricEntry(BaseModel):
    timestamp: datetime
    service: str
    metric_name: str
    value: float
    unit: str = "count"
    tags: Optional[Dict[str, str]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-02T10:00:00Z",
                "service": "payment-api",
                "metric_name": "api_latency_ms",
                "value": 5000.0,
                "unit": "milliseconds",
                "tags": {"endpoint": "/checkout"}
            }
        }


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Incident(BaseModel):
    id: Optional[str] = None
    timestamp: datetime
    service: str
    severity: IncidentSeverity
    title: str
    description: str
    detected_by: str = "anomaly_detection"
    status: str = "open"
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2026-01-02T10:42:00Z",
                "service": "payment-api",
                "severity": "critical",
                "title": "API Latency Spike",
                "description": "Response time increased from 200ms to 5s"
            }
        }


class RCATimeline(BaseModel):
    timestamp: datetime
    event: str
    impact: str


class RCAOutput(BaseModel):
    incident_id: str
    root_cause: str
    timeline: List[RCATimeline]
    mitigation_steps: List[str]
    confidence_score: float = Field(ge=0.0, le=1.0)
    similar_incidents: List[str] = []


class PostmortemRequest(BaseModel):
    incident_id: str


class Postmortem(BaseModel):
    incident_id: str
    summary: str
    impact: str
    root_cause: str
    action_items: List[str]
    monitoring_recommendations: List[str]
    similar_incidents: List[str]
    created_at: datetime


class AnalyzeIncidentRequest(BaseModel):
    time_window: str = Field(
        default="last_30_min",
        description="Time window: last_15_min, last_30_min, last_1_hour, last_6_hours"
    )
    incident_id: Optional[str] = Field(default=None, description="Specific incident ID to analyze")
    services: Optional[List[str]] = None
    severity_threshold: Optional[IncidentSeverity] = IncidentSeverity.MEDIUM


class AnalyzeIncidentResponse(BaseModel):
    incidents_detected: List[Incident]
    rca_results: List[RCAOutput] = []
    analysis_time_ms: float
