"""
Clase base para herramientas de agentes.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional


class BaseTool(ABC):
    """
    Clase base para herramientas que pueden usar los agentes.
    
    Las herramientas son funciones reutilizables que los agentes
    pueden invocar para realizar acciones específicas.
    """

    def __init__(self, name: Optional[str] = None, description: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.description = description or ""

    @property
    @abstractmethod
    def definition(self) -> dict:
        """
        Retorna la definición de la herramienta para el LLM.
        
        Debe incluir:
        - name: Nombre de la herramienta
        - description: Descripción de lo que hace
        - parameters: Schema de parámetros esperados
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        Ejecuta la herramienta con los parámetros dados.
        
        Args:
            **kwargs: Parámetros de ejecución.
            
        Returns:
            Resultado de la ejecución.
        """
        pass

    def validate_input(self, input_data: dict) -> tuple[bool, Optional[str]]:
        """
        Valida los datos de entrada.
        
        Args:
            input_data: Datos a validar.
            
        Returns:
            Tuple (es_valido, mensaje_error)
        """
        return True, None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name})"
