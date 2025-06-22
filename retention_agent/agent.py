"""
Retention Agent - Complete ADK Implementation
File: retention_agent/agent.py

This agent creates personalized retention campaigns for individual customers by:
1. Extracting customer data using SQL
2. Analyzing churn factors with SHAP
3. Generating personalized email or call scripts
4. Displaying content directly in chat
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from vertexai.preview.reasoning_engines import AdkApp

# Import shared tools (assuming they exist in the shared_tools folder)
from shared_tools.simple_sql_agents import (
    generate_sql_query_tool,
    execute_query_dataframe_tool
)
from shared_tools.mlagent import (
    analyze_model_with_shap_tool
)

# Import config from same retention_agent folder
from .config import RetentionConfig
from .retention_content_tools import (
    generate_retention_email_tool,
    generate_call_script_tool,
    analyze_customer_profile_tool
)

# Initialize configuration
config = RetentionConfig()

# =============================================================================
# CORE TOOL FUNCTIONS FOR RETENTION AGENT
# =============================================================================

def extract_customer_data(customer_id: str) -> str:
    """
    Extract complete customer data for retention analysis.
    
    Args:
        customer_id: Unique customer identifier
        
    Returns:
        str: JSON string with customer data and metadata
    """
    try:
        # Generate SQL query to get all customer data
        query_description = f"""
        Get complete customer profile for customer_id = '{customer_id}' including:
        - Demographics (age, income, location)
        - Account details (tenure, plan_type, monthly_usage)
        - Satisfaction and engagement metrics
        - Payment history and billing info
        - All columns needed for ML model analysis
        Use SELECT * to ensure all features are available for SHAP analysis
        """
        
        sql_query = generate_sql_query_tool(query_description)
        
        # Execute the query
        result = execute_query_dataframe_tool(sql_query)
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "sql_query": sql_query,
            "customer_data": result,
            "message": "Customer data extracted successfully"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

def analyze_customer_churn_factors(customer_id: str, sql_query: str) -> str:
    """
    Analyze churn factors for specific customer using SHAP.
    
    Args:
        customer_id: Customer identifier
        sql_query: SQL query that returns customer data with all columns
        
    Returns:
        str: SHAP analysis results with churn factors
    """
    try:
        # Use SHAP analysis to understand churn factors for this customer
        shap_result = analyze_model_with_shap_tool(
            sql_query=sql_query,
            model_name="churn",
            target_event="positive"  # Factors that increase churn risk
        )
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "analysis_type": "churn_factors",
            "shap_analysis": shap_result,
            "message": "Churn factor analysis completed successfully"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

def analyze_customer_protective_factors(customer_id: str, sql_query: str) -> str:
    """
    Analyze protective factors that reduce churn risk for customer.
    
    Args:
        customer_id: Customer identifier  
        sql_query: SQL query that returns customer data with all columns
        
    Returns:
        str: SHAP analysis results with protective factors
    """
    try:
        # Use SHAP analysis to understand protective factors
        shap_result = analyze_model_with_shap_tool(
            sql_query=sql_query,
            model_name="churn", 
            target_event="negative"  # Protective factors that reduce churn
        )
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "analysis_type": "protective_factors",
            "shap_analysis": shap_result,
            "message": "Protective factor analysis completed successfully"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

def generate_personalized_email(
    customer_id: str,
    customer_data: str,
    churn_factors: str,
    protective_factors: str,
    email_type: str = "retention",
    tone: str = "empathetic"
) -> str:
    """
    Generate personalized retention email based on customer analysis.
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data
        churn_factors: SHAP analysis of churn risk factors
        protective_factors: SHAP analysis of protective factors
        email_type: Type of email (retention, win_back, loyalty)
        tone: Email tone (empathetic, professional, urgent, friendly)
        
    Returns:
        str: Generated personalized email content
    """
    try:
        result = generate_retention_email_tool(
            customer_id=customer_id,
            customer_data=customer_data,
            churn_factors=churn_factors,
            protective_factors=protective_factors,
            email_type=email_type,
            tone=tone
        )
        
        return result
        
    except Exception as e:
        return f"❌ Error generating email for {customer_id}: {str(e)}"

def generate_personalized_call_script(
    customer_id: str,
    customer_data: str,
    churn_factors: str,
    protective_factors: str,
    call_type: str = "retention",
    approach: str = "consultative"
) -> str:
    """
    Generate personalized call script based on customer analysis.
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data
        churn_factors: SHAP analysis of churn risk factors
        protective_factors: SHAP analysis of protective factors
        call_type: Type of call (retention, win_back, check_in)
        approach: Call approach (consultative, problem_solving, relationship_building)
        
    Returns:
        str: Generated personalized call script
    """
    try:
        result = generate_call_script_tool(
            customer_id=customer_id,
            customer_data=customer_data,
            churn_factors=churn_factors,
            protective_factors=protective_factors,
            call_type=call_type,
            approach=approach
        )
        
        return result
        
    except Exception as e:
        return f"❌ Error generating call script for {customer_id}: {str(e)}"



# =============================================================================
# ROOT RETENTION AGENT
# =============================================================================

# Root agent that handles all retention requests
root_agent = Agent(
    name="retention_agent",
    model=config.primary_model,
    description="Retention Agent that creates personalized retention campaigns for individual customers",
    instruction="""
    I am the Retention Agent that creates personalized retention campaigns automatically.

    For ANY retention request, I run the complete workflow and display the results directly:

    1. Extract customer data using SQL
    2. Analyze churn factors with SHAP  
    3. Generate personalized content (email or call script as requested)
    4. Display the content clearly formatted for immediate use

    For any analysis request, I:
    - Extract customer data
    - Analyze churn and protective factors using SHAP
    - Use analyze_customer_profile_tool to get comprehensive insights on customer on churn risk
    - Gnereate a comprehensive report with all findings and display it

    **Request Examples:**
    - "Create retention email for customer CUST00008098" → Generate and display email
    - "Generate call script for customer X" → Generate and display call script
    - "Analyze churn factors for customer Y" → Analyze and display churn factors

    I show the generated content directly in a clear, readable format.
    """,
    tools=[
        FunctionTool(extract_customer_data),
        FunctionTool(analyze_customer_churn_factors), 
        FunctionTool(analyze_customer_protective_factors),
        FunctionTool(generate_personalized_email),
        FunctionTool(generate_personalized_call_script),
        FunctionTool(analyze_customer_profile_tool)
    ]
)

# =============================================================================
# APPLICATION SETUP
# =============================================================================

def create_retention_app():
    """
    Create and configure the Retention Agent ADK application.
    
    Returns:
        AdkApp: Configured ADK application ready for deployment
    """
    app = AdkApp(agent=root_agent)
    return app

def run_interactive_retention_agent():
    """Run the retention agent interactively"""
    
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("⚠️  Please set up environment variables first.")
        print("Required: GOOGLE_CLOUD_PROJECT")
        return
    
    # Create runner
    runner = Runner(
        agent=root_agent,
        session_service=InMemorySessionService()
    )
    
    print("🎯 Retention Agent Ready!")
    print("I help create personalized retention campaigns for individual customers.")
    print("\nExample requests:")
    print("  • 'Create retention email for customer CUST_12345'")
    print("  • 'Generate call script for customer CUST_67890'")
    print("  • 'Analyze churn factors for customer CUST_54321'")
    print("  • 'Why might customer CUST_99999 leave?'")
    print("\nType 'quit' to exit.\n")
    
    session_id = f"retention_session_{int(datetime.now().timestamp())}"
    user_id = "retention_specialist"
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Thanks for using Retention Agent!")
                break
            
            if not user_input:
                continue
            
            # Get agent response
            result = runner.run(
                user_id=user_id,
                session_id=session_id,
                message=user_input
            )
            
            print(f"\nRetention Agent: {result.text}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

# For ADK Web UI and CLI
if __name__ == "__main__":
    import sys
    run_interactive_retention_agent()