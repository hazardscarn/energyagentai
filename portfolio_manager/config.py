"""
Portfolio Manager Configuration
Following ADK customer service agent configuration patterns
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class PortfolioConfig:
    """Configuration for Portfolio Manager Agent System"""
    
    # Google Cloud Configuration
    project_id: str = "energyagentai"
    dataset_name: str = "alberta_energy_ai"
    location: str = "us-central1"
    
    # Model Configuration
    primary_model: str = "gemini-2.5-pro-preview-05-06"  # For complex reasoning
    default_model: str = "gemini-2.5-flash-preview-05-20"  # For faster operations
    
    # ML Model Configuration
    bucket_name: str = "albertaenergy-ads"
    
    # Available ML Models
    available_models = {
        "churn": "Customer churn prediction",
        "crosssell_hvac": "HVAC system cross-sell probability",
        "crosssell_insurance": "Insurance product cross-sell probability", 
        "crosssell_solar": "Solar panel cross-sell probability",
        "upsell_green_plan": "Green energy plan upsell probability",
        "upsell_efficiency_analysis": "Energy efficiency analysis upsell",
        "upsell_surge_protection": "Surge protection upsell probability"
    }
    
    def __post_init__(self):
        """Load configuration from environment variables if available"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", self.project_id)
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", self.location)
        self.bucket_name = os.getenv("ML_MODELS_BUCKET", self.bucket_name)
        
        # Set environment variables for ADK
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = self.location
    
    def get_model_description(self, model_name: str) -> str:
        """Get description for a specific ML model"""
        return self.available_models.get(model_name, f"Unknown model: {model_name}")
    
    def validate_model(self, model_name: str) -> bool:
        """Check if model name is valid"""
        return model_name in self.available_models
    
    @property
    def full_table_name(self) -> str:
        """Get fully qualified table name"""
        return f"`{self.project_id}.{self.dataset_name}.customer_base`"


# Global configuration instance
config = PortfolioConfig()