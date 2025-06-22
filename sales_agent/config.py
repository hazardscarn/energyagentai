"""
Sales Agent Configuration - Updated
File: sales_agent/config.py

Configuration settings for the Sales Agent system following ADK best practices
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class salesConfig:
    """Configuration for Sales Agent System"""
    
    # Google Cloud Configuration
    project_id: str = "energyagentai"
    dataset_name: str = "alberta_energy_ai"
    location: str = "us-central1"
    
    # Model Configuration
    primary_model: str = "gemini-2.5-pro-preview-05-06"  # For complex content generation
    default_model: str = "gemini-2.5-flash-preview-05-20"  # For faster operations
    
    # ML Model Configuration
    bucket_name: str = "albertaenergy-ads"
    
    # Sales-specific settings
    default_email_tone: str = "professional"
    default_call_approach: str = "consultative"
    max_content_length: int = 2000  # Maximum content length for emails/scripts
    
    # Product model mappings for SHAP analysis
    product_model_mapping = {
        "Green Energy Plan": "upsell_green_plan",
        "HVAC System": "crosssell_hvac", 
        "Solar Panel Installation": "crosssell_solar",
        "Home Insurance": "crosssell_insurance",
        "Surge Protection": "upsell_surge_protection",
        "Energy Efficiency Analysis": "upsell_efficiency_analysis"
    }
    
    # Content templates and settings
    sales_email_types = {
        "upsell": "Upsell email for existing customers to upgrade services",
        "cross_sell": "Cross-sell email to introduce new product categories",
        "promotional": "Promotional email with special offers and incentives",
        "follow_up": "Follow-up email after initial product interest",
        "win_back": "Win-back email for customers who declined previous offers"
    }
    
    call_script_types = {
        "sales_pitch": "Direct sales pitch for specific products",
        "consultation": "Consultative call to understand needs and recommend products",
        "follow_up": "Follow-up call after email or previous conversation",
        "objection_handling": "Call focused on addressing specific customer concerns",
        "closing": "Closing call to finalize product purchase or agreement"
    }
    
    email_tones = {
        "professional": "Business-focused, authoritative, and trustworthy",
        "friendly": "Warm, approachable, and personal",
        "urgent": "Time-sensitive with clear call to action",
        "consultative": "Advisory, helpful, and educational",
        "appreciative": "Grateful, value-focused, and recognition-heavy"
    }
    
    call_approaches = {
        "consultative": "Problem-solving and advisory approach, focus on customer needs",
        "direct_sales": "Confident, benefit-focused, closing-oriented approach",
        "educational": "Inform and educate about product value and benefits",
        "relationship_building": "Focus on strengthening customer relationship and trust"
    }
    
    # Sales probability thresholds
    high_probability_threshold: float = 0.7
    medium_probability_threshold: float = 0.4
    low_probability_threshold: float = 0.2
    
    def __post_init__(self):
        """Load configuration from environment variables if available"""
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT", self.project_id)
        self.location = os.getenv("GOOGLE_CLOUD_LOCATION", self.location)
        self.bucket_name = os.getenv("ML_MODELS_BUCKET", self.bucket_name)
        
        # Set environment variables for ADK
        os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "TRUE"
        os.environ["GOOGLE_CLOUD_PROJECT"] = self.project_id
        os.environ["GOOGLE_CLOUD_LOCATION"] = self.location
    
    def get_product_model_name(self, product_name: str) -> str:
        """Get ML model name for a product"""
        return self.product_model_mapping.get(product_name, "crosssell_hvac")
    
    def get_email_type_description(self, email_type: str) -> str:
        """Get description for email type"""
        return self.sales_email_types.get(email_type, f"Unknown email type: {email_type}")
    
    def get_call_type_description(self, call_type: str) -> str:
        """Get description for call type"""
        return self.call_script_types.get(call_type, f"Unknown call type: {call_type}")
    
    def get_tone_description(self, tone: str) -> str:
        """Get description for email tone"""
        return self.email_tones.get(tone, f"Unknown tone: {tone}")
    
    def get_approach_description(self, approach: str) -> str:
        """Get description for call approach"""
        return self.call_approaches.get(approach, f"Unknown approach: {approach}")
    
    def get_probability_category(self, probability: float) -> str:
        """Categorize sales probability"""
        if probability >= self.high_probability_threshold:
            return "High"
        elif probability >= self.medium_probability_threshold:
            return "Medium"
        else:
            return "Low"
    
    def validate_email_type(self, email_type: str) -> bool:
        """Check if email type is valid"""
        return email_type in self.sales_email_types
    
    def validate_call_type(self, call_type: str) -> bool:
        """Check if call type is valid"""
        return call_type in self.call_script_types
    
    def validate_tone(self, tone: str) -> bool:
        """Check if tone is valid"""
        return tone in self.email_tones
    
    def validate_approach(self, approach: str) -> bool:
        """Check if approach is valid"""
        return approach in self.call_approaches
    
    @property
    def full_table_name(self) -> str:
        """Get fully qualified table name"""
        return f"`{self.project_id}.{self.dataset_name}.customer_base`"
    
    @property
    def output_directory(self) -> str:
        """Get output directory for sales content"""
        return "sales_outputs"


# Global configuration instance
config = salesConfig()