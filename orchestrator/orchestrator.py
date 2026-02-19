"""
Orquestador CRM - Gestiona y coordina todos los agentes del sistema.

Funciona como un CRM agéntico que:
- Registra y gestiona el ciclo de vida de agentes
- Distribuye tareas entre agentes especializados
- Mantiene estado global del sistema
- Coordina flujos de trabajo multi-agente
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
import uuid
from loguru import logger

from agents.base import BaseAgent, AgentResponse, AgentStatus


@dataclass
class Task:
    """Tarea para ser ejecutada por un agente."""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: Optional[str] = None
    input_data: dict = field(default_factory=dict)
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[AgentResponse] = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "agent_name": self.agent_name,
            "input_data": self.input_data,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "result": self.result.to_dict() if self.result else None,
        }


@dataclass
class CustomerRecord:
    """Registro de cliente en el CRM."""
    customer_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str = "lead"  # lead, prospect, customer, inactive
    metadata: dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "customer_id": self.customer_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "status": self.status,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class CRMOrchestrator:
    """
    Orquestador principal del sistema multi-agente.
    
    Actúa como un CRM agéntico que coordina:
    - Registro de clientes
    - Distribución de tareas a agentes especializados
    - Seguimiento de interacciones
    - Flujos de trabajo automatizados
    """

    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.agents: dict[str, BaseAgent] = {}
        self.customers: dict[str, CustomerRecord] = {}
        self.tasks: dict[str, Task] = {}
        self._running = False
        self._task_queue: asyncio.Queue = asyncio.Queue()
        logger.info("CRM Orchestrator initialized")

    async def register_agent(self, agent: BaseAgent) -> bool:
        """
        Registra un agente en el orquestador.
        
        Args:
            agent: Instancia del agente a registrar.
            
        Returns:
            True si el registro fue exitoso.
        """
        if agent.name in self.agents:
            logger.warning(f"Agent {agent.name} already registered")
            return False

        await agent.initialize()
        self.agents[agent.name] = agent
        logger.info(f"Agent {agent.name} registered successfully")
        return True

    async def unregister_agent(self, agent_name: str) -> bool:
        """
        Da de baja un agente del sistema.
        
        Args:
            agent_name: Nombre del agente a remover.
            
        Returns:
            True si la baja fue exitosa.
        """
        if agent_name not in self.agents:
            return False

        agent = self.agents[agent_name]
        await agent.shutdown()
        del self.agents[agent_name]
        logger.info(f"Agent {agent_name} unregistered")
        return True

    def get_agent(self, agent_name: str) -> Optional[BaseAgent]:
        """Obtiene un agente por nombre."""
        return self.agents.get(agent_name)

    def list_agents(self) -> list[dict]:
        """Lista todos los agentes registrados con su estado."""
        return [
            {
                "name": agent.name,
                "description": agent.description,
                "status": agent.state.status.value,
            }
            for agent in self.agents.values()
        ]

    # Customer Management
    def add_customer(self, customer_data: dict) -> CustomerRecord:
        """
        Agrega un nuevo cliente al CRM.
        
        Args:
            customer_data: Datos del cliente (name, email, phone, etc.)
            
        Returns:
            CustomerRecord del cliente creado.
        """
        customer = CustomerRecord(
            name=customer_data.get("name"),
            email=customer_data.get("email"),
            phone=customer_data.get("phone"),
            status=customer_data.get("status", "lead"),
            metadata=customer_data.get("metadata", {}),
        )
        self.customers[customer.customer_id] = customer
        logger.info(f"Customer {customer.customer_id} added: {customer.name}")
        return customer

    def get_customer(self, customer_id: str) -> Optional[CustomerRecord]:
        """Obtiene un cliente por ID."""
        return self.customers.get(customer_id)

    def update_customer(self, customer_id: str, updates: dict) -> Optional[CustomerRecord]:
        """
        Actualiza datos de un cliente.
        
        Args:
            customer_id: ID del cliente.
            updates: Diccionario con campos a actualizar.
            
        Returns:
            CustomerRecord actualizado o None si no existe.
        """
        customer = self.customers.get(customer_id)
        if not customer:
            return None

        for key, value in updates.items():
            if hasattr(customer, key) and key not in ["customer_id", "created_at"]:
                setattr(customer, key, value)
        
        customer.updated_at = datetime.now()
        logger.info(f"Customer {customer_id} updated")
        return customer

    def list_customers(self, status: Optional[str] = None) -> list[dict]:
        """
        Lista clientes, opcionalmente filtrados por estado.
        
        Args:
            status: Filtro por estado (lead, prospect, customer, inactive)
            
        Returns:
            Lista de diccionarios con datos de clientes.
        """
        customers = self.customers.values()
        if status:
            customers = [c for c in customers if c.status == status]
        return [c.to_dict() for c in customers]

    # Task Management
    async def assign_task(
        self,
        agent_name: str,
        input_data: dict,
        priority: int = 0,
    ) -> Optional[Task]:
        """
        Asigna una tarea a un agente.
        
        Args:
            agent_name: Nombre del agente.
            input_data: Datos de entrada para la tarea.
            priority: Prioridad de la tarea (mayor = más prioritario).
            
        Returns:
            Task creada o None si el agente no existe.
        """
        if agent_name not in self.agents:
            logger.error(f"Agent {agent_name} not found")
            return None

        task = Task(
            agent_name=agent_name,
            input_data=input_data,
            priority=priority,
        )
        self.tasks[task.task_id] = task
        await self._task_queue.put(task)
        logger.info(f"Task {task.task_id} assigned to {agent_name}")
        return task

    async def execute_task(self, task: Task) -> AgentResponse:
        """
        Ejecuta una tarea mediante el agente correspondiente.
        
        Args:
            task: Tarea a ejecutar.
            
        Returns:
            AgentResponse con el resultado.
        """
        agent = self.agents.get(task.agent_name)
        if not agent:
            return AgentResponse(
                success=False,
                error=f"Agent {task.agent_name} not found",
            )

        task.status = "running"
        agent.state.status = AgentStatus.WORKING
        agent.state.current_task = task.task_id

        try:
            result = await agent.execute(task.input_data)
            task.result = result
            task.status = "completed" if result.success else "failed"
            return result
        except Exception as e:
            task.status = "error"
            logger.error(f"Task {task.task_id} failed: {str(e)}")
            return AgentResponse(
                success=False,
                error=str(e),
                agent_id=agent.state.agent_id,
            )
        finally:
            agent.state.status = AgentStatus.IDLE
            agent.state.current_task = None

    async def process_queue(self) -> None:
        """Procesa la cola de tareas continuamente."""
        self._running = True
        logger.info("Task queue processor started")

        while self._running:
            try:
                task = await asyncio.wait_for(self._task_queue.get(), timeout=1.0)
                await self.execute_task(task)
                self._task_queue.task_done()
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing task: {e}")

    def stop(self) -> None:
        """Detiene el orquestador."""
        self._running = False
        logger.info("CRM Orchestrator stopped")

    async def shutdown(self) -> None:
        """Apaga el orquestador y todos los agentes."""
        self.stop()
        for agent in self.agents.values():
            await agent.shutdown()
        logger.info("CRM Orchestrator shutdown complete")

    def get_status(self) -> dict:
        """Obtiene el estado actual del orquestador."""
        return {
            "running": self._running,
            "agents_count": len(self.agents),
            "customers_count": len(self.customers),
            "tasks_count": len(self.tasks),
            "pending_tasks": self._task_queue.qsize(),
            "agents": self.list_agents(),
        }
