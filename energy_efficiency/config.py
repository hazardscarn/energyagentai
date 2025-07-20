"""
Energy Agent Configuration
File: config.py

Configuration settings for the Energy Agent system following ADK best practices
"""

import os
from dataclasses import dataclass


@dataclass
class EnergyConfig:
    """Configuration for Energy Agent System"""
    
    # Google Cloud Configuration
    project_id: str = "energyagentai"
    dataset_name: str = "alberta_energy_ai"
    location: str = "us-central1"
    
    # Model Configuration
    default_model: str = "gemini-2.5-pro"  # For faster operation
    primary_model: str = "gemini-2.5-flash"  # For complex content generation
    
    # ADK Configuration
    app_name: str = "energy_advisor"
    user_id: str = "energy_user"
    session_id: str = "energy_session"


# Global configuration instance
config = EnergyConfig()
