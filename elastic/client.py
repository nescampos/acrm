"""
Cliente de conexión a Elasticsearch.
"""

import asyncio
from typing import Any, Optional
from elasticsearch import AsyncElasticsearch, Elasticsearch
from loguru import logger

from config import config


class ElasticClient:
    """
    Cliente singleton para conexión a Elasticsearch.
    
    Proporciona conexión síncrona y asíncrona al cluster Elastic.
    """

    _instance: Optional["ElasticClient"] = None
    _async_client: Optional[AsyncElasticsearch] = None
    _sync_client: Optional[Elasticsearch] = None

    def __new__(cls) -> "ElasticClient":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

    def _get_connection_params(self) -> dict:
        """Obtiene parámetros de conexión desde configuración."""
        return {
             "hosts":[config.get("ELASTIC_HOST")],
             "api_key":config.get("ELASTIC_CLOUD_API_KEY"),
        }

    @property
    def async_client(self) -> AsyncElasticsearch:
        """Obtiene cliente asíncrono."""
        if self._async_client is None:
            params = self._get_connection_params()
            print(params)
            self._async_client = AsyncElasticsearch(**params)
            logger.info("Async Elasticsearch client created")
        return self._async_client

    @property
    def sync_client(self) -> Elasticsearch:
        """Obtiene cliente síncrono."""
        if self._sync_client is None:
            params = self._get_connection_params()
            self._sync_client = Elasticsearch(**params)
            logger.info("Sync Elasticsearch client created")
        return self._sync_client

    async def ping(self) -> bool:
        """Verifica conexión con el cluster."""
        try:
            info = await self.async_client.info()
            logger.info(f"Connected to Elastic cluster: {info['version']['number']}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Elastic: {e}")
            return False

    async def close(self) -> None:
        """Cierra las conexiones."""
        if self._async_client:
            await self._async_client.close()
            self._async_client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
        logger.info("Elasticsearch clients closed")

    async def create_index(self, index_name: str, mapping: dict) -> bool:
        """
        Crea un índice con mapping específico.
        
        Args:
            index_name: Nombre del índice.
            mapping: Definición del mapping.
            
        Returns:
            True si se creó o ya existía.
        """
        try:
            exists = await self.async_client.indices.exists(index=index_name)
            if exists:
                logger.info(f"Index {index_name} already exists")
                return True
            
            await self.async_client.indices.create(
                index=index_name,
                body=mapping
            )
            logger.info(f"Index {index_name} created")
            return True
        except Exception as e:
            logger.error(f"Failed to create index {index_name}: {e}")
            return False

    async def delete_index(self, index_name: str) -> bool:
        """Elimina un índice."""
        try:
            await self.async_client.indices.delete(index=index_name, ignore=[400, 404])
            logger.info(f"Index {index_name} deleted")
            return True
        except Exception as e:
            logger.error(f"Failed to delete index {index_name}: {e}")
            return False

    async def refresh_index(self, index_name: str) -> None:
        """Refresca un índice para hacer visibles los cambios."""
        await self.async_client.indices.refresh(index=index_name)


# Instancia global
elastic_client = ElasticClient()
