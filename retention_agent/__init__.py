"""
Retention Agent Package
File: retention_agent/__init__.py

This package provides comprehensive customer retention capabilities including:
- Individual customer data extraction and analysis
- SHAP-based churn factor analysis for personalized insights
- Personalized retention email generation
- Detailed call script creation for retention conversations
- Content management and downloadable packages

Usage:
    from retention_agent.agent import root_agent, create_retention_app
    from retention_agent import RetentionConfig
"""

from .agent import root_agent, create_retention_app
from .config import RetentionConfig

__all__ = [
    'root_agent',
    'create_retention_app', 
    'RetentionConfig'
]

__version__ = "1.0.0"
__author__ = "Retention Agent Team"
__description__ = "Personalized customer retention agent for ADK with SHAP analysis"