"""
Clase base para todos los agentes del sistema.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional
import uuid
from datetime import datetime


class AgentStatus(Enum):
    """Estado del agente."""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"


@dataclass
class AgentState:
    """Estado interno del agente."""
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convierte el estado a diccionario."""
        return {
            "agent_id": self.agent_id,
            "status": self.status.value,
            "current_task": self.current_task,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class AgentResponse:
    """Respuesta estándar de un agente."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    agent_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convierte la respuesta a diccionario."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "agent_id": self.agent_id,
            "timestamp": self.timestamp.isoformat(),
        }


class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes.
    
    Cada agente debe implementar:
    - name: Nombre identificador del agente
    - description: Descripción de las capacidades
    - execute: Lógica principal de ejecución
    """

    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        self.name = name or self.__class__.__name__
        self.config = config or {}
        self.state = AgentState()
        self._initialized = False

    @property
    @abstractmethod
    def description(self) -> str:
        """Descripción de las capacidades del agente."""
        pass

    @abstractmethod
    async def execute(self, input_data: dict) -> AgentResponse:
        """
        Ejecuta la tarea principal del agente.
        
        Args:
            input_data: Datos de entrada para procesar.
            
        Returns:
            AgentResponse con el resultado de la ejecución.
        """
        pass

    async def initialize(self) -> None:
        """Inicializa el agente (setup de recursos, conexiones, etc.)."""
        self._initialized = True
        self.state.status = AgentStatus.IDLE

    async def shutdown(self) -> None:
        """Libera recursos antes de cerrar el agente."""
        self._initialized = False
        self.state.status = AgentStatus.IDLE

    def get_capabilities(self) -> dict:
        """Retorna las capacidades del agente."""
        return {
            "name": self.name,
            "description": self.description,
            "config": self.config,
        }

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name}, status={self.state.status.value})"
