"""
Enhanced Main Coordinator Agent with better visualization handling
Properly routes and formats responses from visualization specialist
"""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
import asyncio

# Import your existing agents
from visualization_agent.agent import root_agent as visualization_agent
from energy_efficiency.agent import root_agent as energy_efficiency_agent
from sales_agent.agent import root_agent as sales_agent
from retention_agent.agent import root_agent as retention_agent
from portfolio_manager.agent import root_agent as portfolio_manager_agent

from .config import Config
config=Config()


# Create AgentTools - NO DESCRIPTION PARAMETER!
energy_tool = AgentTool(agent=energy_efficiency_agent)
sales_tool = AgentTool(agent=sales_agent)
visualization_tool = AgentTool(agent=visualization_agent)
retention_tool = AgentTool(agent=retention_agent)
portfolio_tool = AgentTool(agent=portfolio_manager_agent)

# Enhanced Main Coordinator Agent
main_coordinator = Agent(
    name="WattsWise_AI",
    model=config.default_model,
    description="Main interface for Alberta Energy AI system - coordinates all energy, sales, and visualization tasks",
    
    instruction="""You are the main coordinator for Alberta Energy AI system. You have access to three specialized agents:

    **Energy Efficiency Specialist**: For energy analysis, TOU plans, usage patterns, efficiency recommendations
    **Sales Specialist**: For creating personalized sales emails or call scripts or audio sales call pitch for upsell/crosssell opportunities  
    **Visualization Specialist**: For creating charts, graphs, and visual analytics
    **Retention Agent: For creating personalized customer retention email or call scripts
    **Portfolio Manager Agent**: For portfolio level analysis and insights & to handle simple data questions from user

    **Your Role:**
    - Understand what the user wants to accomplish
    - Route requests to the appropriate specialist agent(s)
    - Present results appropriately based on the request type

    **Routing Guidelines:**
    - Energy questions (efficiency, TOU, usage patterns, savings) → Energy Efficiency Specialist
    - Sales requests (emails, call scripts, campaigns, opportunities) → Sales Specialist  
    - Charts/graphs/visualization requests (show, create, display, chart, graph, visual, heatmap, histogram) → Visualization Specialist
    - Complex requests may need multiple specialists
    - Personalized retention requests (emails, call scripts) → Retention Agent
    - Portfolio level analysis and insights → Portfolio Manager Agent
    - Portfolio level/subset of customer level analysis → Portfolio Manager Agent
    - General questions about the portfolio → Portfolio Manager Agent [ eg: How many customers are there in Calgray? Give a list of 10 customers etc.]

    - To understand the reasons/patterns behind sales or churn for a subset or a portfolio use Portfolio Manager Agent

    **CRITICAL Response Guidelines:**

    **For Visualization Requests ONLY:**
    - Return EXACTLY what the Visualization Specialist provides
    - Do NOT add any commentary, explanations, or additional text
    - Do NOT say "The Visualization Specialist has provided..." 
    - Do NOT modify, wrap, or summarize the response
    - Just return the specialist's response verbatim
    - Do NOT ask for SQL queries or dataset names
    - If you need more information to decide which agent to use, ask the user for more details BUT ONLY if the request is not clear

    **For Energy/Sales Requests:**
    - Understand and provide all the details from the specialist to the user
    - Do Not skip any important information

    **For Multiple Specialists:**
    - Combine insights coherently with clear sections

    **For Comprehensice Reports or Analysis on Sales/Churn for a subset**
    - Use Portfolio Manager Agent

    - Use retention agent only for personalized retention requests for a single customer only
    - Use sales specialist for personalized sales requests for a single customer only


    **EXAMPLES:**
    ❌ WRONG for visualization: "The Visualization Specialist has provided the following Python code: [code]"
    ✅ CORRECT for visualization: Just return the specialist's response exactly as received

    Start by greeting the user and explaining your capabilities.""",
    
    tools=[energy_tool, sales_tool, visualization_tool,retention_tool,portfolio_tool]
)

# =============================================================================
# SESSION AND RUNNER SETUP
# =============================================================================

def setup_main_coordinator_session():
    """Set up the session and runner for the main coordinator"""
    
    session_service = InMemorySessionService()
    
    runner = Runner(
        agent=main_coordinator, 
        app_name="alberta_energy_ai_main", 
        session_service=session_service
    )
    
    return main_coordinator, runner, session_service

# =============================================================================
# ENHANCED LIVE TRACKING WITH VISUALIZATION DETECTION
# =============================================================================

async def chat_with_coordinator_live_stream(message: str, runner: Runner, session_service):
    """Enhanced async generator with better visualization handling"""
    try:
        from google.genai.types import Content, Part
        import uuid
        
        session_id = f"coordinator_session_{uuid.uuid4().hex[:8]}"
        session = await session_service.create_session(
            app_name="alberta_energy_ai_main",
            user_id="main_user",
            session_id=session_id
        )
        
        content = Content(role='user', parts=[Part(text=message)])
        
        # Enhanced tool mapping
        TOOL_DISPLAY_NAMES = {
            'energy_efficiency_specialist': '🔋 Energy Efficiency Specialist',
            'sales_specialist': '💼 Sales Specialist',
            'visualization_specialist': '📊 Visualization Specialist',
            'retention_agent': '🔄 Retention Specialist',
            'portfolio_manager_agent': '📈 Portfolio Manager',
            'marketing_agent': '🎯 Marketing Specialist',
            # Energy tools
            'analyze_tou_plan_fit': '⚡ TOU Plan Analysis',
            'analyze_energy_efficiency': '🔋 Energy Efficiency Analysis',
            'get_customer_energy_insights': '📊 Customer Energy Insights',
            # Sales tools
            'extract_customer_data': '👤 Customer Data Extraction',
            'identify_sales_opportunities': '🎯 Sales Opportunity Analysis',
            'generate_sales_email_tool': '📧 Sales Email Generation',
            'generate_call_script_tool': '📞 Call Script Generation',
            # Visualization tools
            'get_sql_data': '🔍 SQL Data Retrieval',
            'generate_sql_query_tool': '🔍 SQL Query Generation',
            'execute_query_json_tool': '📝 Query Execution',
            'generate_visualization_code': '🎨 Visualization Code Generation'
        }
        
        final_response = ""
        current_specialist = None
        
        # Detect if this is a visualization request
        viz_keywords = ['chart', 'graph', 'plot', 'visual', 'show', 'display', 'create', 'heatmap', 'histogram']
        is_viz_request = any(keyword in message.lower() for keyword in viz_keywords)
        
        yield {
            'type': 'STATUS',
            'message': '🤖 Main Coordinator - Analyzing request...',
            'is_visualization': is_viz_request
        }
        
        # Stream events with enhanced context
        async for event in runner.run_async(
            user_id="main_user",
            session_id=session_id,
            new_message=content
        ):
            # Track tool usage with specialist context
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            tool_name = part.function_call.name
                            display_name = TOOL_DISPLAY_NAMES.get(tool_name, f'🔧 {tool_name}')
                            
                            # Track which specialist is being used
                            if tool_name in ['energy_efficiency_specialist', 'sales_specialist', 'visualization_specialist']:
                                current_specialist = display_name
                                yield {
                                    'type': 'SPECIALIST_START',
                                    'message': f'Consulting {display_name}...',
                                    'specialist': current_specialist
                                }
                            else:
                                # Specialist using internal tools
                                yield {
                                    'type': 'TOOL_START',
                                    'message': f'{current_specialist or "System"} → {display_name}',
                                    'specialist': current_specialist
                                }
                        
                        elif hasattr(part, 'function_response') and part.function_response:
                            response_name = getattr(part.function_response, 'name', 'unknown')
                            
                            if response_name in ['energy_efficiency_specialist', 'sales_specialist', 'visualization_specialist']:
                                specialist_name = TOOL_DISPLAY_NAMES.get(response_name, response_name)
                                yield {
                                    'type': 'SPECIALIST_COMPLETE',
                                    'message': f'{specialist_name} → Main Coordinator',
                                    'specialist': specialist_name
                                }
                                current_specialist = None
                            else:
                                yield {
                                    'type': 'TOOL_COMPLETE',
                                    'message': '✅ Tool completed',
                                    'specialist': current_specialist
                                }
            
            # Agent delegation tracking
            if hasattr(event, 'agent_name') and event.agent_name:
                agent_display = TOOL_DISPLAY_NAMES.get(event.agent_name, f'🤖 {event.agent_name}')
                yield {
                    'type': 'AGENT_DELEGATION',
                    'message': f'{agent_display} - Processing...',
                    'specialist': agent_display
                }
            
            # Final response handling
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text
                
                yield {
                    'type': 'FINAL',
                    'message': '🎯 Workflow completed!',
                    'response': final_response,
                    'is_visualization': is_viz_request
                }
                return
        
        # Fallback
        yield {
            'type': 'ERROR',
            'message': '❌ No response received',
            'response': 'No response received from coordinator.',
            'is_visualization': False
        }
        
    except Exception as e:
        yield {
            'type': 'ERROR',
            'message': f'❌ Error: {str(e)}',
            'response': f'Error: {str(e)}',
            'is_visualization': False
        }

# =============================================================================
# SIMPLIFIED CHAT FUNCTION (for compatibility)
# =============================================================================

async def chat_with_coordinator_async(message: str, runner: Runner, session_service):
    """Simple async version that just returns the response"""
    try:
        from google.genai.types import Content, Part
        import uuid
        
        session_id = f"coordinator_session_{uuid.uuid4().hex[:8]}"
        session = await session_service.create_session(
            app_name="alberta_energy_ai_main",
            user_id="main_user",
            session_id=session_id
        )
        
        content = Content(role='user', parts=[Part(text=message)])
        
        final_response = ""
        async for event in runner.run_async(
            user_id="main_user",
            session_id=session_id,
            new_message=content
        ):
            if event.is_final_response():
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text
        
        return final_response if final_response else "No response received from coordinator."
        
    except Exception as e:
        return f"Error communicating with coordinator: {str(e)}"

def chat_with_coordinator(message: str, runner: Runner, session_service):
    """Synchronous wrapper - returns just the response"""
    try:
        import asyncio
        return asyncio.run(chat_with_coordinator_async(message, runner, session_service))
    except Exception as e:
        return f"Error communicating with coordinator: {str(e)}"

# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

def run_coordinator_examples():
    """Test the enhanced coordinator"""
    
    agent, runner, session_service = setup_main_coordinator_session()
    
    test_queries = [
        "Hello! What can you help me with?",
        "Analyze energy efficiency for customer CUST000001",
        "Create sales campaign for customer CUST000002", 
        "What is the average churn rate by city?",  # Visualization request
        "Show me a chart of daily usage for customer CUST000003",  # Visualization request
        "Complete analysis for customer CUST000001"
    ]
    
    print("=== Enhanced Alberta Energy AI Coordinator Test ===\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"Query {i}: {query}")
        print("-" * 60)
        
        response = chat_with_coordinator(query, runner, session_service)
        print(f"Coordinator: {response}\n")
        
        # Check if response contains Python code
        if "```python" in response or any(keyword in response for keyword in ['import ', 'plt.', 'sns.', 'pd.']):
            print("📊 Contains visualization code!")
        
        print("=" * 80 + "\n")

# Root agent for ADK
root_agent = main_coordinator

if __name__ == "__main__":
    run_coordinator_examples()