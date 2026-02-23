"""
Main - Punto de entrada de la aplicación CRM con Elastic.

Ejemplo de uso del sistema multi-agente integrado con Elasticsearch
y Elastic Agent Builder.
"""
import argparse
import asyncio
import signal
import json
from typing import Optional

from loguru import logger

from orchestrator import CRMOrchestrator
from elastic import (
    elastic_client,
    CustomerRepository,
    TicketRepository,
    InteractionRepository,
    CampaignRepository,
    create_and_register_crm_agents,
    Customer,
    Ticket,
    Interaction,
)
from elastic.kibana_agent_builder_client import KibanaAgentBuilderClient
from utils.logger import setup_logger
from config import config


class ElasticCRMApplication:
    """
    Aplicación CRM Multi-Agente con integración Elastic.
    """

    def __init__(self):
        self.orchestrator: Optional[CRMOrchestrator] = None
        self._shutdown_event = asyncio.Event()
        self._kibana_client: Optional[KibanaAgentBuilderClient] = None

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

        # Crear agentes en Kibana (igual que los índices) y registrar wrappers
        try:
            agents, self._kibana_client = await create_and_register_crm_agents()
            for agent in agents:
                await self.orchestrator.register_agent(agent)
                logger.info(f"Agente Kibana registrado: {agent.name}")
        except RuntimeError as e:
            logger.error(str(e))
            raise

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

        # 3. Agente Kibana Ventas - Analizar cliente
        logger.info("\n3. Agente Kibana Ventas - Analizando cliente...")
        sales_agent = self.orchestrator.get_agent("crm_sales_agent")
        if sales_agent and juan_results:
            result = await sales_agent.execute({
                "input": (
                    f"Analiza el cliente con id {juan_results.customer_id} en crm_customers. "
                    "Indica health score y recomendaciones basándote en los datos."
                ),
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

        # 6. Agente Kibana Soporte - Búsqueda
        logger.info("\n6. Agente Kibana Soporte - Búsqueda...")
        support_agent = self.orchestrator.get_agent("crm_support_agent")
        if support_agent:
            result = await support_agent.execute({
                "input": (
                    "Busca en los índices crm_customers y crm_interactions "
                    "clientes enterprise interesados en pricing. Resúmeme hasta 5 resultados."
                ),
            })
            logger.info(f"Búsqueda: {result.data}")

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
        logger.info(f"Agentes Kibana registrados: {status['agents_count']}")
        
        customer_count = await self.customer_repo.count()
        ticket_count = await self.ticket_repo.count()
        interaction_count = await self.interaction_repo.count()
        
        logger.info(f"Clientes en Elastic: {customer_count}")
        logger.info(f"Tickets en Elastic: {ticket_count}")
        logger.info(f"Interacciones en Elastic: {interaction_count}")

        logger.info("\n=== Demostración Elastic CRM Completada ===")

    async def run(self, run_demo: bool = False) -> None:
        """Ejecuta la aplicación."""
        await self.initialize()
        if run_demo:
            await self.run_demo()

    async def run_chat(self) -> None:
        """
        Modo consola interactivo.

        - Rutea cada mensaje con OpenAI (router del orquestador)
        - Ejecuta el agente Kibana correspondiente
        - Mantiene conversation_id por agente cuando Kibana lo devuelve
        """
        await self.initialize()
        assert self.orchestrator is not None

        logger.info("Modo chat iniciado. Comandos: /agents, /exit")
        conversation_ids: dict[str, str] = {}

        while True:
            try:
                user_input = await asyncio.to_thread(input, "crm> ")
            except EOFError:
                break

            user_input = (user_input or "").strip()
            if not user_input:
                continue
            if user_input.lower() in ("/exit", "/quit"):
                break
            if user_input.lower() == "/agents":
                agents = self.orchestrator.list_agents()
                print(json.dumps(agents, ensure_ascii=False, indent=2))
                continue

            try:
                route = await self.orchestrator.route_agent(user_input)
                agent_name = route.agent_name
                conv_id = conversation_ids.get(agent_name)

                result = await self.orchestrator.execute_on_agent(
                    agent_name=agent_name,
                    user_input=user_input,
                    conversation_id=conv_id,
                )

                if result.success and isinstance(result.data, dict):
                    new_conv = result.data.get("conversation_id") or result.data.get("conversationId")
                    if isinstance(new_conv, str) and new_conv:
                        conversation_ids[agent_name] = new_conv

                if result.success:
                    payload = result.data
                    if isinstance(payload, dict) and isinstance(payload.get("message"), str):
                        output = payload["message"]
                    else:
                        output = json.dumps(payload, ensure_ascii=False, indent=2)
                    print(f"[{agent_name}] {output}")
                else:
                    print(f"[{agent_name}] ERROR: {result.error}")
            except Exception as e:
                print(f"[error] {e}")

    async def shutdown(self) -> None:
        """Aplica el shutdown graceful."""
        logger.info("Cerrando aplicación...")
        if self.orchestrator:
            await self.orchestrator.shutdown()
        if self._kibana_client:
            await self._kibana_client.close()
        await elastic_client.close()
        logger.info("Aplicación cerrada")
        self._shutdown_event.set()


async def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--demo",
        action="store_true",
        help="Ejecutar la demo que inserta datos en Elasticsearch",
    )
    group.add_argument(
        "--chat",
        action="store_true",
        help="Iniciar modo chat en consola (ruteo + agentes Kibana)",
    )
    args = parser.parse_args()
    app = ElasticCRMApplication()
    try:
        if args.chat:
            await app.run_chat()
        else:
            await app.run(run_demo=args.demo)
    except KeyboardInterrupt:
        logger.info("Interrupción recibida")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
