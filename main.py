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
    Campaign,
)
from elastic.kibana_agent_builder_client import KibanaAgentBuilderClient
from utils.logger import setup_logger
from config import config
from demo_data import get_all_demo_data


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
        logger.info("Starting Elastic CRM Multi-Agent...")

        # Verificar conexión con Elastic
        connected = await elastic_client.ping()
        if not connected:
            logger.warning("Unable to connect to Elasticsearch. Continuing in limited mode.")
        else:
            logger.info("Connected to Elasticsearch")

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
                logger.info(f"Registered Kibana Agent: {agent.name}")
        except RuntimeError as e:
            logger.error(str(e))
            raise

        logger.info("Elastic CRM Multi-Agent initialized successfully")

    async def _initialize_indices(self) -> None:
        """Inicializa índices de Elasticsearch."""
        try:
            await self.customer_repo.initialize()
            await self.ticket_repo.initialize()
            await self.interaction_repo.initialize()
            await self.campaign_repo.initialize()
            logger.info("Initialized Elastic indices")
        except Exception as e:
            logger.warning(f"Error initializing indices: {e}")

    async def run_demo(self) -> None:
        """Run a demo of the system capabilities."""
        logger.info("=== Starting demo Elastic CRM ===")

        # Get demo data
        customers_data, tickets_data, interactions_data, campaigns_data = get_all_demo_data()

        # 1. Add customers to Elasticsearch
        logger.info("1. Adding customers to Elasticsearch...")
        for customer in customers_data:
            await self.customer_repo.create(customer)
            logger.info(f"Customer added to Elastic: {customer.name}")

        # 2. Add tickets to Elasticsearch
        logger.info("\n2. Adding tickets to Elasticsearch...")
        for ticket in tickets_data:
            # Assign random customer_id from created customers
            import random
            ticket.customer_id = random.choice([c.customer_id for c in customers_data])
            await self.ticket_repo.create(ticket)
            logger.info(f"Ticket added to Elastic: {ticket.subject}")

        # 3. Add interactions to Elasticsearch
        logger.info("\n3. Adding interactions to Elasticsearch...")
        for interaction in interactions_data:
            # Assign random customer_id
            import random
            interaction.customer_id = random.choice([c.customer_id for c in customers_data])
            await self.interaction_repo.create(interaction)
            logger.info(f"Interaction added to Elastic: {interaction.interaction_type}")

        # 4. Add campaigns to Elasticsearch
        logger.info("\n4. Adding campaigns to Elasticsearch...")
        for campaign in campaigns_data:
            await self.campaign_repo.create(campaign)
            logger.info(f"Campaign added to Elastic: {campaign.name}")

        # Wait for Elasticsearch to index
        await asyncio.sleep(1)

        # 5. Search in Elasticsearch
        logger.info("\n5. Search in Elasticsearch...")
        results = await self.customer_repo.search({"match_all": {}})
        logger.info(f"Customers in Elastic: {len(results)}")

        # Specific search
        juan_results = await self.customer_repo.find_by_email("juan.perez@techcorp.com")
        if juan_results:
            logger.info(f"Found: {juan_results.name} (Lead Score: {juan_results.lead_score})")


        # 6. System status
        logger.info("\n6. System status:")
        status = self.orchestrator.get_status()
        logger.info(f"Kibana agents registered: {status['agents_count']}")
        
        customer_count = await self.customer_repo.count()
        ticket_count = await self.ticket_repo.count()
        interaction_count = await self.interaction_repo.count()
        campaign_count = await self.campaign_repo.count()
        
        logger.info(f"Customers in Elastic: {customer_count}")
        logger.info(f"Tickets in Elastic: {ticket_count}")
        logger.info(f"Interactions in Elastic: {interaction_count}")
        logger.info(f"Campaigns in Elastic: {campaign_count}")

        logger.info("\n=== Elastic CRM Demo Completed ===")

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

        logger.info("Chat mode started. Commands: /agents, /exit")
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
                    
                    # Extract the message from the response of the Kibana agent
                    output = self._extract_message_from_response(payload)
                    
                    print(f"[{agent_name}] {output}")
                else:
                    print(f"[{agent_name}] ERROR: {result.error}")
            except Exception as e:
                print(f"[error] {e}")

    async def shutdown(self) -> None:
        """Aplica el shutdown graceful."""
        logger.info("Closing application...")
        if self.orchestrator:
            await self.orchestrator.shutdown()
        if self._kibana_client:
            await self._kibana_client.close()
        await elastic_client.close()
        logger.info("Application closed")
        self._shutdown_event.set()

    def _extract_message_from_response(self, payload: dict) -> str:
        """
        Extract the message from the response of the Kibana agent.
        
        The response from Kibana has the format:
        {
            "response": {
                "message": "content of the message"
            },
            ...
        }
        """
        
        if not isinstance(payload, dict):
            return json.dumps(payload, ensure_ascii=False, indent=2)
        
        # Buscar el mensaje en response.message (formato de Kibana)
        if "response" in payload and isinstance(payload["response"], dict):
            message = payload["response"].get("message")
            if isinstance(message, str):
                return message
        
        # Fallback: buscar message directo
        message = payload.get("message")
        if isinstance(message, str):
            return message
        
        # Si no hay mensaje, retornar el payload completo
        return json.dumps(payload, ensure_ascii=False, indent=2)


async def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--demo",
        action="store_true",
        help="Run the demo that inserts data into Elasticsearch",
    )
    group.add_argument(
        "--chat",
        action="store_true",
        help="Run the chat mode in console (routing + Kibana agents)",
    )
    args = parser.parse_args()
    app = ElasticCRMApplication()
    try:
        if args.chat:
            await app.run_chat()
        else:
            await app.run(run_demo=args.demo)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
