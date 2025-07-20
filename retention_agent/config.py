"""
Fixed Retention Agent Configuration
File: retention_agent/config.py

Addresses the salesConfig import error
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class RetentionConfig:
    """Configuration for Retention Agent System"""
    
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
    
    # Retention-specific settings
    default_email_tone: str = "empathetic"
    default_call_approach: str = "consultative"
    max_content_length: int = 2000  # Maximum content length for emails/scripts
    
    # Content templates and settings
    retention_email_types = {
        "retention": "Standard retention email for at-risk customers",
        "win_back": "Win-back email for recently churned customers", 
        "loyalty": "Loyalty appreciation email for high-value customers",
        "survey": "Feedback survey email to understand concerns"
    }
    
    call_script_types = {
        "retention": "Proactive retention call for at-risk customers",
        "win_back": "Win-back call for recently churned customers",
        "check_in": "Relationship-building check-in call",
        "issue_resolution": "Call to address specific customer issues"
    }
    
    email_tones = {
        "empathetic": "Understanding and caring tone",
        "professional": "Business-focused and formal tone",
        "urgent": "Time-sensitive with clear urgency",
        "friendly": "Casual and approachable tone",
        "appreciative": "Grateful and value-focused tone"
    }
    
    call_approaches = {
        "consultative": "Problem-solving and advisory approach",
        "relationship_building": "Focus on strengthening customer relationship",
        "problem_solving": "Direct focus on resolving specific issues",
        "value_reinforcement": "Emphasizing customer value and benefits"
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


# Global configuration instance
config = RetentionConfig()