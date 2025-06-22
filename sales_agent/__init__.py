"""
Sales Agent Package
File: sales_agent/__init__.py

This package provides comprehensive customer sales capabilities including:
- Customer eligibility analysis for upsell/cross-sell products
- SHAP-based sales factor analysis for personalized insights
- Personalized sales email generation for top products
- Detailed call script creation for sales conversations
- Multi-product campaign management and automation

Usage:
    from sales_agent.agent import root_agent, create_sales_app
    from sales_agent import salesConfig
"""

from .agent import root_agent, create_sales_app
from .config import salesConfig

__all__ = [
    'root_agent',
    'create_sales_app', 
    'salesConfig'
]

__version__ = "1.0.0"
__author__ = "Sales Agent Team"
__description__ = "Personalized customer sales agent for ADK with SHAP analysis and multi-product campaigns"