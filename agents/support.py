"""
Agente de Soporte - Gestiona tickets y atención al cliente.
"""

import asyncio
from datetime import datetime
from typing import Optional
from enum import Enum

from agents.base import BaseAgent, AgentResponse, AgentState


class Priority(Enum):
    """Prioridad de tickets."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SupportAgent(BaseAgent):
    """
    Agente especializado en soporte al cliente.
    
    Capacidades:
    - Creación y gestión de tickets
    - Clasificación automática de incidencias
    - Respuestas sugeridas
    - Escalamiento automático
    """

    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        super().__init__(name or "support_agent", config)
        self._tickets_resolved = 0
        self._avg_response_time = 0

    @property
    def description(self) -> str:
        return "Agente de Soporte: Gestiona tickets, clasifica incidencias y proporciona respuestas"

    async def execute(self, input_data: dict) -> AgentResponse:
        """
        Ejecuta tareas de soporte.
        
        Args:
            input_data: Debe contener:
                - action: "create_ticket", "classify", "suggest_response", "escalate"
                - ticket_id: ID del ticket (opcional para create)
                - data: Datos de la incidencia
                
        Returns:
            AgentResponse con el resultado.
        """
        self.state.status = AgentStatus.WORKING
        self.state.last_updated = datetime.now()

        action = input_data.get("action")
        
        try:
            if action == "create_ticket":
                result = await self._create_ticket(input_data)
            elif action == "classify":
                result = await self._classify_ticket(input_data)
            elif action == "suggest_response":
                result = await self._suggest_response(input_data)
            elif action == "escalate":
                result = await self._escalate_ticket(input_data)
            elif action == "resolve":
                result = await self._resolve_ticket(input_data)
            else:
                return AgentResponse(
                    success=False,
                    error=f"Unknown action: {action}",
                    agent_id=self.state.agent_id,
                )

            return AgentResponse(
                success=True,
                data=result,
                agent_id=self.state.agent_id,
            )

        except Exception as e:
            return AgentResponse(
                success=False,
                error=str(e),
                agent_id=self.state.agent_id,
            )
        finally:
            self.state.status = AgentStatus.IDLE

    async def _create_ticket(self, input_data: dict) -> dict:
        """Crea un nuevo ticket de soporte."""
        customer_id = input_data.get("customer_id")
        subject = input_data.get("subject", "Sin asunto")
        description = input_data.get("description", "")
        channel = input_data.get("channel", "email")  # email, chat, phone

        ticket_id = f"tkt_{customer_id}_{datetime.now().strftime('%Y%m%d%H%M')}"
        
        # Clasificación automática
        classification = await self._auto_classify(description)

        return {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "subject": subject,
            "description": description,
            "channel": channel,
            "priority": classification["priority"],
            "category": classification["category"],
            "status": "open",
            "created_at": datetime.now().isoformat(),
        }

    async def _classify_ticket(self, input_data: dict) -> dict:
        """Clasifica un ticket existente."""
        ticket_id = input_data.get("ticket_id")
        description = input_data.get("description", "")

        classification = await self._auto_classify(description)

        return {
            "ticket_id": ticket_id,
            "priority": classification["priority"],
            "category": classification["category"],
            "subcategory": classification.get("subcategory"),
            "suggested_assignee": classification.get("assignee"),
        }

    async def _suggest_response(self, input_data: dict) -> dict:
        """Sugiere una respuesta para un ticket."""
        ticket_id = input_data.get("ticket_id")
        category = input_data.get("category")
        description = input_data.get("description", "")

        response_template = self._get_response_template(category, description)

        return {
            "ticket_id": ticket_id,
            "suggested_response": response_template["template"],
            "confidence": response_template["confidence"],
            "variables": response_template.get("variables", {}),
            "knowledge_base_articles": response_template.get("articles", []),
        }

    async def _escalate_ticket(self, input_data: dict) -> dict:
        """Escala un ticket a nivel superior."""
        ticket_id = input_data.get("ticket_id")
        reason = input_data.get("reason", "Escalamiento solicitado")
        target_level = input_data.get("target_level", "tier2")

        return {
            "ticket_id": ticket_id,
            "escalated": True,
            "target_level": target_level,
            "reason": reason,
            "escalated_at": datetime.now().isoformat(),
        }

    async def _resolve_ticket(self, input_data: dict) -> dict:
        """Marca un ticket como resuelto."""
        ticket_id = input_data.get("ticket_id")
        resolution_notes = input_data.get("resolution_notes", "")
        customer_satisfaction = input_data.get("satisfaction_score")

        self._tickets_resolved += 1

        return {
            "ticket_id": ticket_id,
            "status": "resolved",
            "resolution_notes": resolution_notes,
            "customer_satisfaction": customer_satisfaction,
            "resolved_at": datetime.now().isoformat(),
        }

    async def _auto_classify(self, description: str) -> dict:
        """Clasificación automática basada en palabras clave."""
        description_lower = description.lower()

        # Detección de prioridad
        priority = Priority.LOW
        if any(word in description_lower for word in ["urgente", "crítico", "emergency", "critical"]):
            priority = Priority.CRITICAL
        elif any(word in description_lower for word in ["importante", "prioritario", "high"]):
            priority = Priority.HIGH
        elif any(word in description_lower for word in ["ayuda", "duda", "question"]):
            priority = Priority.MEDIUM

        # Detección de categoría
        category = "general"
        subcategory = None
        assignee = None

        if any(word in description_lower for word in ["login", "password", "acceso", "contraseña"]):
            category = "access_management"
            assignee = "security_team"
        elif any(word in description_lower for word in ["pago", "factura", "billing", "cobro"]):
            category = "billing"
            assignee = "billing_team"
        elif any(word in description_lower for word in ["bug", "error", "fallo", "no funciona"]):
            category = "technical_issue"
            subcategory = "bug"
            assignee = "dev_team"
        elif any(word in description_lower for word in ["feature", "mejora", "sugerencia"]):
            category = "feature_request"
            assignee = "product_team"

        return {
            "priority": priority.value,
            "category": category,
            "subcategory": subcategory,
            "assignee": assignee,
        }

    def _get_response_template(self, category: Optional[str], description: str) -> dict:
        """Retorna plantilla de respuesta según categoría."""
        templates = {
            "access_management": {
                "template": "Hola, hemos recibido tu solicitud de acceso. Para verificar tu identidad, por favor confirma: 1) Tu email registrado 2) El último acceso exitoso. Te ayudaremos a recuperar el acceso lo antes posible.",
                "confidence": 0.85,
                "articles": ["KB-001: Recuperación de contraseña", "KB-002: Verificación en dos pasos"],
            },
            "billing": {
                "template": "Gracias por contactarnos sobre tu consulta de facturación. Para asistirte mejor, necesitamos: 1) Número de factura 2) Fecha del cargo 3) Monto cuestionado. Nuestro equipo de billing te responderá en 24h.",
                "confidence": 0.80,
                "articles": ["KB-010: Entendiendo tu factura", "KB-011: Métodos de pago"],
            },
            "technical_issue": {
                "template": "Lamentamos los inconvenientes técnicos. Para diagnosticar el problema, por favor proporciona: 1) Pasos para reproducir 2) Capturas de pantalla 3) Navegador/dispositivo utilizado. Nuestro equipo técnico está investigando.",
                "confidence": 0.75,
                "articles": ["KB-020: Solución de problemas comunes", "KB-021: Reportar un bug"],
            },
            None: {
                "template": "Gracias por contactarnos. Hemos recibido tu consulta y la estamos revisando. Te responderemos lo antes posible con una solución.",
                "confidence": 0.60,
                "articles": [],
            },
        }

        return templates.get(category, templates[None])

    def get_stats(self) -> dict:
        """Retorna estadísticas del agente."""
        return {
            "tickets_resolved": self._tickets_resolved,
            "avg_response_time": self._avg_response_time,
        }
