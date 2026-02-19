"""
Modelos de datos para CRM en Elasticsearch.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Optional
import uuid


@dataclass
class Customer:
    """
    Modelo de cliente para Elasticsearch.
    
    Mapeo optimizado para búsquedas y agregaciones.
    """
    customer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    status: str = "lead"  # lead, prospect, customer, inactive, champion
    source: str = "unknown"  # website, referral, campaign, direct
    tags: list[str] = field(default_factory=list)
    
    # Scoring y segmentación
    lead_score: int = 0
    engagement_score: int = 0
    lifetime_value: float = 0.0
    
    # Fechas importantes
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    last_contacted_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    
    # Metadata adicional
    custom_fields: dict[str, Any] = field(default_factory=dict)
    
    # IDs relacionados para joins
    assigned_agent_id: Optional[str] = None
    current_opportunity_id: Optional[str] = None

    def to_dict(self) -> dict:
        """Convierte a diccionario para indexar en Elastic."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.last_contacted_at:
            data["last_contacted_at"] = self.last_contacted_at.isoformat()
        if self.converted_at:
            data["converted_at"] = self.converted_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Customer":
        """Crea instancia desde diccionario de Elastic."""
        data = data.copy()
        if "created_at" in data and isinstance(data["created_at"], str):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data and isinstance(data["updated_at"], str):
            data["updated_at"] = datetime.fromisoformat(data["updated_at"])
        if "last_contacted_at" in data and data["last_contacted_at"]:
            data["last_contacted_at"] = datetime.fromisoformat(data["last_contacted_at"])
        if "converted_at" in data and data["converted_at"]:
            data["converted_at"] = datetime.fromisoformat(data["converted_at"])
        return cls(**data)

    @staticmethod
    def get_mapping() -> dict:
        """Retorna mapping de Elasticsearch para este modelo."""
        return {
            "mappings": {
                "properties": {
                    "customer_id": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "email": {"type": "keyword"},
                    "phone": {"type": "keyword"},
                    "company": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "status": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "lead_score": {"type": "integer"},
                    "engagement_score": {"type": "integer"},
                    "lifetime_value": {"type": "float"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "last_contacted_at": {"type": "date"},
                    "converted_at": {"type": "date"},
                    "custom_fields": {"type": "object"},
                    "assigned_agent_id": {"type": "keyword"},
                    "current_opportunity_id": {"type": "keyword"},
                }
            },
            "settings": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
                "analysis": {
                    "analyzer": {
                        "email_analyzer": {
                            "type": "custom",
                            "tokenizer": "uax_url_email"
                        }
                    }
                }
            }
        }


@dataclass
class Ticket:
    """
    Modelo de ticket de soporte para Elasticsearch.
    """
    ticket_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    subject: str = ""
    description: str = ""
    status: str = "open"  # open, in_progress, pending, resolved, closed
    priority: str = "medium"  # low, medium, high, critical
    category: str = "general"
    subcategory: Optional[str] = None
    
    # Asignación
    assigned_to: Optional[str] = None
    escalated: bool = False
    escalation_level: int = 0
    
    # SLA
    sla_deadline: Optional[datetime] = None
    first_response_time: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Satisfacción
    satisfaction_score: Optional[int] = None
    satisfaction_comment: Optional[str] = None
    
    # Timeline
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Canal de origen
    channel: str = "email"  # email, chat, phone, web

    def to_dict(self) -> dict:
        """Convierte a diccionario para indexar."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        if self.sla_deadline:
            data["sla_deadline"] = self.sla_deadline.isoformat()
        if self.first_response_time:
            data["first_response_time"] = self.first_response_time.isoformat()
        if self.resolved_at:
            data["resolved_at"] = self.resolved_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Ticket":
        """Crea instancia desde diccionario."""
        data = data.copy()
        for date_field in ["created_at", "updated_at", "sla_deadline", 
                          "first_response_time", "resolved_at"]:
            if date_field in data and data[date_field]:
                data[date_field] = datetime.fromisoformat(data[date_field])
        return cls(**data)

    @staticmethod
    def get_mapping() -> dict:
        """Retorna mapping de Elasticsearch."""
        return {
            "mappings": {
                "properties": {
                    "ticket_id": {"type": "keyword"},
                    "customer_id": {"type": "keyword"},
                    "subject": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "description": {"type": "text"},
                    "status": {"type": "keyword"},
                    "priority": {"type": "keyword"},
                    "category": {"type": "keyword"},
                    "subcategory": {"type": "keyword"},
                    "assigned_to": {"type": "keyword"},
                    "escalated": {"type": "boolean"},
                    "escalation_level": {"type": "integer"},
                    "sla_deadline": {"type": "date"},
                    "first_response_time": {"type": "date"},
                    "resolved_at": {"type": "date"},
                    "satisfaction_score": {"type": "integer"},
                    "satisfaction_comment": {"type": "text"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                    "channel": {"type": "keyword"},
                }
            }
        }


@dataclass
class Interaction:
    """
    Modelo de interacción con cliente para Elasticsearch.
    
    Registra todas las interacciones para análisis de engagement.
    """
    interaction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    customer_id: str = ""
    interaction_type: str = "email"  # email, call, meeting, chat, social
    
    # Dirección
    direction: str = "outbound"  # inbound, outbound
    
    # Contenido
    subject: Optional[str] = None
    content: str = ""
    summary: Optional[str] = None
    
    # Resultado
    outcome: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[datetime] = None
    
    # Metadata
    channel: str = "email"
    duration_seconds: Optional[int] = None
    agent_id: Optional[str] = None
    
    # Timestamps
    occurred_at: datetime = field(default_factory=datetime.now)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convierte a diccionario para indexar."""
        data = asdict(self)
        data["occurred_at"] = self.occurred_at.isoformat()
        data["created_at"] = self.created_at.isoformat()
        if self.next_action_date:
            data["next_action_date"] = self.next_action_date.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Interaction":
        """Crea instancia desde diccionario."""
        data = data.copy()
        for date_field in ["occurred_at", "created_at", "next_action_date"]:
            if date_field in data and data[date_field]:
                data[date_field] = datetime.fromisoformat(data[date_field])
        return cls(**data)

    @staticmethod
    def get_mapping() -> dict:
        """Retorna mapping de Elasticsearch."""
        return {
            "mappings": {
                "properties": {
                    "interaction_id": {"type": "keyword"},
                    "customer_id": {"type": "keyword"},
                    "interaction_type": {"type": "keyword"},
                    "direction": {"type": "keyword"},
                    "subject": {"type": "text"},
                    "content": {"type": "text"},
                    "summary": {"type": "text"},
                    "outcome": {"type": "keyword"},
                    "next_action": {"type": "keyword"},
                    "next_action_date": {"type": "date"},
                    "channel": {"type": "keyword"},
                    "duration_seconds": {"type": "integer"},
                    "agent_id": {"type": "keyword"},
                    "occurred_at": {"type": "date"},
                    "created_at": {"type": "date"},
                }
            }
        }


@dataclass
class Campaign:
    """
    Modelo de campaña de marketing para Elasticsearch.
    """
    campaign_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: Optional[str] = None
    campaign_type: str = "email"  # email, sms, social, multi-channel
    status: str = "draft"  # draft, active, paused, completed
    
    # Segmentación
    target_segment: str = "all"
    target_customer_ids: list[str] = field(default_factory=list)
    
    # Contenido
    subject: Optional[str] = None
    content: dict[str, Any] = field(default_factory=dict)
    
    # Métricas
    sent_count: int = 0
    delivered_count: int = 0
    opened_count: int = 0
    clicked_count: int = 0
    converted_count: int = 0
    
    # Fechas
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convierte a diccionario para indexar."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["updated_at"] = self.updated_at.isoformat()
        for date_field in ["scheduled_at", "started_at", "completed_at"]:
            if getattr(self, date_field):
                data[date_field] = getattr(self, date_field).isoformat()
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Campaign":
        """Crea instancia desde diccionario."""
        data = data.copy()
        for date_field in ["created_at", "updated_at", "scheduled_at", 
                          "started_at", "completed_at"]:
            if date_field in data and data[date_field]:
                data[date_field] = datetime.fromisoformat(data[date_field])
        return cls(**data)

    @staticmethod
    def get_mapping() -> dict:
        """Retorna mapping de Elasticsearch."""
        return {
            "mappings": {
                "properties": {
                    "campaign_id": {"type": "keyword"},
                    "name": {"type": "text"},
                    "description": {"type": "text"},
                    "campaign_type": {"type": "keyword"},
                    "status": {"type": "keyword"},
                    "target_segment": {"type": "keyword"},
                    "target_customer_ids": {"type": "keyword"},
                    "subject": {"type": "text"},
                    "content": {"type": "object"},
                    "sent_count": {"type": "integer"},
                    "delivered_count": {"type": "integer"},
                    "opened_count": {"type": "integer"},
                    "clicked_count": {"type": "integer"},
                    "converted_count": {"type": "integer"},
                    "scheduled_at": {"type": "date"},
                    "started_at": {"type": "date"},
                    "completed_at": {"type": "date"},
                    "created_at": {"type": "date"},
                    "updated_at": {"type": "date"},
                }
            }
        }
