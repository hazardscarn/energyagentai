"""
Marketing Manager Configuration
Following ADK customer service agent configuration patterns
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class MarketingConfig:
    """Configuration for Marketing Manager Agent System"""
    
    # Google Cloud Configuration
    project_id: str = "energyagentai"
    dataset_name: str = "alberta_energy_ai"
    location: str = "us-central1"
    
    # Model Configuration
    primary_model: str = "gemini-2.5-pro-preview-05-06"  # For complex reasoning
    default_model: str = "gemini-2.5-flash-preview-05-20"  # For faster operations
    
    # ML Model Configuration
    bucket_name: str = "albertaenergy-ads"
    

    def __post_init__(self):
        """Load configuration from environment variables if available"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", self.project_id)
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", self.location)
        self.bucket_name = os.getenv("ML_MODELS_BUCKET", self.bucket_name)
        
        # Set environment variables for ADK
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = self.location
    


# Global configuration instance
config = MarketingConfig()