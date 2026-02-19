"""
Main - Punto de entrada de la aplicación CRM con Elastic.

Ejemplo de uso del sistema multi-agente integrado con Elasticsearch
y Elastic Agent Builder.
"""

import asyncio
import signal
from typing import Optional

from loguru import logger

from orchestrator import CRMOrchestrator
from elastic import (
    elastic_client,
    CustomerRepository,
    TicketRepository,
    InteractionRepository,
    CampaignRepository,
    create_elastic_sales_agent,
    create_elastic_support_agent,
    create_elastic_marketing_agent,
    Customer,
    Ticket,
    Interaction,
)
from utils.logger import setup_logger
from config import config


class ElasticCRMApplication:
    """
    Aplicación CRM Multi-Agente con integración Elastic.
    """

    def __init__(self):
        self.orchestrator: Optional[CRMOrchestrator] = None
        self._shutdown_event = asyncio.Event()
        
        # Repositorios Elastic
        self.customer_repo: Optional[CustomerRepository] = None
        self.ticket_repo: Optional[TicketRepository] = None
        self.interaction_repo: Optional[InteractionRepository] = None
        self.campaign_repo: Optional[CampaignRepository] = None

    async def initialize(self) -> None:
        """Inicializa la aplicación, Elastic y registra agentes."""
        setup_logger(level=config.log_level)
        logger.info("Iniciando Elastic CRM Multi-Agente...")

        # Verificar conexión con Elastic
        connected = await elastic_client.ping()
        if not connected:
            logger.warning("No se pudo conectar a Elasticsearch. Continuando en modo limitado.")
        else:
            logger.info("Conectado a Elasticsearch")

        # Inicializar repositorios
        self.customer_repo = CustomerRepository()
        self.ticket_repo = TicketRepository()
        self.interaction_repo = InteractionRepository()
        self.campaign_repo = CampaignRepository()

        # Crear índices en Elastic
        await self._initialize_indices()

        # Crear orquestador
        self.orchestrator = CRMOrchestrator()

        # Crear y registrar agentes Elastic
        agents = [
            create_elastic_sales_agent(),
            create_elastic_support_agent(),
            create_elastic_marketing_agent(),
        ]

        for agent in agents:
            await self.orchestrator.register_agent(agent)
            logger.info(f"Agente Elastic registrado: {agent.name}")

        logger.info("Elastic CRM Multi-Agente inicializado correctamente")

    async def _initialize_indices(self) -> None:
        """Inicializa índices de Elasticsearch."""
        try:
            await self.customer_repo.initialize()
            await self.ticket_repo.initialize()
            await self.interaction_repo.initialize()
            await self.campaign_repo.initialize()
            logger.info("Índices de Elastic inicializados")
        except Exception as e:
            logger.warning(f"Error inicializando índices: {e}")

    async def run_demo(self) -> None:
        """Ejecuta una demostración de las capacidades del sistema."""
        logger.info("=== Iniciando Demostración Elastic CRM ===")

        # 1. Agregar clientes a Elasticsearch
        logger.info("1. Agregando clientes a Elasticsearch...")
        customers_data = [
            Customer(
                name="Juan Pérez",
                email="juan@example.com",
                phone="+1234567890",
                company="TechCorp",
                status="lead",
                lead_score=75,
                tags=["enterprise", "hot_lead"],
            ),
            Customer(
                name="María García",
                email="maria@example.com",
                phone="+0987654321",
                company="DataSoft",
                status="prospect",
                lead_score=60,
                engagement_score=45,
                tags=["smb", "warm"],
            ),
            Customer(
                name="Carlos López",
                email="carlos@example.com",
                phone="+1122334455",
                company="CloudInc",
                status="customer",
                lifetime_value=15000.0,
                engagement_score=85,
                tags=["enterprise", "champion"],
            ),
        ]

        for customer in customers_data:
            await self.customer_repo.create(customer)
            logger.info(f"Cliente agregado a Elastic: {customer.name}")

        # Esperar a que Elastic indexe
        await asyncio.sleep(1)

        # 2. Búsqueda en Elasticsearch
        logger.info("\n2. Búsqueda en Elasticsearch...")
        results = await self.customer_repo.search({"match_all": {}})
        logger.info(f"Clientes en Elastic: {len(results)}")

        # Búsqueda específica
        juan_results = await self.customer_repo.find_by_email("juan@example.com")
        if juan_results:
            logger.info(f"Encontrado: {juan_results.name} (Lead Score: {juan_results.lead_score})")

        # 3. Agente Elastic - Analizar cliente con contexto de Elastic
        logger.info("\n3. Agente Elastic - Analizando cliente con RAG...")
        sales_agent = self.orchestrator.get_agent("elastic_sales_agent")
        if sales_agent and juan_results:
            result = await sales_agent.execute({
                "action": "analyze",
                "customer_id": juan_results.customer_id,
                "include_interactions": False,
                "include_tickets": False,
            })
            logger.info(f"Análisis completado: {result.data}")

        # 4. Crear ticket en Elasticsearch
        logger.info("\n4. Creando ticket en Elasticsearch...")
        ticket = Ticket(
            customer_id=juan_results.customer_id if juan_results else "unknown",
            subject="Consulta sobre pricing enterprise",
            description="El cliente necesita información sobre planes enterprise",
            status="open",
            priority="medium",
            category="sales",
            channel="email",
        )
        await self.ticket_repo.create(ticket)
        logger.info(f"Ticket creado en Elastic: {ticket.ticket_id}")

        # 5. Registrar interacción
        logger.info("\n5. Registrando interacción en Elasticsearch...")
        interaction = Interaction(
            customer_id=juan_results.customer_id if juan_results else "unknown",
            interaction_type="email",
            direction="inbound",
            subject="Re: Consulta pricing",
            content="Cliente interesado en plan enterprise",
            outcome="interested",
            next_action="schedule_demo",
            channel="email",
        )
        await self.interaction_repo.create(interaction)
        logger.info(f"Interacción registrada: {interaction.interaction_id}")

        # 6. Agente Elastic - Búsqueda semántica
        logger.info("\n6. Agente Elastic - Búsqueda semántica...")
        support_agent = self.orchestrator.get_agent("elastic_support_agent")
        if support_agent:
            result = await support_agent.execute({
                "action": "search",
                "query": "cliente enterprise interesado pricing",
                "top_k": 5,
            })
            logger.info(f"Búsqueda semántica: {result.data.get('total_found', 0)} resultados")

        # 7. Agregaciones en Elasticsearch
        logger.info("\n7. Agregaciones en Elasticsearch...")
        agg_results = await self.customer_repo.aggregate({
            "status_agg": {
                "terms": {"field": "status"}
            },
            "avg_lead_score": {
                "avg": {"field": "lead_score"}
            }
        })
        logger.info(f"Agregaciones: {agg_results}")

        # 8. Mostrar estado del sistema
        logger.info("\n8. Estado del sistema:")
        status = self.orchestrator.get_status()
        logger.info(f"Agentes Elastic registrados: {status['agents_count']}")
        
        customer_count = await self.customer_repo.count()
        ticket_count = await self.ticket_repo.count()
        interaction_count = await self.interaction_repo.count()
        
        logger.info(f"Clientes en Elastic: {customer_count}")
        logger.info(f"Tickets en Elastic: {ticket_count}")
        logger.info(f"Interacciones en Elastic: {interaction_count}")

        logger.info("\n=== Demostración Elastic CRM Completada ===")

    async def run(self) -> None:
        """Ejecuta la aplicación."""
        await self.initialize()
        await self.run_demo()

    async def shutdown(self) -> None:
        """Aplica el shutdown graceful."""
        logger.info("Cerrando aplicación...")
        if self.orchestrator:
            await self.orchestrator.shutdown()
        await elastic_client.close()
        logger.info("Aplicación cerrada")
        self._shutdown_event.set()


async def main():
    """Punto de entrada principal."""
    app = ElasticCRMApplication()
    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Interrupción recibida")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
