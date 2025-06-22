"""
Complete ADK Agent Setup with Energy Analysis Tools
Integrates SQL capabilities with energy analysis
"""

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

# Import configuration
from .config import config

# Import existing SQL tools
from shared_tools.simple_sql_agents import (
    generate_sql_query_tool,
    execute_query_dataframe_tool,
    execute_query_json_tool
)

# Import energy analysis tools
from .energy_analysis_tools import (
    analyze_tou_plan_fit,
    analyze_energy_efficiency,
    get_customer_energy_insights
)


def create_comprehensive_energy_agent():
    """
    Create an ADK agent that combines SQL capabilities with energy analysis
    """
    return Agent(
        model=config.primary_model,
        name="energy_advisor_agent",
        instruction="""You are an expert energy advisor with access to smart meter data and analysis tools.

        Your capabilities include:
        1. **SQL Analysis**: Generate and execute SQL queries on energy data
        2. **TOU Plan Analysis**: Assess customer fit for Time of Use plans (8PM-8AM free, daytime 2x cost)
        3. **Energy Efficiency**: Analyze usage patterns and provide improvement recommendations
        4. **Comprehensive Insights**: Combine multiple analyses for actionable advice

        When a user asks about:
        - "TOU plan" or "time of use" → use analyze_tou_plan_fit
        - "energy efficiency" or "reduce usage" → use analyze_energy_efficiency  
        - "energy insights" or "complete analysis" → use get_customer_energy_insights
        - Custom data queries → use generate_sql_query_tool then execute_query_json_tool

        Always:
        - Ask for customer_id if not provided
        - Explain your analysis in simple terms
        - Provide specific, actionable recommendations
        - Include dollar savings when relevant
        - Cite the data sources and timeframes used
        """,
        
        description="Expert energy advisor with smart meter data analysis capabilities",
        
        tools=[
            # SQL tools
            generate_sql_query_tool,
            execute_query_dataframe_tool, 
            execute_query_json_tool,
            
            # Energy analysis tools
            analyze_tou_plan_fit,
            analyze_energy_efficiency,
            get_customer_energy_insights
        ]
    )


def create_specialized_agents():
    """
    Create specialized agents for different aspects of energy analysis
    """
    
    # TOU Plan Specialist
    tou_specialist = Agent(
        model=config.primary_model,
        name="tou_specialist",
        instruction="""You are a TOU (Time of Use) plan specialist. You help customers determine 
        if they would benefit from TOU plans where nighttime usage (8PM-8AM) is free and 
        daytime usage costs twice the normal rate. Always provide clear savings calculations.""",
        tools=[analyze_tou_plan_fit]
    )
    
    # Energy Efficiency Specialist
    efficiency_specialist = Agent(
        model=config.primary_model, 
        name="efficiency_specialist",
        instruction="""You are an energy efficiency expert. You analyze usage patterns to 
        identify inefficiencies and provide actionable recommendations for reducing energy 
        consumption. Focus on practical, implementable solutions.""",
        tools=[analyze_energy_efficiency]
    )
    
    # SQL Query Specialist  
    sql_specialist = Agent(
        model=config.primary_model,
        name="sql_specialist", 
        instruction="""You are a SQL expert for energy data analysis. You generate and execute 
        SQL queries on smart meter data to answer specific questions about energy usage patterns.""",
        tools=[generate_sql_query_tool, execute_query_json_tool, execute_query_dataframe_tool]
    )
    
    return {
        "tou_specialist": tou_specialist,
        "efficiency_specialist": efficiency_specialist, 
        "sql_specialist": sql_specialist
    }


def create_energy_coordinator_agent():
    """
    Create a coordinator agent that delegates to specialized agents
    """
    # Create specialized agents
    specialists = create_specialized_agents()
    
    # Create coordinator with specialists as tools
    return Agent(
        model=config.primary_model,
        name="energy_coordinator",
        instruction="""You are an energy advisory coordinator. You have access to specialized agents:

        1. TOU Specialist - for Time of Use plan analysis
        2. Efficiency Specialist - for energy efficiency analysis  
        3. SQL Specialist - for custom data queries

        Route questions to the appropriate specialist based on the user's needs. 
        You can also combine insights from multiple specialists for comprehensive analysis.""",
        
        tools=[
            AgentTool(agent=specialists["tou_specialist"]),
            AgentTool(agent=specialists["efficiency_specialist"]),
            AgentTool(agent=specialists["sql_specialist"])
        ]
    )


def setup_energy_advisor_session(agent_type="comprehensive"):
    """
    Set up the session and runner for the energy advisor agent
    
    Args:
        agent_type: "comprehensive", "coordinator", or "specialized"
    """
    
    # Create the appropriate agent
    if agent_type == "comprehensive":
        agent = create_comprehensive_energy_agent()
    elif agent_type == "coordinator":
        agent = create_energy_coordinator_agent()
    else:
        raise ValueError("agent_type must be 'comprehensive' or 'coordinator'")
    
    # Session management
    session_service = InMemorySessionService()
    session = session_service.create_session(
        app_name=config.app_name, 
        user_id=config.user_id, 
        session_id=config.session_id
    )
    
    # Create runner
    runner = Runner(
        agent=agent, 
        app_name=config.app_name, 
        session_service=session_service
    )
    
    return agent, runner, session_service


def chat_with_energy_advisor(message: str, runner: Runner):
    """
    Handle conversation with the energy advisor agent
    """
    try:
        content = types.Content(
            role='user', 
            parts=[types.Part(text=message)]
        )
        
        events = runner.run(
            user_id=config.user_id, 
            session_id=config.session_id, 
            new_message=content
        )
        
        # Process events and get final response
        for event in events:
            if event.is_final_response():
                final_response = event.content.parts[0].text
                return final_response
                
        return "No response received from agent."
        
    except Exception as e:
        return f"Error communicating with agent: {str(e)}"


def run_energy_advisor_examples():
    """
    Example interactions with the energy advisor agent
    """
    
    # Setup
    agent, runner, session_service = setup_energy_advisor_session()
    
    # Test scenarios
    test_queries = [
        "Analyze TOU plan fit for customer CUST000001",
        "What's the energy efficiency analysis for CUST000001?",
        "Give me comprehensive energy insights for customer CUST000001",
        "Create a SQL query to show daily usage trends for CUST000001 over the last 7 days",
        "How much could customer CUST000001 save by switching to a TOU plan?",
        "What are the top energy efficiency improvements for CUST000001?"
    ]
    
    print("=== Energy Advisor Agent Test ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 50)
        
        response = chat_with_energy_advisor(query, runner)
        print(f"Response: {response}\n")
        print("=" * 70 + "\n")


# Create the root_agent that ADK expects to find
root_agent = create_comprehensive_energy_agent()


if __name__ == "__main__":
    # Run example interactions
    run_energy_advisor_examples()