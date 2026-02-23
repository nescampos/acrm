"""
Módulo de configuración del sistema.
"""

import os
from pathlib import Path
from typing import Any, Optional
from dotenv import load_dotenv
import yaml


class Config:
    """
    Gestiona la configuración del sistema.

    Carga configuración desde:
    1. Variables de entorno (.env)
    2. Archivo config.yaml
    3. Valores por defecto
    """

    _instance: Optional["Config"] = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._load_env()
        self._load_config_file()
        self._initialized = True

    def _load_env(self) -> None:
        """Carga variables de entorno desde .env"""
        # Buscar .env en directorio raíz
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()

    def _load_config_file(self) -> None:
        """Carga configuración desde config.yaml"""
        config_path = Path(__file__).parent.parent / "config" / "config.yaml"
        self.file_config = {}

        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                self.file_config = yaml.safe_load(f) or {}

    def get(self, key: str, default: Any = None) -> Any:
        """
        Obtiene un valor de configuración.

        Primero busca en variables de entorno, luego en config.yaml.
        """
        # Buscar en variables de entorno
        env_value = os.getenv(key)
        if env_value is not None:
            return env_value

        # Buscar en config file (soporta keys anidadas con .)
        keys = key.split(".")
        value = self.file_config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                value = None
                break

        return value if value is not None else default

    def get_int(self, key: str, default: int = 0) -> int:
        """Obtiene un valor entero de configuración."""
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, key: str, default: float = 0.0) -> float:
        """Obtiene un valor flotante de configuración."""
        value = self.get(key, default)
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Obtiene un valor booleano de configuración."""
        value = self.get(key, str(default)).lower()
        return value in ("true", "1", "yes", "on")

    # Propiedades LLM
    @property
    def llm_provider(self) -> str:
        """Proveedor LLM configurado."""
        return self.get("LLM_PROVIDER", "openai")

    @property
    def llm_model(self) -> str:
        """Modelo LLM configurado."""
        return self.get("LLM_MODEL", "gpt-4o")

    @property
    def temperature(self) -> float:
        """Temperatura para generación LLM."""
        return self.get_float("TEMPERATURE", 0.7)

    @property
    def log_level(self) -> str:
        """Nivel de logging."""
        return self.get("LOG_LEVEL", "INFO")

    # Propiedades Elastic
    @property
    def elastic_host(self) -> str:
        """Host de Elasticsearch."""
        return self.get("ELASTIC_HOST", "http://localhost:9200")

    @property
    def elastic_user(self) -> str:
        """Usuario de Elasticsearch."""
        return self.get("ELASTIC_USER", "elastic")

    @property
    def elastic_password(self) -> str:
        """Contraseña de Elasticsearch."""
        return self.get("ELASTIC_PASSWORD", "changeme")

    @property
    def elastic_verify_certs(self) -> bool:
        """Verificar certificados SSL de Elastic."""
        return self.get_bool("ELASTIC_VERIFY_CERTS", False)

    @property
    def elastic_timeout(self) -> int:
        """Timeout para conexiones a Elastic."""
        return self.get_int("ELASTIC_TIMEOUT", 30)

    @property
    def elastic_cloud_api_key(self) -> str:
        """API Key de Elasticsearch Cloud."""
        return self.get("ELASTIC_CLOUD_API_KEY")

    @property
    def kibana_host(self) -> str:
        """Host de Kibana (para Agent Builder API)."""
        return self.get("KIBANA_HOST") or self.get("kibana.host", "http://localhost:5601")

    @property
    def kibana_space(self) -> str:
        """Space de Kibana (vacío = default)."""
        return self.get("KIBANA_SPACE") or self.get("kibana.space", "")


# Instancia global
config = Config()
