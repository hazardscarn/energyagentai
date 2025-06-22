"""
Portfolio Manager Agent - ADK Implementation
Following Google ADK best practices from customer service agent patterns
"""

from google.adk.agents import Agent, SequentialAgent, LlmAgent
from google.adk.tools import FunctionTool
from vertexai.preview.reasoning_engines import AdkApp
import os

# Import shared tools from root shared_tools folder
from shared_tools.simple_sql_agents import (
    generate_sql_query_tool,
    execute_query_dataframe_tool,
    execute_query_json_tool
)
from shared_tools.mlagent import (
    analyze_model_with_shap_tool
)



# Import config from same portfolio_manager folder
from .config import PortfolioConfig

# Initialize configuration
config = PortfolioConfig()

# =============================================================================
# TOOL DEFINITIONS (Following ADK Best Practices)
# =============================================================================

def generate_sql_query(query_description: str) -> str:
    """
    Generate SQL query from natural language description.
    
    Use this tool when you need to create SQL queries for customer analysis.

    
    Args:
        query_description: Natural language description of what data to retrieve
        
    Returns:
        str: Generated SQL query ready for execution
    """
    try:
        result = generate_sql_query_tool(query_description)
        return result
    except Exception as e:
        return f"Error generating SQL: {str(e)}"

def execute_sql_query(sql_query: str) -> str:
    """
    Execute SQL query and return results as DataFrame information.
    
    Use this tool to run SQL queries and get structured data results.
    
    Args:
        sql_query: SQL query to execute
        
    Returns:
        str: JSON string with query results and metadata
    """
    try:
        result = execute_query_dataframe_tool(sql_query)
        return result
    except Exception as e:
        return f"Error executing SQL: {str(e)}"

def analyze_ml_model(sql_query: str, model_name: str, target_event: str = "positive") -> str:
    """
    Analyze ML model using SHAP with customer data from SQL query.
    
    Use this tool to understand what factors drive model predictions.
    
    Args:
        sql_query: SQL query that returns customer data with all columns (SELECT *)
        model_name: Model to analyze (churn, crosssell_hvac, crosssell_insurance, 
                   crosssell_solar, upsell_green_plan, upsell_efficiency_analysis, 
                   upsell_surge_protection)
        target_event: "positive" for factors that increase probability, 
                     "negative" for protective factors
    
    Returns:
        str: Detailed SHAP analysis report with contributing factors
    """
    try:
        result = analyze_model_with_shap_tool(sql_query, model_name, target_event)
        return result
    except Exception as e:
        return f"Error in ML analysis: {str(e)}"

def calculate_customer_clv(sql_query: str) -> str:
    """
    Calculate Customer Lifetime Value from SQL query results.
    
    Use this tool to analyze CLV for customer segments.
    Requires customers with: customer_id, annual_income, monthly_usage_kwh, satisfaction_score
    
    Args:
        sql_query: SQL query returning customer data with required CLV columns
        
    Returns:
        str: CLV analysis report with statistics and top customers
    """
    try:
        # Import your existing CLV function
        from test import calculate_clv_from_query_results_tool_simple
        result = calculate_clv_from_query_results_tool_simple(sql_query)
        return result
    except Exception as e:
        return f"Error calculating CLV: {str(e)}"







# =============================================================================
# SPECIALIZED AGENTS (Following Customer Service Agent Pattern)
# =============================================================================

# 1. SQL Developer Agent - Handles all SQL generation and execution
sql_developer_agent = Agent(
    name="sql_developer_agent",
    model=config.default_model,
    description="SQL specialist that generates and executes queries for customer analysis",
    instruction="""
    I am an expert SQL developer for Alberta Energy AI customer analysis.
    
    My responsibilities:
    - Generate precise SQL queries from natural language requests
    - Execute queries and return structured data
    - Ensure queries use SELECT * when data will be used for ML model scoring
    
    I understand customer criteria like:
    - Demographics: "customers over 50", "annual income above 100K"
    - Location: "customers in Calgary", "Edmonton residents" 
    - Behavior: "high usage customers", "satisfied customers"
    - Business: "commercial customers", "residential customers"
    
    For ML analysis, I always modify SELECT statements to use SELECT * to ensure 
    all required features are available for model scoring.
    """,
    tools=[
        FunctionTool(generate_sql_query),
        FunctionTool(execute_sql_query)
    ]
)

# 2. ML Analysis Agent - Handles SHAP analysis and model insights  
ml_analysis_agent = Agent(
    name="ml_analysis_agent",
    model=config.default_model,
    description="ML specialist that performs SHAP analysis and model interpretation",
    instruction="""
    I am a Machine Learning Analysis specialist focused on model interpretation.
    
    My capabilities:
    - Perform SHAP analysis on XGBoost models to explain predictions
    - Identify factors that increase or decrease prediction probabilities
    - Analyze customer segments using trained ML models
    - Provide business insights from model outputs
    
    Available models and their purposes:
    - churn: Customer churn prediction
    - crosssell_hvac: HVAC system cross-sell probability  
    - crosssell_insurance: Insurance product cross-sell probability
    - crosssell_solar: Solar panel cross-sell probability
    - upsell_green_plan: Green energy plan upsell probability
    - upsell_efficiency_analysis: Energy efficiency analysis upsell
    - upsell_surge_protection: Surge protection upsell probability
    
    I can analyze:
    - Positive factors: What drives higher prediction probabilities
    - Negative factors: What protects against churn or reduces upsell likelihood
    
    I always provide detailed business interpretations of SHAP results.
    """,
    tools=[
        FunctionTool(analyze_ml_model)
    ]
)

# 3. CLV Analysis Agent - Handles Customer Lifetime Value calculations
clv_analysis_agent = Agent(
    name="clv_analysis_agent", 
    model=config.default_model,
    description="CLV specialist that calculates and analyzes Customer Lifetime Value",
    instruction="""
    I am a Customer Lifetime Value (CLV) analysis specialist.
    
    My expertise:
    - Calculate CLV using customer income, usage, and satisfaction data
    - Analyze CLV distribution across customer segments
    - Identify high-value customers and segments
    - Provide actionable insights for customer retention and growth
    
    Required data for CLV calculation:
    - customer_id: Unique customer identifier
    - annual_income: Customer's annual income
    - monthly_usage_kwh: Monthly energy usage in kWh
    - satisfaction_score: Customer satisfaction rating
    
    I provide comprehensive CLV reports including:
    - Average and total CLV by segment
    - Top customers by CLV
    - Distribution analysis
    - Business recommendations
    """,
    tools=[
        FunctionTool(generate_sql_query),
        FunctionTool(calculate_customer_clv)
    ]
)


# =============================================================================
# WORKFLOW AGENTS (Sequential Processing)
# =============================================================================

# Create separate SQL agent instances (ADK requirement)
sql_developer_agent_ml = Agent(
    name="sql_developer_agent_ml",
    model=config.default_model,
    description="SQL specialist for ML workflows",
    instruction="""
    I am an expert SQL developer for ML workflows.
    I generate SQL queries with SELECT * for model scoring.
    """,
    tools=[
        FunctionTool(generate_sql_query),
        FunctionTool(execute_sql_query)
    ]
)


# ML Analysis Workflow: SQL → SHAP Analysis
ml_workflow_agent = SequentialAgent(
    name="ml_workflow_agent",
    description="Sequential workflow for ML model analysis",
    sub_agents=[sql_developer_agent_ml, ml_analysis_agent]  # ✅ Unique instance
)


# =============================================================================
# ROOT AGENT (Main Orchestrator)
# =============================================================================

root_agent = LlmAgent(
    name="portfolio_manager_agent",
    model=config.primary_model,
    description=f"""Portfolio Manager that performs comprehensive portfolio analysis for Alberta Energy AI.
    Duties include ML model effect/contribution analysis, customer lifetime value (CLV) analysis, portfolio segmentation analysis etc.""",
    instruction="""
    I am the Portfolio Manager for Alberta Energy AI customer intelligence.
    
    I coordinate a team of specialist agents to provide comprehensive customer analysis:
    
    **For ML Model Analysis:**
    - Questions about "churn factors", "what drives churn" → Delegate to ml_workflow_agent for churn model
    - Questions about "HVAC cross-sell", "HVAC opportunities" → Delegate to ml_workflow_agent for crosssell_hvac  
    - Questions about "solar cross-sell", "solar opportunities" → Delegate to ml_workflow_agent for crosssell_solar
    - Questions about "green energy", "green plan upsell" → Delegate to ml_workflow_agent for upsell_green_plan
    - Questions about "protective factors", "preventing churn" → Delegate to ml_workflow_agent with negative factors
    - Questions about "insurance cross-sell" → Delegate to ml_workflow_agent for crosssell_insurance
    - Questions about "efficiency analysis" → Delegate to ml_workflow_agent for upsell_efficiency_analysis
    
    **When asked to create a report on factors that lead to churn or upsell opportunities, use ml_workflow_agent **
    
    **For Basic SQL and Data Analysis:**
    - Questions about "data", "customers", "segments"  → Delegate to sql_developer_agent
    
    **My Process:**
    1. Analyze the business question to determine the type of analysis needed
    2. Extract customer criteria and segments from the request
    3. Delegate to the appropriate specialist agent or workflow
    4. Synthesize results into actionable business insights
    5. Provide strategic recommendations based on findings
    
    - DO NOT ask for SQL queries or dataset names.
    I
      always provide executive-level insights and connect analysis to business value.
.
    """,
    sub_agents=[
        ml_workflow_agent,
        clv_analysis_agent,
        sql_developer_agent
    ]
)

# =============================================================================
# APPLICATION SETUP
# =============================================================================

def create_portfolio_manager_app():
    """
    Create and configure the Portfolio Manager ADK application.
    
    Returns:
        AdkApp: Configured ADK application ready for deployment
    """
    app = AdkApp(agent=root_agent)
    return app

# For ADK Web UI and CLI
if __name__ == "__main__":
    app = create_portfolio_manager_app()
    
    # Test the system
    print("🤖 Portfolio Manager Agent System with Simplified Visualization Created!")
    print(f"Root agent: {root_agent.name}")
    print(f"Sub-agents: {[sub.name for sub in root_agent.sub_agents]}")
    
    # Example test queries with visualization
    test_queries = [
        "Show me a chart of customer CLV by segment",
        "What factors drive churn for customers over 50 years old?",
        "Create a bar chart of customer satisfaction by city",
        "Visualize green energy plan upsell opportunities for high-income customers",
        "Show me customer data for Calgary residents"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"Test Query {i}: {query}")
        print('='*60)
        
        try:
            # Stream the response
            for event in app.stream_query(
                user_id=f"test_user_{i}",
                message=query
            ):
                if 'content' in event and 'parts' in event['content']:
                    for part in event['content']['parts']:
                        if 'text' in part:
                            print(f"🤖 {part['text']}")
                            
        except Exception as e:
            print(f"❌ Error in test {i}: {str(e)}")
    
    print(f"\n🎯 Simplified Features:")
    print("- Direct SQL-to-chart creation")
    print("- No dataset name questions")
    print("- Automatic column selection")  
    print("- Simple KPI dashboards")
    print("- Multiple chart types from same data")
    print("- Streamlined visualization workflow")