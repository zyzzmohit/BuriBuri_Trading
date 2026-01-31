"""
broker/__init__.py

Broker adapters for portfolio data access.
Supports both Mock (default) and Alpaca (paper trading) modes.
"""

from .mock_adapter import MockAdapter

__all__ = ["MockAdapter"]
