import json
import os
from pathlib import Path
from google.adk.evaluation import evaluate_agent
from google.adk.agents import Agent

"""
Helper script to create additional test cases
"""

def create_additional_test_cases():
    """Create more comprehensive test cases"""
    
    additional_cases = [
        {
            "id": "seasonal_analysis",
            "input": {
                "user_id": "test_seasonal",
                "message": "Analyze seasonal usage patterns and their impact on churn for customers in Edmonton"
            },
            "expected_behavior": {
                "should_use_tools": ["generate_sql_query", "analyze_ml_model"],
                "should_filter_by": ["Edmonton", "seasonal"],
                "should_analyze_patterns": True
            }
        },
        {
            "id": "business_customer_segmentation", 
            "input": {
                "user_id": "test_business",
                "message": "What drives cross-sell success for business customers by industry type?"
            },
            "expected_behavior": {
                "should_segment_by": ["business_type", "industry"],
                "should_analyze_multiple_models": ["crosssell_hvac", "crosssell_solar", "crosssell_insurance"],
                "should_provide_segmentation_insights": True
            }
        },
        {
            "id": "retention_strategy",
            "input": {
                "user_id": "test_retention",
                "message": "Create a data-driven retention strategy for high-value customers at risk of churn"
            },
            "expected_behavior": {
                "should_combine_analyses": ["churn", "clv"],
                "should_identify_at_risk_segments": True,
                "should_provide_action_plan": True
            }
        }
    ]
    
    return additional_cases