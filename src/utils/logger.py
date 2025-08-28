"""Logging utilities using Loguru."""

import sys
from pathlib import Path
from loguru import logger
from config.settings import settings


def setup_logger():
    """Setup logger configuration with file and console output."""
    
    # Remove default logger
    logger.remove()
    
    # Ensure logs directory exists
    log_path = Path(settings.logging.file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Console handler
    logger.add(
        sys.stdout,
        level=settings.logging.level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        colorize=True
    )
    
    # File handler
    logger.add(
        settings.logging.file_path,
        level=settings.logging.level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation=settings.logging.rotation,
        retention=settings.logging.retention,
        compression="gz",
        backtrace=True,
        diagnose=True
    )
    
    return logger


def get_logger(name: str = None):
    """Get a logger instance."""
    if name:
        return logger.bind(name=name)
    return logger


# Initialize logger on import
setup_logger()