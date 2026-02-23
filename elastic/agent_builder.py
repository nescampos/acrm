"""
Elastic Agent Builder - Integración con Elastic AI Assistant.

Proporciona:
- Agentes locales (ElasticBaseAgent) con búsqueda/RAG sobre Elasticsearch.
- Integración con la API de Kibana (Elastic Agent Builder) para gestionar
  agentes, tools y conversaciones de forma programática.
Ref: https://www.elastic.co/docs/explore-analyze/ai-features/agent-builder/kibana-api
"""

from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime
import json

from agents.base import BaseAgent, AgentResponse, AgentState, AgentStatus
from elastic.repository import (
    CustomerRepository,
    TicketRepository,
    InteractionRepository,
    CampaignRepository,
)
from loguru import logger

from config import config
from .kibana_agent_builder_client import KibanaAgentBuilderClient


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
        self.state.status = AgentStatus.WORKING
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
            self.state.status = AgentStatus.IDLE

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


# ---------- Integración API Kibana (Elastic Agent Builder) ----------


def get_kibana_client() -> Optional[KibanaAgentBuilderClient]:
    """
    Retorna un cliente para la API de Elastic Agent Builder en Kibana
    si están configurados KIBANA_HOST y ELASTIC_CLOUD_API_KEY. Si no, retorna None.
    """
    host = config.get("KIBANA_HOST")
    api_key = config.get("ELASTIC_CLOUD_API_KEY")
    if not host or not api_key:
        return None
    return KibanaAgentBuilderClient(
        base_url=host,
        api_key=api_key,
        space=config.kibana_space,
    )


# Definición de los agentes CRM que se crean en Kibana al arrancar
CRM_AGENTS = [
    {
        "id": "crm_sales_agent",
        "name": "Ventas CRM",
        "description": "Agente de Ventas: califica leads, analiza oportunidades en índices crm_*",
        "instructions": (
            "Eres un agente de ventas. Usa las herramientas de búsqueda para consultar "
            "los índices crm_customers y crm_interactions. Ayuda a calificar leads, "
            "analizar oportunidades y recomendar siguientes pasos. Responde en español."
        ),
        "tool_ids": [
            "platform.core.search",
            "platform.core.list_indices",
            "platform.core.get_document_by_id",
        ],
        "labels": ["crm", "elastic-crm", "sales"],
    },
    {
        "id": "crm_support_agent",
        "name": "Soporte CRM",
        "description": "Agente de Soporte: gestiona tickets, analiza historial en índices crm_*",
        "instructions": (
            "Eres un agente de soporte. Usa las herramientas para consultar "
            "crm_tickets, crm_customers y crm_interactions. Ayuda a resolver incidencias, "
            "buscar tickets similares y revisar el historial del cliente. Responde en español."
        ),
        "tool_ids": [
            "platform.core.search",
            "platform.core.list_indices",
            "platform.core.get_document_by_id",
        ],
        "labels": ["crm", "elastic-crm", "support"],
    },
    {
        "id": "crm_marketing_agent",
        "name": "Marketing CRM",
        "description": "Agente de Marketing: segmenta, analiza engagement en índices crm_*",
        "instructions": (
            "Eres un agente de marketing. Usa las herramientas para consultar "
            "crm_customers, crm_campaigns y crm_interactions. Ayuda a segmentar clientes, "
            "analizar engagement y resultados de campañas. Responde en español."
        ),
        "tool_ids": [
            "platform.core.search",
            "platform.core.list_indices",
            "platform.core.get_document_by_id",
        ],
        "labels": ["crm", "elastic-crm", "marketing"],
    },
]


async def ensure_crm_agents_in_kibana(
    client: KibanaAgentBuilderClient,
) -> list[str]:
    """
    Crea en Kibana los agentes CRM si no existen (igual que se crean los índices).
    Retorna la lista de ids de agentes (ya existentes o recién creados).
    """
    for spec in CRM_AGENTS:
        agent_id = spec["id"]
        # Validar existencia usando get_agent del cliente
        existing = await client.get_agent(agent_id)
        if existing:
            logger.debug(f"Agente ya existe en Kibana: {agent_id}")
            continue

        payload = build_crm_agent_payload(
            agent_id=agent_id,
            name=spec["name"],
            description=spec["description"],
            instructions=spec["instructions"],
            tool_ids=spec.get("tool_ids"),
            labels=spec.get("labels"),
        )
        await client.create_agent(payload)
        logger.info(f"Agente creado en Kibana: {agent_id}")

    return [s["id"] for s in CRM_AGENTS]


async def create_and_register_crm_agents(
    client: Optional[KibanaAgentBuilderClient] = None,
) -> tuple[list["KibanaAgentWrapper"], KibanaAgentBuilderClient]:
    """
    Asegura que los agentes CRM existan en Kibana y retorna los wrappers
    listos para registrar en el orquestador y el cliente (para cerrarlo en shutdown).
    """
    c = client or get_kibana_client()
    if not c:
        raise RuntimeError(
            "Kibana no configurado. Define KIBANA_HOST y KIBANA_API_KEY en .env"
        )
    await ensure_crm_agents_in_kibana(c)
    wrappers = [
        KibanaAgentWrapper(
            kibana_agent_id=spec["id"],
            client=c,
            name=spec["id"],
            description=spec["description"],
        )
        for spec in CRM_AGENTS
    ]
    return wrappers, c


class KibanaAgentWrapper(BaseAgent):
    """
    Wrapper que delega execute() en un agente de Elastic Agent Builder (Kibana)
    mediante la API converse.

    Útil para usar agentes creados/gestionados en Kibana desde el orquestador CRM.
    """

    def __init__(
        self,
        kibana_agent_id: str,
        client: KibanaAgentBuilderClient,
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        super().__init__(name=name or kibana_agent_id)
        self._kibana_agent_id = kibana_agent_id
        self._client = client
        self._description = description or f"Agente Kibana: {kibana_agent_id}"

    @property
    def description(self) -> str:
        return self._description

    @property
    def kibana_agent_id(self) -> str:
        return self._kibana_agent_id

    async def execute(self, input_data: dict) -> AgentResponse:
        """
        Envía el mensaje al agente en Kibana vía API converse.

        input_data puede contener:
          - "input" o "message": texto a enviar al agente
          - "conversation_id": opcional, para continuar una conversación
        """
        self.state.status = AgentStatus.WORKING
        self.state.last_updated = datetime.now()
        try:
            text = input_data.get("input") or input_data.get("message") or ""
            if not text:
                return AgentResponse(
                    success=False,
                    error="Falta 'input' o 'message' en input_data",
                    agent_id=self.state.agent_id,
                )
            conversation_id = input_data.get("conversation_id")
            response = await self._client.converse(
                agent_id=self._kibana_agent_id,
                input_text=text,
                conversation_id=conversation_id,
            )
            return AgentResponse(
                success=True,
                data=response,
                agent_id=self.state.agent_id,
            )
        except Exception as e:
            logger.error(f"KibanaAgentWrapper execute error: {e}")
            return AgentResponse(
                success=False,
                error=str(e),
                agent_id=self.state.agent_id,
            )
        finally:
            self.state.status = AgentStatus.IDLE


def create_kibana_agent_wrapper(
    kibana_agent_id: str,
    client: Optional[KibanaAgentBuilderClient] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
) -> Optional[KibanaAgentWrapper]:
    """
    Crea un wrapper que usa el agente de Kibana con el id dado.

    Si no se pasa client, se usa get_kibana_client(). Si Kibana no está
    configurado, retorna None.
    """
    c = client or get_kibana_client()
    if not c:
        logger.warning("Kibana no configurado (KIBANA_HOST + KIBANA_API_KEY). No se crea wrapper.")
        return None
    return KibanaAgentWrapper(
        kibana_agent_id=kibana_agent_id,
        client=c,
        name=name,
        description=description,
    )


def build_crm_agent_payload(
    agent_id: str,
    name: str,
    description: str,
    instructions: str,
    tool_ids: Optional[list[str]] = None,
    labels: Optional[list[str]] = None,
) -> dict:
    """
    Construye el payload para crear/actualizar un agente en Kibana
    orientado a CRM (búsqueda en índices crm_*).

    tool_ids por defecto: platform.core.search y list_indices para explorar datos.
    """
    if tool_ids is None:
        tool_ids = [
            "platform.core.search",
            "platform.core.list_indices",
            "platform.core.get_document_by_id",
        ]
    return {
        "id": agent_id,
        "name": name,
        "description": description,
        "labels": labels or ["crm", "elastic-crm"],
        "configuration": {
            "instructions": instructions,
            "tools": [{"tool_ids": tool_ids}],
        },
    }


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
