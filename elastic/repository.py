"""
Repositorio para operaciones CRUD en Elasticsearch.
"""

from typing import Any, Generic, Optional, TypeVar
from datetime import datetime
from loguru import logger

from elastic.client import elastic_client
from elastic.models import Customer, Ticket, Interaction, Campaign

T = TypeVar("T")


class ElasticRepository(Generic[T]):
    """
    Repositorio genérico para operaciones CRUD en Elasticsearch.
    
    Proporciona una capa de abstracción sobre el cliente de Elastic.
    """

    def __init__(self, index_name: str, model_class: type[T]):
        self.index_name = index_name
        self.model_class = model_class
        self._initialized = False

    async def initialize(self) -> bool:
        """
        Inicializa el índice con el mapping del modelo.
        
        Returns:
            True si la inicialización fue exitosa.
        """
        if self._initialized:
            return True

        try:
            mapping = self.model_class.get_mapping()
            success = await elastic_client.create_index(self.index_name, mapping)
            self._initialized = success
            return success
        except Exception as e:
            logger.error(f"Failed to initialize index {self.index_name}: {e}")
            return False

    async def create(self, entity: T) -> Optional[str]:
        """
        Crea un nuevo documento.
        
        Args:
            entity: Entidad a crear.
            
        Returns:
            ID del documento creado o None si falló.
        """
        try:
            doc = entity.to_dict()
            # Obtener ID desde la entidad
            doc_id = getattr(entity, f"{self.model_class.__name__.lower()}_id", None)
            if not doc_id:
                doc_id = getattr(entity, "id", None)
            
            result = await elastic_client.async_client.index(
                index=self.index_name,
                id=doc_id,
                document=doc,
                refresh=True,
            )
            logger.debug(f"Created document {result['_id']} in {self.index_name}")
            return result["_id"]
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            return None

    async def get(self, doc_id: str) -> Optional[T]:
        """
        Obtiene un documento por ID.
        
        Args:
            doc_id: ID del documento.
            
        Returns:
            Entidad o None si no existe.
        """
        try:
            result = await elastic_client.async_client.get(
                index=self.index_name,
                id=doc_id,
                ignore=[404],
            )
            if result.get("found"):
                return self.model_class.from_dict(result["_source"])
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None

    async def update(self, doc_id: str, updates: dict) -> bool:
        """
        Actualiza un documento parcialmente.
        
        Args:
            doc_id: ID del documento.
            updates: Campos a actualizar.
            
        Returns:
            True si la actualización fue exitosa.
        """
        try:
            updates["updated_at"] = datetime.now().isoformat()
            await elastic_client.async_client.update(
                index=self.index_name,
                id=doc_id,
                doc=updates,
                refresh=True,
            )
            logger.debug(f"Updated document {doc_id} in {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            return False

    async def delete(self, doc_id: str) -> bool:
        """
        Elimina un documento.
        
        Args:
            doc_id: ID del documento a eliminar.
            
        Returns:
            True si la eliminación fue exitosa.
        """
        try:
            await elastic_client.async_client.delete(
                index=self.index_name,
                id=doc_id,
                refresh=True,
                ignore=[404],
            )
            logger.debug(f"Deleted document {doc_id} from {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            return False

    async def search(
        self,
        query: dict,
        size: int = 10,
        from_: int = 0,
        sort: Optional[list] = None,
    ) -> list[T]:
        """
        Busca documentos con una query de Elasticsearch.
        
        Args:
            query: Query DSL de Elasticsearch.
            size: Número máximo de resultados.
            from_: Offset para paginación.
            sort: Lista de criterios de ordenamiento.
            
        Returns:
            Lista de entidades encontradas.
        """
        try:
            body = {"query": query, "size": size, "from": from_}
            if sort:
                body["sort"] = sort

            result = await elastic_client.async_client.search(
                index=self.index_name,
                body=body,
            )
            
            hits = result.get("hits", {}).get("hits", [])
            return [self.model_class.from_dict(hit["_source"]) for hit in hits]
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    async def count(self, query: Optional[dict] = None) -> int:
        """
        Cuenta documentos que matchean una query.
        
        Args:
            query: Query DSL de Elasticsearch (opcional, cuenta todos si es None).
            
        Returns:
            Número de documentos.
        """
        try:
            body = {"query": query} if query else {}
            result = await elastic_client.async_client.count(
                index=self.index_name,
                body=body,
            )
            return result.get("count", 0)
        except Exception as e:
            logger.error(f"Count failed: {e}")
            return 0

    async def aggregate(self, aggregation: dict) -> dict:
        """
        Ejecuta una agregación.
        
        Args:
            aggregation: Definición de agregación.
            
        Returns:
            Resultados de la agregación.
        """
        try:
            result = await elastic_client.async_client.search(
                index=self.index_name,
                body={"size": 0, "aggs": aggregation},
            )
            return result.get("aggregations", {})
        except Exception as e:
            logger.error(f"Aggregation failed: {e}")
            return {}

    async def bulk_create(self, entities: list[T]) -> int:
        """
        Crea múltiples documentos en batch.
        
        Args:
            entities: Lista de entidades a crear.
            
        Returns:
            Número de documentos creados exitosamente.
        """
        try:
            from elasticsearch import helpers
            
            actions = []
            for entity in entities:
                doc = entity.to_dict()
                doc_id = getattr(entity, f"{self.model_class.__name__.lower()}_id", None)
                if not doc_id:
                    doc_id = getattr(entity, "id", None)
                
                action = {
                    "_index": self.index_name,
                    "_source": doc,
                }
                if doc_id:
                    action["_id"] = doc_id
                actions.append(action)

            success, failed = await helpers.async_bulk(
                elastic_client.async_client,
                actions,
                refresh=True,
                raise_on_error=False,
            )
            
            logger.info(f"Bulk created {success} documents, {len(failed) if isinstance(failed, list) else failed} failed")
            return success
        except Exception as e:
            logger.error(f"Bulk create failed: {e}")
            return 0


# Repositorios específicos
class CustomerRepository(ElasticRepository[Customer]):
    """Repositorio específico para Customer."""
    
    def __init__(self):
        super().__init__("crm_customers", Customer)

    async def find_by_email(self, email: str) -> Optional[Customer]:
        """Busca un cliente por email."""
        results = await self.search({"term": {"email": email}})
        return results[0] if results else None

    async def find_by_status(self, status: str) -> list[Customer]:
        """Busca clientes por estado."""
        return await self.search({"term": {"status": status}})

    async def search_by_name(self, name: str) -> list[Customer]:
        """Busca clientes por nombre (búsqueda fuzzy)."""
        return await self.search({
            "multi_match": {
                "query": name,
                "fields": ["name^2", "company", "email"],
                "fuzziness": "AUTO",
            }
        })


class TicketRepository(ElasticRepository[Ticket]):
    """Repositorio específico para Ticket."""
    
    def __init__(self):
        super().__init__("crm_tickets", Ticket)

    async def find_by_customer(self, customer_id: str) -> list[Ticket]:
        """Busca tickets de un cliente."""
        return await self.search({"term": {"customer_id": customer_id}})

    async def find_open_tickets(self) -> list[Ticket]:
        """Busca tickets abiertos."""
        return await self.search({"term": {"status": "open"}})

    async def find_overdue_tickets(self) -> list[Ticket]:
        """Busca tickets con SLA vencido."""
        return await self.search({
            "bool": {
                "must": [
                    {"term": {"status": "open"}},
                    {"range": {"sla_deadline": {"lt": "now"}}}
                ]
            }
        })


class InteractionRepository(ElasticRepository[Interaction]):
    """Repositorio específico para Interaction."""
    
    def __init__(self):
        super().__init__("crm_interactions", Interaction)

    async def find_by_customer(self, customer_id: str) -> list[Interaction]:
        """Busca interacciones de un cliente."""
        return await self.search(
            {"term": {"customer_id": customer_id}},
            sort=[{"occurred_at": {"order": "desc"}}],
        )

    async def find_recent(self, customer_id: str, days: int = 7) -> list[Interaction]:
        """Busca interacciones recientes de un cliente."""
        return await self.search({
            "bool": {
                "must": [
                    {"term": {"customer_id": customer_id}},
                    {"range": {"occurred_at": {"gte": f"now-{days}d"}}}
                ]
            }
        })


class CampaignRepository(ElasticRepository[Campaign]):
    """Repositorio específico para Campaign."""
    
    def __init__(self):
        super().__init__("crm_campaigns", Campaign)

    async def find_active(self) -> list[Campaign]:
        """Busca campañas activas."""
        return await self.search({"term": {"status": "active"}})

    async def find_by_segment(self, segment: str) -> list[Campaign]:
        """Busca campañas por segmento."""
        return await self.search({"term": {"target_segment": segment}})
