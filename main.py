"""
Main - Punto de entrada de la aplicación.

Ejemplo de uso del sistema multi-agente CRM.
"""

import asyncio
import signal
from typing import Optional

from loguru import logger

from orchestrator import CRMOrchestrator
from agents.specialized import SalesAgent, SupportAgent, MarketingAgent
from utils.logger import setup_logger
from config import config


class CRMApplication:
    """
    Aplicación principal del CRM Multi-Agente.
    """

    def __init__(self):
        self.orchestrator: Optional[CRMOrchestrator] = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self) -> None:
        """Inicializa la aplicación y registra todos los agentes."""
        setup_logger(level=config.log_level)
        logger.info("Iniciando CRM Multi-Agente...")

        # Crear orquestador
        self.orchestrator = CRMOrchestrator()

        # Crear y registrar agentes
        agents = [
            SalesAgent(config={"auto_qualify": True}),
            SupportAgent(config={"auto_classify": True}),
            MarketingAgent(config={"auto_segment": True}),
        ]

        for agent in agents:
            await self.orchestrator.register_agent(agent)
            logger.info(f"Agente registrado: {agent.name}")

        logger.info("CRM Multi-Agente inicializado correctamente")

    async def run_demo(self) -> None:
        """Ejecuta una demostración de las capacidades del sistema."""
        logger.info("=== Iniciando Demostración ===")

        # 1. Agregar clientes de ejemplo
        logger.info("1. Agregando clientes al CRM...")
        customers = [
            {
                "name": "Juan Pérez",
                "email": "juan@example.com",
                "phone": "+1234567890",
                "status": "lead",
            },
            {
                "name": "María García",
                "email": "maria@example.com",
                "phone": "+0987654321",
                "status": "prospect",
            },
            {
                "name": "Carlos López",
                "email": "carlos@example.com",
                "phone": "+1122334455",
                "status": "customer",
            },
        ]

        for cust_data in customers:
            customer = self.orchestrator.add_customer(cust_data)
            logger.info(f"Cliente agregado: {customer.name} (ID: {customer.customer_id[:8]}...)")

        # 2. Agente de Ventas - Calificar lead
        logger.info("\n2. Agente de Ventas - Calificando lead...")
        sales_agent = self.orchestrator.get_agent("sales_agent")
        if sales_agent:
            result = await sales_agent.execute({
                "action": "qualify_lead",
                "customer_id": customers[0]["email"],
                "data": {
                    "budget": 5000,
                    "has_authority": True,
                    "need_score": 80,
                    "timeline": "this_month",
                },
            })
            logger.info(f"Calificación: {result.data}")

        # 3. Agente de Soporte - Crear ticket
        logger.info("\n3. Agente de Soporte - Creando ticket...")
        support_agent = self.orchestrator.get_agent("support_agent")
        if support_agent:
            result = await support_agent.execute({
                "action": "create_ticket",
                "customer_id": customers[1]["email"],
                "subject": "Problema con login",
                "description": "No puedo acceder a mi cuenta, dice que mi contraseña es incorrecta",
                "channel": "email",
            })
            logger.info(f"Ticket creado: {result.data}")

        # 4. Agente de Marketing - Segmentar audiencia
        logger.info("\n4. Agente de Marketing - Segmentando audiencia...")
        marketing_agent = self.orchestrator.get_agent("marketing_agent")
        if marketing_agent:
            customer_list = [
                {
                    "customer_id": c["email"],
                    "days_since_signup": 15 if i == 0 else 60 if i == 1 else 180,
                    "total_purchases": 0 if i == 0 else 2 if i == 1 else 8,
                    "days_since_last_activity": 5 if i == 0 else 45 if i == 1 else 10,
                }
                for i, c in enumerate(customers)
            ]
            result = await marketing_agent.execute({
                "action": "segment",
                "criteria": "behavior",
                "customers": customer_list,
            })
            logger.info(f"Segmentación: {result.data}")

        # 5. Mostrar estado del sistema
        logger.info("\n5. Estado del sistema:")
        status = self.orchestrator.get_status()
        logger.info(f"Agentes registrados: {status['agents_count']}")
        logger.info(f"Clientes en CRM: {status['customers_count']}")
        logger.info(f"Estado de agentes: {status['agents']}")

        logger.info("\n=== Demostración Completada ===")

    async def run(self) -> None:
        """Ejecuta la aplicación."""
        await self.initialize()
        await self.run_demo()

    async def shutdown(self) -> None:
        """Aplica el shutdown graceful."""
        logger.info("Cerrando aplicación...")
        if self.orchestrator:
            await self.orchestrator.shutdown()
        logger.info("Aplicación cerrada")
        self._shutdown_event.set()

    async def run_interactive(self) -> None:
        """
        Ejecuta la aplicación en modo interactivo.
        Mantiene el proceso vivo para recibir tareas.
        """
        await self.initialize()

        # Configurar signal handlers
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown()),
            )

        # Iniciar procesador de cola en background
        queue_task = asyncio.create_task(self.orchestrator.process_queue())

        logger.info("Sistema listo. Presiona Ctrl+C para salir.")

        # Mantener ejecución
        await self._shutdown_event.wait()
        queue_task.cancel()
        try:
            await queue_task
        except asyncio.CancelledError:
            pass


async def main():
    """Punto de entrada principal."""
    app = CRMApplication()
    try:
        await app.run()
    except KeyboardInterrupt:
        logger.info("Interrupción recibida")
    finally:
        await app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
