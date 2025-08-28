"""Data collectors package for different tech sites."""

from .base import BaseCollector
from .tecmundo import TecmundoCollector

__all__ = ["BaseCollector", "TecmundoCollector"]