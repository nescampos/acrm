"""
Módulo de integración con Elastic Stack.

Proporciona:
- Conexión a Elasticsearch
- Modelos de datos CRM
- Repositorios para operaciones CRUD
- Elastic Agent Builder para agentes con RAG
"""

from .client import ElasticClient, elastic_client
from .models import Customer, Ticket, Interaction, Campaign
from .repository import (
    ElasticRepository,
    CustomerRepository,
    TicketRepository,
    InteractionRepository,
    CampaignRepository,
)
from .agent_builder import (
    ElasticAgentBuilder,
    ElasticAgentConfig,
    ElasticBaseAgent,
    create_elastic_sales_agent,
    create_elastic_support_agent,
    create_elastic_marketing_agent,
)

__all__ = [
    "ElasticClient",
    "elastic_client",
    "Customer",
    "Ticket",
    "Interaction",
    "Campaign",
    "ElasticRepository",
    "CustomerRepository",
    "TicketRepository",
    "InteractionRepository",
    "CampaignRepository",
    "ElasticAgentBuilder",
    "ElasticAgentConfig",
    "ElasticBaseAgent",
    "create_elastic_sales_agent",
    "create_elastic_support_agent",
    "create_elastic_marketing_agent",
]
