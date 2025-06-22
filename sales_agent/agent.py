"""
Sales Assistant Agent - Clean & Simple Implementation
File: sales_agent/agent.py
"""

import os
import json
from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools import FunctionTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from vertexai.preview.reasoning_engines import AdkApp

# Import shared tools
from shared_tools.simple_sql_agents import (
    generate_sql_query_tool,
    execute_query_dataframe_tool
)
from shared_tools.mlagent import analyze_model_with_shap_tool

# Import config and tools
from .config import salesConfig
from .sales_content_tools import (
    get_sales_eligibility_customer,
    generate_sales_email_tool,
    generate_call_script_tool
)

config = salesConfig()

# =============================================================================
# CORE AGENT TOOLS
# =============================================================================

def extract_customer_data(customer_id: str) -> str:
    """Extract customer data for sales analysis"""
    try:
        query_description = f"Get complete customer profile for customer_id = '{customer_id}'"
        sql_query_response = generate_sql_query_tool(query_description)
        sql_query_json = json.loads(sql_query_response)
        
        if sql_query_json.get("success", False):
            actual_sql_query = sql_query_json.get("sql_query", "")
        else:
            actual_sql_query = f"SELECT * FROM `energyagentai.alberta_energy_ai.customer_base` WHERE customer_id = '{customer_id}'"
        
        result = execute_query_dataframe_tool(actual_sql_query)
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "sql_query": actual_sql_query,
            "customer_data": result,
            "message": "Customer data extracted successfully"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "error": str(e)
        }, indent=2)

def identify_sales_opportunities(customer_id: str) -> str:
    """Identify top 2 products for upsell/cross-sell"""
    try:
        eligibility_result = get_sales_eligibility_customer(customer_id)
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "sales_opportunities": eligibility_result,
            "message": "Sales opportunities identified successfully"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "error": str(e)
        }, indent=2)

def analyze_sales_promoting_factors(customer_id: str, sql_query: str, product_model_name: str) -> str:
    """
    Analyze factors that PROMOTE sales for a specific product using SHAP.
    
    Args:
        customer_id: Customer identifier
        sql_query: SQL query that returns customer data
        product_model_name: ML model name (e.g., 'crosssell_hvac')
        
    Returns:
        str: SHAP analysis of factors that increase sales probability
    """
    try:
        shap_result = analyze_model_with_shap_tool(
            sql_query=sql_query,
            model_name=product_model_name,
            target_event="positive"
        )
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "product_model": product_model_name,
            "analysis_type": "promoting_factors",
            "shap_analysis": shap_result,
            "message": "Sales promoting factors analysis completed"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "product_model": product_model_name,
            "error": str(e)
        }, indent=2)

def analyze_sales_preventing_factors(customer_id: str, sql_query: str, product_model_name: str) -> str:
    """
    Analyze factors that PREVENT sales for a specific product using SHAP.
    
    Args:
        customer_id: Customer identifier
        sql_query: SQL query that returns customer data
        product_model_name: ML model name (e.g., 'crosssell_hvac')
        
    Returns:
        str: SHAP analysis of factors that decrease sales probability
    """
    try:
        shap_result = analyze_model_with_shap_tool(
            sql_query=sql_query,
            model_name=product_model_name,
            target_event="negative"
        )
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "product_model": product_model_name,
            "analysis_type": "preventing_factors",
            "shap_analysis": shap_result,
            "message": "Sales preventing factors analysis completed"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "product_model": product_model_name,
            "error": str(e)
        }, indent=2)

# =============================================================================
# SALES AGENT
# =============================================================================

root_agent = Agent(
    name="sales_assistant_agent",
    model=config.primary_model,
    description="Sales Assistant Agent for personalized sales campaigns",
    instruction="""
    I am the Sales Assistant Agent. I help create personalized sales campaigns.

    My workflow:
    1. Extract customer data using extract_customer_data()
    2. Find sales opportunities using identify_sales_opportunities()
    3. Analyze promoting factors using analyze_sales_promoting_factors()
    4. Generate content using generate_sales_email_tool() or generate_call_script_tool()

    I can handle requests like:
    - "Create sales campaign for customer X"
    - "Generate call script for customer Y"
    - "Analyze sales factors for customer Z"
    """,
    tools=[
        FunctionTool(extract_customer_data),
        FunctionTool(identify_sales_opportunities),
        FunctionTool(analyze_sales_promoting_factors),
        #FunctionTool(analyze_sales_preventing_factors),
        FunctionTool(generate_sales_email_tool),
        FunctionTool(generate_call_script_tool)
    ]
)

# =============================================================================
# APP SETUP
# =============================================================================

def create_sales_app():
    """Create ADK application"""
    return AdkApp(agent=root_agent)

def test_sales_agent():
    """Test the sales agent"""
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("⚠️ Set GOOGLE_CLOUD_PROJECT environment variable")
        return
    
    runner = Runner(
        agent=root_agent,
        session_service=InMemorySessionService()
    )
    
    test_message = "Create sales campaign for customer CUST00000598"
    
    try:
        result = runner.run(
            user_id="sales_specialist",
            session_id="test_session",
            message=test_message
        )
        print("✅ Test successful")
        print(f"Response: {result.text[:200]}...")
    except Exception as e:
        print(f"❌ Test failed: {e}")

def run_interactive():
    """Run interactive mode"""
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("⚠️ Set GOOGLE_CLOUD_PROJECT environment variable")
        return
    
    runner = Runner(
        agent=root_agent,
        session_service=InMemorySessionService()
    )
    
    print("🎯 Sales Assistant Ready!")
    print("Example: 'Create sales campaign for customer CUST00000598'")
    print("Type 'quit' to exit.\n")
    
    session_id = f"session_{int(datetime.now().timestamp())}"
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            result = runner.run(
                user_id="sales_specialist",
                session_id=session_id,
                message=user_input
            )
            
            print(f"\nSales Agent: {result.text}\n")
            
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "test":
            test_sales_agent()
        elif sys.argv[1] == "interactive":
            run_interactive()
        else:
            print("Usage: python agent.py [test|interactive]")
    else:
        run_interactive()