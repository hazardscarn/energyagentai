"""
Sales Assistant Agent - Clean & Simple Implementation
File: sales_agent/agent.py
"""

import os
import sys
import json
from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools import FunctionTool,ToolContext
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.artifacts import InMemoryArtifactService
from vertexai.preview.reasoning_engines import AdkApp
from .subtools import clean_sql_response, is_valid_sql
from dotenv import load_dotenv
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
    generate_call_script_tool,
    generate_sales_call_pitch_tool,create_audio_from_pitch
)


config = salesConfig()
load_dotenv()

# Create ElevenLabs MCP Toolset (add this before the root_agent definition):
# elevenlabs_mcp = MCPToolset(
#     connection_params=StdioServerParameters(
#         command='uvx',
#         args=['elevenlabs-mcp'],
#         env={
#             "ELEVENLABS_API_KEY": os.getenv("ELEVENLABS_API_KEY", ""),
#             "ELEVENLABS_MCP_BASE_PATH": "./audio_output"
#         }
#     )
# )

# elevenlabs_mcp = MCPToolset(
#     connection_params=SseServerParams(
#         url="http://localhost:3001/sse",  # Connect via HTTP
#         headers={
#             "Authorization": f"Bearer {os.getenv('ELEVENLABS_API_KEY', '')}"
#         }
#     )
#)
# =============================================================================
# CORE AGENT TOOLS
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

        IMPORTANT: Return only SQL code, not JSON or formatted text.
        """
        
        # sql_query = generate_sql_query_tool(query_description)
        raw_sql_response = generate_sql_query_tool(query_description)

        # Clean and validate the SQL response for Flash models
        sql_query = clean_sql_response(raw_sql_response)
        
        # Debug logging to see what we got
        print(f"🔍 Debug - Raw SQL response: {raw_sql_response}")
        print(f"🔍 Debug - Cleaned SQL: {sql_query}")

        # Validate SQL before executing
        if not is_valid_sql(sql_query):
            # Fallback to a simple, direct query
            sql_query = f"SELECT * FROM `energyagentai.alberta_energy_ai.customer_base` WHERE customer_id = '{customer_id}'"
            print(f"⚠️  Using fallback SQL: {sql_query}")

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


# def identify_sales_opportunities(tool_context: ToolContext, customer_id: str) -> str:
#     """Identify top 2 products for upsell/cross-sell"""
#     try:
#         eligibility_result = get_sales_eligibility_customer(tool_context, customer_id)  # Pass tool_context
#         return json.dumps({
#             "success": True,
#             "customer_id": customer_id,
#             "sales_opportunities": eligibility_result,
#             "message": "Sales opportunities identified successfully"
#         }, indent=2)
        
#     except Exception as e:
#         return json.dumps({
#             "success": False,
#             "customer_id": customer_id,
#             "error": str(e)
#         }, indent=2)

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
    model=config.default_model,
    description="Sales Assistant Agent for personalized sales campaigns",
    instruction="""
    I am the Sales Assistant Agent. I help create personalized sales campaigns.

    My workflow:
    1. Extract customer data using extract_customer_data()
    2. Find sales opportunities using get_sales_eligibility_customer()
    3. Analyze promoting factors using analyze_sales_promoting_factors()
    5. If asked to create an email:
        - Generate content using generate_sales_email_tool() 
    6. If asked to create call script:
        - Generate content using generate_call_script_tool() 
    7. If asked to create an outbound call or audio sales pitch to pitch the product to customer:
        - First run generate_sales_call_pitch_tool to create the pitch content
        - Then run create_audio_from_pitch to generate the audio for the sales call pitch content

    - Use your tools for the tasks above.
    - DONOT ask the user to give SQL query or product name etc. You have all the tools needed

    I can handle requests like:
    - "Create sales campaign for customer X"
    - "Generate call script for customer Y"
    - "Make audio sales pitch or outbound sales pitch for customer Z"
    """,
    tools=[
        FunctionTool(extract_customer_data),
        FunctionTool(get_sales_eligibility_customer),
        FunctionTool(analyze_sales_promoting_factors),
        #FunctionTool(analyze_sales_preventing_factors),
        FunctionTool(generate_sales_email_tool),
        FunctionTool(generate_call_script_tool),
        FunctionTool(generate_sales_call_pitch_tool),
        FunctionTool(create_audio_from_pitch),
#        elevenlabs_mcp  # Add the MCP toolset
    ]
)
        # - Finally use the ElevenLabs generate_speech or text_to_speech tool to create the MP3 audio file
        # - Provide both text and audio versions of the sales pitch
        #     4. Analyze preventing factors using analyze_sales_preventing_factors()
# =============================================================================
# APP SETUP
# =============================================================================

def create_sales_app():
    """Create ADK application"""
    return AdkApp(agent=root_agent)

# def test_sales_agent():
#     """Test the sales agent"""
#     if not os.getenv("GOOGLE_CLOUD_PROJECT"):
#         print("⚠️ Set GOOGLE_CLOUD_PROJECT environment variable")
#         return
    
#     runner = Runner(
#         agent=root_agent,
#         session_service=InMemorySessionService()
#     )
    
#     test_message = "Create sales campaign for customer CUST00000598"
    
#     try:
#         result = runner.run(
#             user_id="sales_specialist",
#             session_id="test_session",
#             message=test_message
#         )
#         print("✅ Test successful")
#         print(f"Response: {result.text[:200]}...")
#     except Exception as e:
#         print(f"❌ Test failed: {e}")

# def run_interactive():
#     """Run interactive mode"""
#     if not os.getenv("GOOGLE_CLOUD_PROJECT"):
#         print("⚠️ Set GOOGLE_CLOUD_PROJECT environment variable")
#         return
    
#     runner = Runner(
#         agent=root_agent,
#         session_service=InMemorySessionService()
#     )
    
#     print("🎯 Sales Assistant Ready!")
#     print("Example: 'Create sales campaign for customer CUST00000598'")
#     print("Type 'quit' to exit.\n")
    
#     session_id = f"session_{int(datetime.now().timestamp())}"
    
#     while True:
#         try:
#             user_input = input("You: ").strip()
            
#             if user_input.lower() in ['quit', 'exit']:
#                 print("👋 Goodbye!")
#                 break
            
#             if not user_input:
#                 continue
            
#             result = runner.run(
#                 user_id="sales_specialist",
#                 session_id=session_id,
#                 message=user_input
#             )
            
#             print(f"\nSales Agent: {result.text}\n")
            
#         except KeyboardInterrupt:
#             print("\n👋 Goodbye!")
#             break
#         except Exception as e:
#             print(f"❌ Error: {e}\n")

# if __name__ == "__main__":
#     import sys
    
#     if len(sys.argv) > 1:
#         if sys.argv[1] == "test":
#             test_sales_agent()
#         elif sys.argv[1] == "interactive":
#             run_interactive()
#         else:
#             print("Usage: python agent.py [test|interactive]")
#     else:
#         run_interactive()