"""
Sales Agent Configuration - Updated
File: sales_agent/config.py

Configuration settings for the Sales Agent system following ADK best practices
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class Config:
    """Configuration for Sales Agent System"""
    
    # Google Cloud Configuration
    project_id: str = "energyagentai"
    dataset_name: str = "alberta_energy_ai"
    location: str = "us-central1"
    
    # Model Configuration
    # primary_model: str = "gemini-2.5-pro-preview-05-06"  # For complex content generation
    # default_model: str = "gemini-2.5-flash-preview-05-20"  # For faster operations
    
    default_model: str = "gemini-2.5-flash"  # For complex reasoning
    primary_model: str = "gemini-2.5-pro"  # For faster operation    
    
    # ML Model Configuration
    bucket_name: str = "albertaenergy-ads"
    
