"""
Agente de Ventas - Gestiona leads y oportunidades de venta.
"""

import asyncio
from datetime import datetime
from typing import Optional

from agents.base import BaseAgent, AgentResponse, AgentState


class SalesAgent(BaseAgent):
    """
    Agente especializado en gestión de ventas.
    
    Capacidades:
    - Calificación de leads
    - Seguimiento de oportunidades
    - Programación de reuniones
    - Análisis de probabilidad de cierre
    """

    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        super().__init__(name or "sales_agent", config)
        self._leads_qualified = 0
        self._opportunities_created = 0

    @property
    def description(self) -> str:
        return "Agente de Ventas: Califica leads, gestiona oportunidades y programa reuniones"

    async def execute(self, input_data: dict) -> AgentResponse:
        """
        Ejecuta tareas de ventas.
        
        Args:
            input_data: Debe contener:
                - action: "qualify_lead", "follow_up", "schedule_meeting", "analyze"
                - customer_id: ID del cliente
                - data: Datos adicionales según la acción
                
        Returns:
            AgentResponse con el resultado de la acción.
        """
        self.state.status = AgentStatus.WORKING
        self.state.last_updated = datetime.now()

        action = input_data.get("action")
        
        try:
            if action == "qualify_lead":
                result = await self._qualify_lead(input_data)
            elif action == "follow_up":
                result = await self._follow_up(input_data)
            elif action == "schedule_meeting":
                result = await self._schedule_meeting(input_data)
            elif action == "analyze":
                result = await self._analyze_opportunity(input_data)
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

    async def _qualify_lead(self, input_data: dict) -> dict:
        """Califica un lead basado en criterios BANT."""
        customer_id = input_data.get("customer_id")
        data = input_data.get("data", {})

        # Criterios de calificación (Budget, Authority, Need, Timeline)
        budget = data.get("budget", 0)
        authority = data.get("has_authority", False)
        need = data.get("need_score", 0)
        timeline = data.get("timeline", "unknown")

        score = 0
        if budget >= 1000:
            score += 25
        if authority:
            score += 25
        score += min(need, 25)
        if timeline in ["immediate", "this_month"]:
            score += 25

        qualification = "hot" if score >= 75 else "warm" if score >= 50 else "cold"
        self._leads_qualified += 1

        return {
            "customer_id": customer_id,
            "qualification": qualification,
            "score": score,
            "recommendation": self._get_recommendation(qualification),
        }

    async def _follow_up(self, input_data: dict) -> dict:
        """Genera un plan de seguimiento para un cliente."""
        customer_id = input_data.get("customer_id")
        last_contact = input_data.get("last_contact")
        interaction_history = input_data.get("history", [])

        # Determinar siguiente acción basada en historial
        next_action = "email"
        if len(interaction_history) > 3:
            next_action = "call"
        
        return {
            "customer_id": customer_id,
            "next_action": next_action,
            "suggested_date": datetime.now().strftime("%Y-%m-%d"),
            "talking_points": self._generate_talking_points(interaction_history),
        }

    async def _schedule_meeting(self, input_data: dict) -> dict:
        """Programa una reunión con un cliente."""
        customer_id = input_data.get("customer_id")
        meeting_type = input_data.get("meeting_type", "discovery")
        preferred_times = input_data.get("preferred_times", [])

        meeting_id = f"mtg_{customer_id}_{datetime.now().strftime('%Y%m%d')}"
        
        return {
            "meeting_id": meeting_id,
            "customer_id": customer_id,
            "meeting_type": meeting_type,
            "status": "pending_confirmation",
            "duration_minutes": 30 if meeting_type == "discovery" else 60,
        }

    async def _analyze_opportunity(self, input_data: dict) -> dict:
        """Analiza la probabilidad de cierre de una oportunidad."""
        opportunity_data = input_data.get("opportunity", {})
        
        stage = opportunity_data.get("stage", "prospecting")
        deal_size = opportunity_data.get("deal_size", 0)
        engagement_score = opportunity_data.get("engagement_score", 50)

        stage_probability = {
            "prospecting": 0.1,
            "qualified": 0.25,
            "proposal": 0.5,
            "negotiation": 0.75,
            "closing": 0.9,
        }

        base_prob = stage_probability.get(stage, 0.1)
        final_probability = min(base_prob * (engagement_score / 50), 0.95)

        return {
            "close_probability": round(final_probability * 100, 2),
            "expected_value": round(deal_size * final_probability, 2),
            "recommended_actions": self._get_closure_actions(stage),
        }

    def _get_recommendation(self, qualification: str) -> str:
        """Retorna recomendación basada en calificación."""
        recommendations = {
            "hot": "Priorizar contacto inmediato, alta probabilidad de conversión",
            "warm": "Mantener seguimiento regular, nutrir relación",
            "cold": "Incluir en nurturing campaigns, re-evaluar en 30 días",
        }
        return recommendations.get(qualification, "Re-evaluar información")

    def _generate_talking_points(self, history: list) -> list:
        """Genera puntos de conversación basados en historial."""
        if not history:
            return ["Presentación inicial", "Descubrimiento de necesidades"]
        
        return [
            "Seguimiento de conversación anterior",
            "Actualización de productos/servicios",
            "Resolución de objeciones pendientes",
        ]

    def _get_closure_actions(self, stage: str) -> list:
        """Retorna acciones recomendadas para cada etapa."""
        actions = {
            "prospecting": ["Investigar empresa", "Identificar decisores"],
            "qualified": ["Agendar discovery call", "Preparar preguntas BANT"],
            "proposal": ["Enviar propuesta formal", "Seguimiento en 48h"],
            "negotiation": ["Preparar opciones de pricing", "Identificar objeciones"],
            "closing": ["Preparar contrato", "Coordinar onboarding"],
        }
        return actions.get(stage, ["Re-evaluar estrategia"])

    def get_stats(self) -> dict:
        """Retorna estadísticas del agente."""
        return {
            "leads_qualified": self._leads_qualified,
            "opportunities_created": self._opportunities_created,
        }
