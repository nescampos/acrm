"""
Agente de Marketing - Gestiona campañas y engagement.
"""

import asyncio
from datetime import datetime
from typing import Optional

from agents.base import BaseAgent, AgentResponse, AgentState


class MarketingAgent(BaseAgent):
    """
    Agente especializado en marketing.
    
    Capacidades:
    - Segmentación de clientes
    - Creación de campañas
    - Análisis de engagement
    - Recomendaciones de contenido
    """

    def __init__(self, name: Optional[str] = None, config: Optional[dict] = None):
        super().__init__(name or "marketing_agent", config)
        self._campaigns_created = 0
        self._segments_analyzed = 0

    @property
    def description(self) -> str:
        return "Agente de Marketing: Crea campañas, segmenta audiencias y analiza engagement"

    async def execute(self, input_data: dict) -> AgentResponse:
        """
        Ejecuta tareas de marketing.
        
        Args:
            input_data: Debe contener:
                - action: "segment", "create_campaign", "analyze_engagement", "recommend_content"
                - data: Datos específicos de la acción
                
        Returns:
            AgentResponse con el resultado.
        """
        self.state.status = AgentStatus.WORKING
        self.state.last_updated = datetime.now()

        action = input_data.get("action")
        
        try:
            if action == "segment":
                result = await self._segment_audience(input_data)
            elif action == "create_campaign":
                result = await self._create_campaign(input_data)
            elif action == "analyze_engagement":
                result = await self._analyze_engagement(input_data)
            elif action == "recommend_content":
                result = await self._recommend_content(input_data)
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

    async def _segment_audience(self, input_data: dict) -> dict:
        """Segmenta la audiencia basada en criterios."""
        customers = input_data.get("customers", [])
        criteria = input_data.get("criteria", "behavior")

        segments = {
            "new_leads": [],
            "active_prospects": [],
            "customers": [],
            "at_risk": [],
            "champions": [],
        }

        for customer in customers:
            segment = self._classify_customer_segment(customer)
            segments[segment].append(customer.get("customer_id"))

        self._segments_analyzed += 1

        return {
            "total_customers": len(customers),
            "segments": {k: len(v) for k, v in segments.items()},
            "segment_details": segments,
        }

    async def _create_campaign(self, input_data: dict) -> dict:
        """Crea una nueva campaña de marketing."""
        campaign_name = input_data.get("name", "Nueva Campaña")
        target_segment = input_data.get("target_segment", "all")
        channel = input_data.get("channel", "email")
        content = input_data.get("content", {})

        campaign_id = f"cmp_{datetime.now().strftime('%Y%m%d%H%M')}"
        
        estimated_reach = input_data.get("estimated_reach", 0)
        predicted_ctr = self._predict_ctr(channel, target_segment)

        self._campaigns_created += 1

        return {
            "campaign_id": campaign_id,
            "name": campaign_name,
            "target_segment": target_segment,
            "channel": channel,
            "content": content,
            "status": "draft",
            "estimated_reach": estimated_reach,
            "predicted_ctr": predicted_ctr,
            "created_at": datetime.now().isoformat(),
        }

    async def _analyze_engagement(self, input_data: dict) -> dict:
        """Analiza el engagement de un cliente o segmento."""
        customer_id = input_data.get("customer_id")
        interactions = input_data.get("interactions", [])

        if not interactions:
            return {
                "customer_id": customer_id,
                "engagement_score": 0,
                "level": "inactive",
                "recommendations": ["Iniciar campaña de re-engagement"],
            }

        # Calcular score de engagement
        email_opens = sum(1 for i in interactions if i.get("type") == "email_open")
        clicks = sum(1 for i in interactions if i.get("type") == "click")
        purchases = sum(1 for i in interactions if i.get("type") == "purchase")
        support_tickets = sum(1 for i in interactions if i.get("type") == "support")

        score = (email_opens * 5) + (clicks * 10) + (purchases * 50) - (support_tickets * 10)
        score = min(max(score, 0), 100)  # Normalizar 0-100

        level = "inactive"
        if score >= 80:
            level = "champion"
        elif score >= 60:
            level = "engaged"
        elif score >= 40:
            level = "moderate"
        elif score >= 20:
            level = "low"

        return {
            "customer_id": customer_id,
            "engagement_score": score,
            "level": level,
            "metrics": {
                "email_opens": email_opens,
                "clicks": clicks,
                "purchases": purchases,
                "support_tickets": support_tickets,
            },
            "recommendations": self._get_engagement_recommendations(level),
        }

    async def _recommend_content(self, input_data: dict) -> dict:
        """Recomienda contenido basado en el perfil del cliente."""
        customer_data = input_data.get("customer", {})
        customer_stage = customer_data.get("stage", "lead")
        interests = customer_data.get("interests", [])
        past_interactions = customer_data.get("past_interactions", [])

        content_recommendations = self._generate_content_recommendations(
            customer_stage, interests, past_interactions
        )

        return {
            "customer_id": customer_data.get("customer_id"),
            "recommendations": content_recommendations,
            "personalization_score": self._calculate_personalization_score(customer_data),
        }

    def _classify_customer_segment(self, customer: dict) -> str:
        """Clasifica un cliente en un segmento."""
        days_since_signup = customer.get("days_since_signup", 0)
        total_purchases = customer.get("total_purchases", 0)
        last_activity_days = customer.get("days_since_last_activity", 999)

        if total_purchases >= 5 and last_activity_days <= 30:
            return "champions"
        elif total_purchases >= 1 and last_activity_days <= 60:
            return "customers"
        elif days_since_signup <= 30 and total_purchases == 0:
            return "new_leads"
        elif last_activity_days > 90:
            return "at_risk"
        else:
            return "active_prospects"

    def _predict_ctr(self, channel: str, segment: str) -> float:
        """Predice el CTR basado en canal y segmento."""
        base_rates = {
            "email": 0.025,
            "sms": 0.045,
            "push": 0.035,
            "social": 0.015,
        }

        segment_multipliers = {
            "champions": 2.0,
            "customers": 1.5,
            "active_prospects": 1.2,
            "new_leads": 0.8,
            "at_risk": 0.5,
            "all": 1.0,
        }

        base = base_rates.get(channel, 0.02)
        multiplier = segment_multipliers.get(segment, 1.0)
        
        return round(base * multiplier, 4)

    def _get_engagement_recommendations(self, level: str) -> list:
        """Retorna recomendaciones según nivel de engagement."""
        recommendations = {
            "champion": [
                "Programa programa de referidos",
                "Ofrece acceso anticipado a nuevos productos",
                "Solicita testimonios/reviews",
            ],
            "engaged": [
                "Envía contenido educativo avanzado",
                "Ofrece upsell/cross-sell relevante",
                "Invita a webinars exclusivos",
            ],
            "moderate": [
                "Envía casos de éxito relevantes",
                "Ofrece demo personalizada",
                "Comparte contenido de valor",
            ],
            "low": [
                "Campaña de re-activación",
                "Oferta especial de bienvenida",
                "Encuesta de intereses",
            ],
            "inactive": [
                "Campaña 'Te extrañamos'",
                "Oferta de recuperación agresiva",
                "Re-evaluar canal de comunicación",
            ],
        }
        return recommendations.get(level, ["Re-evaluar estrategia"])

    def _generate_content_recommendations(
        self, stage: str, interests: list, past_interactions: list
    ) -> list:
        """Genera recomendaciones de contenido personalizadas."""
        content_map = {
            "lead": ["Guía de introducción", "Webinar: Fundamentos", "Ebook gratuito"],
            "prospect": ["Caso de éxito", "Demo del producto", "Comparativa competitiva"],
            "customer": ["Guía de mejores prácticas", "Tutorial avanzado", "Nuevas features"],
        }

        base_content = content_map.get(stage, content_map["lead"])
        
        return [
            {"type": "content", "title": title, "priority": "high" if i == 0 else "medium"}
            for i, title in enumerate(base_content)
        ]

    def _calculate_personalization_score(self, customer_data: dict) -> float:
        """Calcula score de personalización disponible."""
        score = 0
        if customer_data.get("name"):
            score += 10
        if customer_data.get("interests"):
            score += min(len(customer_data["interests"]) * 15, 45)
        if customer_data.get("past_interactions"):
            score += min(len(customer_data["past_interactions"]) * 5, 30)
        if customer_data.get("purchase_history"):
            score += 15
        return min(score, 100)

    def get_stats(self) -> dict:
        """Retorna estadísticas del agente."""
        return {
            "campaigns_created": self._campaigns_created,
            "segments_analyzed": self._segments_analyzed,
        }
