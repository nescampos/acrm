"""
Agentes especializados para el CRM.
"""

from .sales import SalesAgent
from .support import SupportAgent
from .marketing import MarketingAgent

__all__ = ["SalesAgent", "SupportAgent", "MarketingAgent"]
