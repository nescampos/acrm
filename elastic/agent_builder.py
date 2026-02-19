"""
Elastic Agent Builder - Integración con Elastic AI Assistant.

Proporciona agentes que utilizan Elasticsearch para:
- Búsqueda semántica de datos CRM
- RAG (Retrieval Augmented Generation) con datos del cliente
- Análisis de tendencias y patrones
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import json

from agents.base import BaseAgent, AgentResponse, AgentState
from elastic.repository import (
    CustomerRepository,
    TicketRepository,
    InteractionRepository,
    CampaignRepository,
)
from loguru import logger


@dataclass
class ElasticAgentConfig:
    """Configuración para agentes Elastic."""
    enable_semantic_search: bool = True
    enable_rag: bool = True
    top_k_results: int = 5
    index_prefix: str = "crm_"
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"


class ElasticAgentBuilder:
    """
    Builder para crear agentes integrados con Elastic.
    
    Facilita la creación de agentes con capacidades de:
    - Búsqueda en Elasticsearch
    - Análisis de datos CRM
    - Generación de respuestas con contexto
    """

    def __init__(self, name: str):
        self.name = name
        self.config = ElasticAgentConfig()
        self.repositories = {}
        self.tools = []
        self.description = ""

    def with_config(self, config: ElasticAgentConfig) -> "ElasticAgentBuilder":
        """Configura opciones del agente."""
        self.config = config
        return self

    def with_repository(self, name: str, repo: Any) -> "ElasticAgentBuilder":
        """Agrega un repositorio al agente."""
        self.repositories[name] = repo
        return self

    def with_tool(self, tool: dict) -> "ElasticAgentBuilder":
        """Agrega una herramienta al agente."""
        self.tools.append(tool)
        return self

    def with_description(self, description: str) -> "ElasticAgentBuilder":
        """Establece la descripción del agente."""
        self.description = description
        return self

    def build(self) -> "ElasticBaseAgent":
        """Construye el agente Elastic."""
        return ElasticBaseAgent(
            name=self.name,
            config=self.config,
            repositories=self.repositories,
            tools=self.tools,
            description=self.description,
        )


class ElasticBaseAgent(BaseAgent):
    """
    Agente base con integración Elastic.
    
    Proporciona capacidades de búsqueda y análisis sobre datos CRM
    almacenados en Elasticsearch.
    """

    def __init__(
        self,
        name: str,
        config: ElasticAgentConfig,
        repositories: dict,
        tools: list,
        description: str,
    ):
        super().__init__(name, config.__dict__)
        self._config = config
        self._repositories = repositories
        self._tools = tools
        self._description = description
        self._context = []

    @property
    def description(self) -> str:
        return self._description or f"Agente Elastic: {self.name}"

    async def execute(self, input_data: dict) -> AgentResponse:
        """
        Ejecuta una consulta usando Elastic.
        
        Args:
            input_data: Debe contener:
                - query: Consulta natural o estructurada
                - action: Acción específica a realizar
                - filters: Filtros opcionales
                
        Returns:
            AgentResponse con resultados.
        """
        self.state.status = AgentState.WORKING
        self.state.last_updated = datetime.now()

        try:
            action = input_data.get("action", "search")
            
            if action == "search":
                result = await self._search(input_data)
            elif action == "analyze":
                result = await self._analyze(input_data)
            elif action == "aggregate":
                result = await self._aggregate(input_data)
            elif action == "retrieve_context":
                result = await self._retrieve_context(input_data)
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
            logger.error(f"ElasticAgent execution error: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                agent_id=self.state.agent_id,
            )
        finally:
            self.state.status = AgentState.IDLE

    async def _search(self, input_data: dict) -> dict:
        """
        Ejecuta búsqueda en Elasticsearch.
        
        Soporta búsqueda por índice específico o búsqueda global.
        """
        index = input_data.get("index")
        query = input_data.get("query", "")
        filters = input_data.get("filters", {})
        top_k = input_data.get("top_k", self._config.top_k_results)

        results = {}
        
        if index and index in self._repositories:
            repo = self._repositories[index]
            search_query = self._build_search_query(query, filters)
            results[index] = await repo.search(search_query, size=top_k)
        else:
            # Búsqueda global en todos los repositorios
            for repo_name, repo in self._repositories.items():
                search_query = self._build_search_query(query, filters)
                repo_results = await repo.search(search_query, size=top_k // 2)
                if repo_results:
                    results[repo_name] = repo_results

        return {
            "query": query,
            "results": {k: [r.to_dict() if hasattr(r, 'to_dict') else r for r in v] for k, v in results.items()},
            "total_found": sum(len(v) for v in results.values()),
        }

    async def _analyze(self, input_data: dict) -> dict:
        """
        Analiza datos de un cliente o entidad.
        """
        customer_id = input_data.get("customer_id")
        include_interactions = input_data.get("include_interactions", True)
        include_tickets = input_data.get("include_tickets", True)

        analysis = {"customer_id": customer_id}

        # Obtener datos del cliente
        if "customers" in self._repositories:
            customer = await self._repositories["customers"].get(customer_id)
            if customer:
                analysis["customer"] = customer.to_dict()

        # Obtener interacciones
        if include_interactions and "interactions" in self._repositories:
            interactions = await self._repositories["interactions"].find_recent(customer_id)
            analysis["recent_interactions"] = [i.to_dict() for i in interactions]
            analysis["interaction_count"] = len(interactions)

        # Obtener tickets
        if include_tickets and "tickets" in self._repositories:
            tickets = await self._repositories["tickets"].find_by_customer(customer_id)
            analysis["tickets"] = [t.to_dict() for t in tickets]
            analysis["open_tickets"] = sum(1 for t in tickets if t.status == "open")

        # Calcular métricas derivadas
        analysis["health_score"] = self._calculate_health_score(analysis)
        analysis["recommendations"] = self._generate_recommendations(analysis)

        return analysis

    async def _aggregate(self, input_data: dict) -> dict:
        """
        Ejecuta agregaciones en Elasticsearch.
        """
        index = input_data.get("index")
        aggregation_type = input_data.get("aggregation_type", "terms")
        field = input_data.get("field")
        filters = input_data.get("filters", {})

        if not index or index not in self._repositories:
            return {"error": "Invalid index"}

        repo = self._repositories[index]
        
        # Construir agregación
        agg_config = {
            "main_agg": {
                "filter": filters if filters else {"match_all": {}},
                "aggs": {}
            }
        }

        if aggregation_type == "terms":
            agg_config["main_agg"]["aggs"][field] = {
                "terms": {"field": field, "size": 10}
            }
        elif aggregation_type == "date_histogram":
            agg_config["main_agg"]["aggs"][field] = {
                "date_histogram": {"field": field, "calendar_interval": "month"}
            }
        elif aggregation_type == "metrics":
            agg_config["main_agg"]["aggs"][f"{field}_avg"] = {"avg": {"field": field}}
            agg_config["main_agg"]["aggs"][f"{field}_sum"] = {"sum": {"field": field}}
            agg_config["main_agg"]["aggs"][f"{field}_min"] = {"min": {"field": field}}
            agg_config["main_agg"]["aggs"][f"{field}_max"] = {"max": {"field": field}}

        results = await repo.aggregate(agg_config)
        
        return {
            "index": index,
            "aggregation_type": aggregation_type,
            "results": results,
        }

    async def _retrieve_context(self, input_data: dict) -> dict:
        """
        Recupera contexto para RAG (Retrieval Augmented Generation).
        
        Busca información relevante en Elasticsearch para proporcionar
        contexto a un LLM.
        """
        query = input_data.get("query", "")
        context_types = input_data.get("context_types", ["customers", "interactions", "tickets"])
        top_k = input_data.get("top_k", self._config.top_k_results)

        context = []
        
        for ctx_type in context_types:
            if ctx_type in self._repositories:
                repo = self._repositories[ctx_type]
                search_query = self._build_semantic_query(query)
                results = await repo.search(search_query, size=top_k // len(context_types))
                
                for result in results:
                    context.append({
                        "type": ctx_type,
                        "data": result.to_dict() if hasattr(result, 'to_dict') else result,
                    })

        return {
            "query": query,
            "context": context,
            "context_count": len(context),
            "formatted_context": self._format_context_for_llm(context),
        }

    def _build_search_query(self, query: str, filters: dict) -> dict:
        """Construye query de búsqueda Elasticsearch."""
        if not query:
            return filters if filters else {"match_all": {}}
        
        bool_query = {"bool": {}}
        
        # Query principal (búsqueda full-text)
        bool_query["bool"]["must"] = {
            "multi_match": {
                "query": query,
                "fields": ["*"],
                "fuzziness": "AUTO",
            }
        }
        
        # Filtros adicionales
        if filters:
            bool_query["bool"]["filter"] = filters
            
        return bool_query

    def _build_semantic_query(self, query: str) -> dict:
        """Construye query para búsqueda semántica."""
        # Si hay campos de texto enriquecido, priorizarlos
        return {
            "multi_match": {
                "query": query,
                "fields": [
                    "description^2",
                    "content^2",
                    "subject^2",
                    "summary^2",
                    "name^1.5",
                    "tags^1.5",
                    "category",
                    "outcome",
                ],
                "type": "best_fields",
                "fuzziness": "AUTO",
            }
        }

    def _calculate_health_score(self, analysis: dict) -> int:
        """Calcula score de salud del cliente (0-100)."""
        score = 50  # Base
        
        # Ajustar por interacciones recientes
        interaction_count = analysis.get("interaction_count", 0)
        if interaction_count >= 5:
            score += 20
        elif interaction_count >= 2:
            score += 10
        
        # Penalizar por tickets abiertos
        open_tickets = analysis.get("open_tickets", 0)
        score -= open_tickets * 10
        
        # Bonus por ser cliente convertido
        customer = analysis.get("customer", {})
        if customer.get("status") == "customer":
            score += 15
        elif customer.get("status") == "champion":
            score += 25
            
        return max(0, min(100, score))

    def _generate_recommendations(self, analysis: dict) -> list[str]:
        """Genera recomendaciones basadas en el análisis."""
        recommendations = []
        
        open_tickets = analysis.get("open_tickets", 0)
        if open_tickets > 0:
            recommendations.append(f"Resolver {open_tickets} ticket(s) pendiente(s)")
        
        interaction_count = analysis.get("interaction_count", 0)
        if interaction_count < 2:
            recommendations.append("Programar seguimiento con el cliente")
        
        customer = analysis.get("customer", {})
        if customer.get("status") == "lead":
            recommendations.append("Calificar lead y avanzar en funnel de ventas")
        elif customer.get("status") == "champion":
            recommendations.append("Considerar para programa de referidos")
            
        return recommendations

    def _format_context_for_llm(self, context: list) -> str:
        """Formatea contexto para enviar a LLM."""
        formatted = []
        for item in context:
            ctx_type = item["type"]
            data = item["data"]
            formatted.append(f"[{ctx_type.upper()}]")
            for key, value in data.items():
                if value is not None:
                    formatted.append(f"  {key}: {value}")
            formatted.append("")
        return "\n".join(formatted)

    def get_available_tools(self) -> list[dict]:
        """Retorna herramientas disponibles para el agente."""
        return self._tools


# Factory para crear agentes Elastic preconfigurados
def create_elastic_sales_agent() -> ElasticBaseAgent:
    """Crea agente de ventas con integración Elastic."""
    return ElasticAgentBuilder("elastic_sales_agent") \
        .with_description("Agente de Ventas con búsqueda Elastic: califica leads, analiza oportunidades") \
        .with_repository("customers", CustomerRepository()) \
        .with_repository("interactions", InteractionRepository()) \
        .build()


def create_elastic_support_agent() -> ElasticBaseAgent:
    """Crea agente de soporte con integración Elastic."""
    return ElasticAgentBuilder("elastic_support_agent") \
        .with_description("Agente de Soporte con búsqueda Elastic: gestiona tickets, analiza historial") \
        .with_repository("customers", CustomerRepository()) \
        .with_repository("tickets", TicketRepository()) \
        .with_repository("interactions", InteractionRepository()) \
        .build()


def create_elastic_marketing_agent() -> ElasticBaseAgent:
    """Crea agente de marketing con integración Elastic."""
    return ElasticAgentBuilder("elastic_marketing_agent") \
        .with_description("Agente de Marketing con búsqueda Elastic: segmenta, analiza engagement") \
        .with_repository("customers", CustomerRepository()) \
        .with_repository("campaigns", CampaignRepository()) \
        .with_repository("interactions", InteractionRepository()) \
        .build()
