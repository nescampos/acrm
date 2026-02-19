"""
Configuración de logging para el sistema.
"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(
    level: str = "INFO",
    log_file: str = "logs/app.log",
    rotation: str = "10 MB",
    retention: str = "30 days",
) -> None:
    """
    Configura el logger para toda la aplicación.
    
    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Ruta al archivo de log
        rotation: Cuándo rotar el archivo de log
        retention: Cuánto tiempo retener logs antiguos
    """
    # Remover handler por defecto
    logger.remove()

    # Handler para consola
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # Crear directorio de logs si no existe
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Handler para archivo
    logger.add(
        log_file,
        level=level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation=rotation,
        retention=retention,
        compression="zip",
        enqueue=True,  # Thread-safe
    )

    logger.info("Logger initialized")
