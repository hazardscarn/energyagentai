"""
Enhanced Multi-Agent AI Assistant Streamlit App
Supports Visualization Agent, Sales Agent, Energy Efficiency Agent, and Marketing Agent
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
import traceback
import asyncio
import uuid
import re
import base64

# Page configuration
st.set_page_config(
    page_title="Alberta Energy AI - Multi-Agent Assistant",
    page_icon="⚡",
    layout="centered",
    initial_sidebar_state="expanded"
)


# Custom CSS for multi-agent chatbot
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .sales-header {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .energy-header {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .marketing-header {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 0.5rem 0;
        margin-left: 20%;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    .agent-message {
        background: #ffffff;
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .sales-message {
        background: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        border: 1px solid #f5576c;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .energy-message {
        background: linear-gradient(135deg, #e8f5e8 0%, #d4edda 100%);
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        border: 1px solid #56ab2f;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .marketing-message {
        background: linear-gradient(135deg, #ffeef8 0%, #fce4ec 100%);
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        border: 1px solid #ff9a9e;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .viz-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    .marketing-container {
        background: #ffeef8;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        border: 1px solid #ff9a9e;
    }
    .agent-selector {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border-left: 4px solid #667eea;
    }
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        border: none;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_agent' not in st.session_state:
    st.session_state.current_agent = "visualization"
if 'viz_messages' not in st.session_state:
    st.session_state.viz_messages = []
if 'sales_messages' not in st.session_state:
    st.session_state.sales_messages = []
if 'energy_messages' not in st.session_state:
    st.session_state.energy_messages = []
if 'marketing_messages' not in st.session_state:
    st.session_state.marketing_messages = []
if 'viz_agent_loaded' not in st.session_state:
    st.session_state.viz_agent_loaded = False
if 'sales_agent_loaded' not in st.session_state:
    st.session_state.sales_agent_loaded = False
if 'energy_agent_loaded' not in st.session_state:
    st.session_state.energy_agent_loaded = False
if 'marketing_agent_loaded' not in st.session_state:
    st.session_state.marketing_agent_loaded = False
if 'viz_root_agent' not in st.session_state:
    st.session_state.viz_root_agent = None
if 'sales_root_agent' not in st.session_state:
    st.session_state.sales_root_agent = None
if 'energy_root_agent' not in st.session_state:
    st.session_state.energy_root_agent = None
if 'marketing_root_agent' not in st.session_state:
    st.session_state.marketing_root_agent = None
if 'viz_session_service' not in st.session_state:
    st.session_state.viz_session_service = None
if 'sales_session_service' not in st.session_state:
    st.session_state.sales_session_service = None
if 'energy_session_service' not in st.session_state:
    st.session_state.energy_session_service = None
if 'marketing_session_service' not in st.session_state:
    st.session_state.marketing_session_service = None
if 'viz_runner' not in st.session_state:
    st.session_state.viz_runner = None
if 'sales_runner' not in st.session_state:
    st.session_state.sales_runner = None
if 'energy_runner' not in st.session_state:
    st.session_state.energy_runner = None
if 'marketing_runner' not in st.session_state:
    st.session_state.marketing_runner = None
if 'show_technical_details' not in st.session_state:
    st.session_state.show_technical_details = False

# =============================================================================
# AGENT LOADING FUNCTIONS
# =============================================================================

@st.cache_resource
def load_visualization_agent():
    """Load visualization agent components"""
    try:
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner
        from google.genai.types import Content, Part
        from shared_tools.simple_sql_agents import initialize_sql_components
        
        initialize_sql_components()
        
        # Import visualization agent
        import visualization_agent.agent as va_module
        root_agent = va_module.root_agent
        
        # Setup ADK components
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="alberta_energy_viz",
            session_service=session_service
        )
        
        return root_agent, session_service, runner, True
        
    except Exception as e:
        st.error(f"Failed to load visualization agent: {str(e)}")
        return None, None, None, False

@st.cache_resource
def load_sales_agent():
    """Load sales agent components"""
    try:
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner
        from google.genai.types import Content, Part
        
        # Import sales agent
        import sales_agent.agent as sa_module
        root_agent = sa_module.root_agent
        
        # Setup ADK components
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="alberta_energy_sales",
            session_service=session_service
        )
        
        return root_agent, session_service, runner, True
        
    except Exception as e:
        st.error(f"Failed to load sales agent: {str(e)}")
        return None, None, None, False

@st.cache_resource
def load_energy_efficiency_agent():
    """Load energy efficiency agent components"""
    try:
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner
        from google.genai.types import Content, Part
        
        # Import energy efficiency agent (using your existing agent.py structure)
        import energy_efficiency.agent as energy_module  # Your energy agent from agent.py
        
        # Create the energy efficiency agent using your existing setup
        root_agent = energy_module.create_comprehensive_energy_agent()
        
        # Setup ADK components
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="alberta_energy_efficiency",
            session_service=session_service
        )
        
        return root_agent, session_service, runner, True
        
    except Exception as e:
        st.error(f"Failed to load energy efficiency agent: {str(e)}")
        return None, None, None, False

@st.cache_resource
def load_marketing_agent():
    """Load marketing agent components"""
    try:
        from google.adk.sessions import InMemorySessionService
        from google.adk.runners import Runner
        from google.genai.types import Content, Part
        
        # Import marketing agent
        import marketing_agent.agent as ma_module
        root_agent = ma_module.root_agent
        
        # Setup ADK components
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="alberta_energy_marketing",
            session_service=session_service
        )
        
        return root_agent, session_service, runner, True
        
    except Exception as e:
        st.error(f"Failed to load marketing agent: {str(e)}")
        return None, None, None, False

# =============================================================================
# SHARED UTILITY FUNCTIONS
# =============================================================================

def extract_python_code(text):
    """Extract only Python code from agent response"""
    if "```python" in text:
        pattern = r'```python\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    lines = text.split('\n')
    code_lines = []
    collecting_code = False
    
    for line in lines:
        stripped = line.strip()
        
        if (stripped.startswith(('import ', 'from ')) or 
            stripped.startswith(('data_rows = [')) or
            any(keyword in stripped for keyword in ['plt.', 'sns.', 'pd.', 'np.'])):
            collecting_code = True
            code_lines.append(line)
        elif collecting_code:
            if (line.strip() == '' or  # empty lines
                stripped.startswith((' ', '\t')) or  # indented lines
                stripped.startswith('#') or  # comments
                any(keyword in stripped for keyword in ['plt.', 'sns.', 'pd.', 'np.', '=', 'df', 'fig', 'ax'])):
                code_lines.append(line)
    
    if code_lines:
        return '\n'.join(code_lines).strip()
    
    return text.strip()

def extract_marketing_package_data(response_text):
    """Extract marketing package data from agent response"""
    try:
        # Look for JSON data in the response
        import json
        
        # Try to find JSON structure in the response
        lines = response_text.split('\n')
        json_lines = []
        in_json = False
        
        for line in lines:
            if line.strip().startswith('{') and ('success' in line or 'zip_data' in line):
                in_json = True
                json_lines.append(line)
            elif in_json:
                json_lines.append(line)
                if line.strip().endswith('}') and len(json_lines) > 10:  # Reasonable JSON size
                    break
        
        if json_lines:
            json_text = '\n'.join(json_lines)
            try:
                package_data = json.loads(json_text)
                return package_data
            except json.JSONDecodeError:
                pass
        
        return None
        
    except Exception as e:
        print(f"Error extracting package data: {e}")
        return None

def execute_python_code(python_code, message_id):
    """Execute Python code and display the plot"""
    try:
        exec_globals = {
            'pd': pd,
            'plt': plt,
            'sns': sns,
            'np': np,
            'print': lambda *args: None,
        }
        
        try:
            from matplotlib.ticker import PercentFormatter
            exec_globals['PercentFormatter'] = PercentFormatter
        except:
            pass
        
        plt.ioff()
        plt.style.use('default')
        
        exec(python_code, exec_globals)
        
        if plt.get_fignums():
            for i, fig_num in enumerate(plt.get_fignums()):
                fig = plt.figure(fig_num)
                fig.set_size_inches(10, 6)
                
                with st.container():
                    st.pyplot(fig, use_container_width=True)
                    
                    img_buffer = BytesIO()
                    fig.savefig(img_buffer, format='png', dpi=300, bbox_inches='tight')
                    img_buffer.seek(0)
                    
                    st.download_button(
                        label="📥 Download Chart",
                        data=img_buffer.getvalue(),
                        file_name=f"chart_{message_id}_{i}.png",
                        mime="image/png",
                        key=f"download_{message_id}_{i}"
                    )
            
            plt.close('all')
            return True
        else:
            st.info("Code executed successfully but no visualizations were generated.")
            return False
            
    except Exception as e:
        st.error(f"❌ Visualization error: {str(e)}")
        return False

async def run_agent_async(user_input, runner, session_service, app_name):
    """Generic async agent runner with tool tracking"""
    try:
        from google.genai.types import Content, Part
        
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        session = await session_service.create_session(
            app_name=app_name,
            user_id="streamlit_user",
            session_id=session_id
        )
        
        content = Content(role='user', parts=[Part(text=user_input)])
        
        final_response = ""
        tool_status_placeholder = st.empty()
        
        # Tool name mapping for better display
        tool_display_names = {
            # Sales tools
            'extract_customer_data': '👤 Extracting customer data',
            'identify_sales_opportunities': '🎯 Identifying sales opportunities',
            'analyze_sales_promoting_factors': '📈 Analyzing promoting factors',
            'analyze_sales_preventing_factors': '📉 Analyzing preventing factors', 
            'generate_sales_email_tool': '📧 Generating sales email',
            'generate_call_script_tool': '📞 Generating call script',
            # Visualization tools
            'get_sql_data': '🔍 Retrieving SQL data',
            'generate_visualization_code': '🎨 Generating visualization code',
            # Energy efficiency tools
            'analyze_tou_plan_fit': '⚡ Analyzing TOU plan fit',
            'analyze_energy_efficiency': '🔋 Analyzing energy efficiency',
            'get_customer_energy_insights': '📊 Getting energy insights',
            'generate_sql_query_tool': '🔍 Generating SQL query',
            'execute_query_dataframe_tool': '📋 Executing query (DataFrame)',
            'execute_query_json_tool': '📝 Executing query (JSON)',
            # Marketing tools
            'marketing_coordinator_tool': '🎯 Marketing Coordinator',
            'email_marketing_specialist_tool': '📧 Email Marketing Specialist',
            'social_media_specialist_tool': '📱 Social Media Specialist',
            'direct_mail_specialist_tool': '📮 Direct Mail Specialist',
            'web_landing_page_specialist_tool': '🌐 Landing Page Specialist'
        }
        
        async for event in runner.run_async(
            user_id="streamlit_user",
            session_id=session_id,
            new_message=content
        ):
            # Check for tool usage events
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts'):
                    for part in event.content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            tool_name = part.function_call.name
                            display_name = tool_display_names.get(tool_name, f'🔧 {tool_name}')
                            tool_status_placeholder.info(f"**{display_name}**")
                        elif hasattr(part, 'function_response') and part.function_response:
                            tool_status_placeholder.success("✅ Tool completed")
            
            # Check for sub-agent delegation
            if hasattr(event, 'agent_name') and event.agent_name:
                agent_display_names = {
                    'sql_data_retrieval_agent': '🔍 SQL Data Agent working',
                    'intelligent_visualization_generator': '🎨 Visualization Generator working',
                    'code_execution_agent': '💻 Code Executor working',
                    'tou_specialist': '⚡ TOU Specialist working',
                    'efficiency_specialist': '🔋 Efficiency Specialist working',
                    'sql_specialist': '🔍 SQL Specialist working',
                    'marketing_coordinator': '🎯 Marketing Coordinator working',
                    'social_media_specialist': '📱 Social Media Specialist working'
                }
                display_name = agent_display_names.get(event.agent_name, f'🤖 {event.agent_name} working')
                tool_status_placeholder.info(f"**{display_name}**")
            
            # Collect final response
            if event.is_final_response():
                tool_status_placeholder.success("✅ **Workflow completed!**")
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'text') and part.text:
                            final_response += part.text
        
        # Clear tool status after a brief delay
        import time
        time.sleep(1)
        tool_status_placeholder.empty()
        
        return final_response if final_response else "No response generated"
        
    except Exception as e:
        if 'tool_status_placeholder' in locals():
            tool_status_placeholder.error(f"❌ **Error: {str(e)}**")
        raise Exception(f"Agent execution error: {str(e)}")

def run_agent(user_input, runner, session_service, app_name):
    """Synchronous wrapper for async agent execution"""
    try:
        return asyncio.run(run_agent_async(user_input, runner, session_service, app_name))
    except Exception as e:
        raise Exception(f"Agent execution error: {str(e)}")

# =============================================================================
# VISUALIZATION AGENT PAGE
# =============================================================================

def visualization_agent_page():
    """Visualization agent chat interface"""
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📊 Visualization Agent</h1>
        <p>Multi-Agent Data Visualization Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load visualization agent
    if not st.session_state.viz_agent_loaded:
        with st.spinner("🚀 Loading visualization agents..."):
            agent, session_service, runner, loaded = load_visualization_agent()
            st.session_state.viz_root_agent = agent
            st.session_state.viz_session_service = session_service
            st.session_state.viz_runner = runner
            st.session_state.viz_agent_loaded = loaded
    
    if not st.session_state.viz_agent_loaded:
        st.error("❌ Visualization agent failed to load")
        return
    
    # Chat interface
    st.markdown("### 💬 Chat with Visualization AI")
    
    # Display chat messages
    for message in st.session_state.viz_messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            if st.session_state.show_technical_details:
                st.markdown(f"""
                <div class="agent-message">
                    <strong>🤖 AI Agent:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
            
            if "python_code" in message and message["python_code"].strip():
                st.markdown('<div class="viz-container">', unsafe_allow_html=True)
                st.markdown("📊 **Generated Visualization:**")
                execute_python_code(message["python_code"], message["id"])
                st.markdown('</div>', unsafe_allow_html=True)
            
            elif not st.session_state.show_technical_details:
                st.markdown("""
                <div class="agent-message">
                    <strong>🤖 AI Agent:</strong> ✅ Analysis complete! Here's your visualization:
                </div>
                """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    with st.form("viz_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask about Alberta energy data:",
            placeholder="What is the average churn rate by city?",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            send_button = st.form_submit_button("Send 📤", type="primary")
    
    # Quick examples
    st.markdown("**💡 Try these examples:**")
    viz_examples = [
        "What is the average churn rate by city?",
        "What is the average monthly usage by city",
        "Create a heatmap of sales rate of HVAC cross sell among different age group and segments",
        "What is the sales rate of solar across different tech segments?"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(viz_examples):
        with cols[i % 2]:
            if st.button(example, key=f"viz_example_{i}"):
                process_viz_message(example)
    
    if send_button and user_input.strip():
        process_viz_message(user_input.strip())

def process_viz_message(user_input):
    """Process visualization agent message"""
    message_id = len(st.session_state.viz_messages)
    
    st.session_state.viz_messages.append({
        "role": "user", 
        "content": user_input,
        "id": message_id
    })
    
    with st.spinner("🤖 AI agents working: SQL → Analysis → Visualization..."):
        try:
            if st.session_state.viz_runner and st.session_state.viz_session_service:
                response_text = run_agent(
                    user_input, 
                    st.session_state.viz_runner, 
                    st.session_state.viz_session_service,
                    "alberta_energy_viz"
                )
                
                python_code = extract_python_code(response_text)
                
                st.session_state.viz_messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "python_code": python_code,
                    "id": message_id + 1
                })
            else:
                st.session_state.viz_messages.append({
                    "role": "assistant",
                    "content": "❌ Visualization agent system not initialized.",
                    "id": message_id + 1
                })
                
        except Exception as e:
            error_msg = f"❌ Visualization agent error: {str(e)}"
            st.session_state.viz_messages.append({
                "role": "assistant",
                "content": error_msg,
                "id": message_id + 1
            })
    
    st.rerun()

# =============================================================================
# SALES AGENT PAGE
# =============================================================================

def sales_agent_page():
    """Sales agent chat interface"""
    
    # Header
    st.markdown("""
    <div class="sales-header">
        <h1>🎯 Sales Agent</h1>
        <p>Personalized Customer Sales Assistant</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load sales agent
    if not st.session_state.sales_agent_loaded:
        with st.spinner("🚀 Loading sales agent..."):
            agent, session_service, runner, loaded = load_sales_agent()
            st.session_state.sales_root_agent = agent
            st.session_state.sales_session_service = session_service
            st.session_state.sales_runner = runner
            st.session_state.sales_agent_loaded = loaded
    
    if not st.session_state.sales_agent_loaded:
        st.error("❌ Sales agent failed to load")
        return
    
    # Chat interface
    st.markdown("### 💼 Chat with Sales AI")
    
    # Display chat messages
    for message in st.session_state.sales_messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="sales-message">
                <strong>🎯 Sales Agent:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    with st.form("sales_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask about sales campaigns and customer analysis:",
            placeholder="Create sales campaign for customer CUST00000598",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            send_button = st.form_submit_button("Send 🎯", type="primary")
    
    # Quick examples
    st.markdown("**💡 Try these sales examples:**")
    sales_examples = [
        "Create sales email campaign for customer CUST00002467",
        "Generate sales call script for customer CUST00003397",
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(sales_examples):
        with cols[i % 2]:
            if st.button(example, key=f"sales_example_{i}"):
                process_sales_message(example)
    
    if send_button and user_input.strip():
        process_sales_message(user_input.strip())

def process_sales_message(user_input):
    """Process sales agent message"""
    message_id = len(st.session_state.sales_messages)
    
    st.session_state.sales_messages.append({
        "role": "user", 
        "content": user_input,
        "id": message_id
    })
    
    with st.spinner("🎯 Sales AI working: Customer Analysis → SHAP Insights → Content Generation..."):
        try:
            if st.session_state.sales_runner and st.session_state.sales_session_service:
                response_text = run_agent(
                    user_input, 
                    st.session_state.sales_runner, 
                    st.session_state.sales_session_service,
                    "alberta_energy_sales"
                )
                
                st.session_state.sales_messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "id": message_id + 1
                })
            else:
                st.session_state.sales_messages.append({
                    "role": "assistant",
                    "content": "❌ Sales agent system not initialized.",
                    "id": message_id + 1
                })
                
        except Exception as e:
            error_msg = f"❌ Sales agent error: {str(e)}"
            st.session_state.sales_messages.append({
                "role": "assistant",
                "content": error_msg,
                "id": message_id + 1
            })
    
    st.rerun()

# =============================================================================
# ENERGY EFFICIENCY AGENT PAGE
# =============================================================================

def energy_efficiency_agent_page():
    """Energy efficiency agent chat interface"""
    
    # Header
    st.markdown("""
    <div class="energy-header">
        <h1>🔋 Energy Efficiency Agent</h1>
        <p>Smart Meter Data Analysis & Optimization</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load energy efficiency agent
    if not st.session_state.energy_agent_loaded:
        with st.spinner("🚀 Loading energy efficiency agent..."):
            agent, session_service, runner, loaded = load_energy_efficiency_agent()
            st.session_state.energy_root_agent = agent
            st.session_state.energy_session_service = session_service
            st.session_state.energy_runner = runner
            st.session_state.energy_agent_loaded = loaded
    
    if not st.session_state.energy_agent_loaded:
        st.error("❌ Energy efficiency agent failed to load")
        return
    
    # Chat interface
    st.markdown("### ⚡ Chat with Energy Efficiency AI")
    
    # Display chat messages
    for message in st.session_state.energy_messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="energy-message">
                <strong>🔋 Energy Agent:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    with st.form("energy_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask about energy efficiency and TOU plans:",
            placeholder="Analyze TOU plan fit for customer CUST000001",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            send_button = st.form_submit_button("Send ⚡", type="primary")
    
    # Quick examples
    st.markdown("**💡 Try these energy examples:**")
    energy_examples = [
        "Analyze TOU plan fit for customer CUST000001",
        "What's the energy efficiency analysis for CUST000001?",
        "Give me comprehensive energy insights for customer CUST000001",
        "How much could customer CUST000001 save by switching to a TOU plan?",
        "What are the top energy efficiency improvements for CUST000001?",
        "Create a SQL query to show daily usage trends for CUST000001 over the last 7 days"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(energy_examples):
        with cols[i % 2]:
            if st.button(example, key=f"energy_example_{i}"):
                process_energy_message(example)
    
    if send_button and user_input.strip():
        process_energy_message(user_input.strip())

def process_energy_message(user_input):
    """Process energy efficiency agent message"""
    message_id = len(st.session_state.energy_messages)
    
    st.session_state.energy_messages.append({
        "role": "user", 
        "content": user_input,
        "id": message_id
    })
    
    with st.spinner("⚡ Energy AI working: Smart Meter Analysis → TOU Assessment → Efficiency Recommendations..."):
        try:
            if st.session_state.energy_runner and st.session_state.energy_session_service:
                response_text = run_agent(
                    user_input, 
                    st.session_state.energy_runner, 
                    st.session_state.energy_session_service,
                    "alberta_energy_efficiency"
                )
                
                st.session_state.energy_messages.append({
                    "role": "assistant",
                    "content": response_text,
                    "id": message_id + 1
                })
            else:
                st.session_state.energy_messages.append({
                    "role": "assistant",
                    "content": "❌ Energy efficiency agent system not initialized.",
                    "id": message_id + 1
                })
                
        except Exception as e:
            error_msg = f"❌ Energy efficiency agent error: {str(e)}"
            st.session_state.energy_messages.append({
                "role": "assistant",
                "content": error_msg,
                "id": message_id + 1
            })
    
    st.rerun()

# =============================================================================
# MARKETING AGENT PAGE
# =============================================================================

def marketing_agent_page():
    """Marketing agent chat interface"""
    
    # Header
    st.markdown("""
    <div class="marketing-header">
        <h1>🎯 Marketing Agent</h1>
        <p>AI-Powered Marketing Campaign Generator</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load marketing agent
    if not st.session_state.marketing_agent_loaded:
        with st.spinner("🚀 Loading marketing agent..."):
            agent, session_service, runner, loaded = load_marketing_agent()
            st.session_state.marketing_root_agent = agent
            st.session_state.marketing_session_service = session_service
            st.session_state.marketing_runner = runner
            st.session_state.marketing_agent_loaded = loaded
    
    if not st.session_state.marketing_agent_loaded:
        st.error("❌ Marketing agent failed to load")
        return
    
    # Chat interface
    st.markdown("### 🎨 Chat with Marketing AI")
    
    # Display chat messages
    for message in st.session_state.marketing_messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="marketing-message">
                <strong>🎯 Marketing Agent:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
            
            # Check for marketing package data
            if "package_data" in message:
                package_data = message["package_data"]
                if package_data and package_data.get("success"):
                    st.markdown('<div class="marketing-container">', unsafe_allow_html=True)
                    st.markdown("📦 **Marketing Package Generated!**")
                    
                    # Package info
                    package_info = package_data.get("package_info", {})
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📋 Campaign Type", package_info.get("medium", "Marketing"))
                    with col2:
                        st.metric("📅 Created", package_info.get("created_at", "Now")[:16])
                    with col3:
                        st.metric("🖼️ Image", "✅ Included" if package_data.get("image_available") else "❌ Failed")
                    
                    # Download button
                    if package_data.get("zip_data"):
                        try:
                            zip_data = base64.b64decode(package_data["zip_data"])
                            filename = package_data.get("filename", "marketing_package.zip")
                            
                            st.download_button(
                                label="📦 Download Complete Marketing Package",
                                data=zip_data,
                                file_name=filename,
                                mime="application/zip",
                                help="Complete marketing package with content, images, and instructions"
                            )
                        except Exception as e:
                            st.error(f"❌ Download error: {str(e)}")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    with st.form("marketing_chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Ask about marketing campaigns and content creation:",
            placeholder="Create social media campaign for HVAC services",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns([3, 1])
        with col2:
            send_button = st.form_submit_button("Send 🎯", type="primary")
    
    # Quick examples
    st.markdown("**💡 Try these marketing examples:**")
    marketing_examples = [
        "Create social media campaign for HVAC services targeting Calgary homeowners",
        "Generate email marketing campaign for energy efficiency upgrades",
        "Design direct mail campaign for smart thermostat installations",
        "Create landing page content for solar panel installations",
        "Generate winter heating preparation social media posts",
        "Create cross-sell campaign for heat pump upgrades"
    ]
    
    cols = st.columns(2)
    for i, example in enumerate(marketing_examples):
        with cols[i % 2]:
            if st.button(example, key=f"marketing_example_{i}"):
                process_marketing_message(example)
    
    if send_button and user_input.strip():
        process_marketing_message(user_input.strip())

def process_marketing_message(user_input):
    """Process marketing agent message"""
    message_id = len(st.session_state.marketing_messages)
    
    st.session_state.marketing_messages.append({
        "role": "user", 
        "content": user_input,
        "id": message_id
    })
    
    with st.spinner("🎯 Marketing AI working: Campaign Analysis → Content Generation → Image Creation → Package Assembly..."):
        try:
            if st.session_state.marketing_runner and st.session_state.marketing_session_service:
                response_text = run_agent(
                    user_input, 
                    st.session_state.marketing_runner, 
                    st.session_state.marketing_session_service,
                    "alberta_energy_marketing"
                )
                
                # Extract package data if available
                package_data = extract_marketing_package_data(response_text)
                
                message_data = {
                    "role": "assistant",
                    "content": response_text,
                    "id": message_id + 1
                }
                
                if package_data:
                    message_data["package_data"] = package_data
                
                st.session_state.marketing_messages.append(message_data)
            else:
                st.session_state.marketing_messages.append({
                    "role": "assistant",
                    "content": "❌ Marketing agent system not initialized.",
                    "id": message_id + 1
                })
                
        except Exception as e:
            error_msg = f"❌ Marketing agent error: {str(e)}"
            st.session_state.marketing_messages.append({
                "role": "assistant",
                "content": error_msg,
                "id": message_id + 1
            })
    
    st.rerun()

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application with agent selection"""
    
    # Agent selector in sidebar
    with st.sidebar:
        st.markdown("### 🤖 Select AI Agent")
        
        agent_choice = st.radio(
            "Choose your AI assistant:",
            ["📊 Visualization Agent", "🎯 Sales Agent", "🔋 Energy Efficiency Agent", "🎨 Marketing Agent"],
            index=0 if st.session_state.current_agent == "visualization" 
                  else 1 if st.session_state.current_agent == "sales" 
                  else 2 if st.session_state.current_agent == "energy"
                  else 3,
            key="agent_selector"
        )
        
        # Update current agent
        new_agent = ("visualization" if "Visualization" in agent_choice 
                    else "sales" if "Sales" in agent_choice 
                    else "energy" if "Energy" in agent_choice
                    else "marketing")
        if new_agent != st.session_state.current_agent:
            st.session_state.current_agent = new_agent
            st.rerun()
        
        st.markdown("---")
        
        # System status
        st.markdown("### 🎯 System Status")
        
        if st.session_state.current_agent == "visualization":
            if st.session_state.viz_agent_loaded:
                st.success("✅ Visualization System Online")
                st.markdown("""
                **🔄 Workflow:**
                1. 🔍 SQL Data Agent
                2. 🎨 Visualization Generator  
                3. 💻 Code Executor
                4. 📊 Display Results
                """)
            else:
                st.error("❌ Visualization System Offline")
        elif st.session_state.current_agent == "sales":
            if st.session_state.sales_agent_loaded:
                st.success("✅ Sales System Online")
                st.markdown("""
                **🔄 Workflow:**
                1. 👤 Customer Analysis
                2. 🧠 SHAP Factor Analysis
                3. 📧 Content Generation
                4. 🎯 Sales Insights
                """)
            else:
                st.error("❌ Sales System Offline")
        elif st.session_state.current_agent == "energy":
            if st.session_state.energy_agent_loaded:
                st.success("✅ Energy Efficiency System Online")
                st.markdown("""
                **🔄 Workflow:**
                1. ⚡ Smart Meter Data Analysis
                2. 🔍 TOU Plan Assessment
                3. 🔋 Efficiency Analysis
                4. 📊 Savings Recommendations
                """)
            else:
                st.error("❌ Energy Efficiency System Offline")
        else:  # marketing
            if st.session_state.marketing_agent_loaded:
                st.success("✅ Marketing System Online")
                st.markdown("""
                **🔄 Workflow:**
                1. 🎯 Campaign Analysis
                2. 📝 Content Generation
                3. 🎨 Image Creation
                4. 📦 Package Assembly
                """)
            else:
                st.error("❌ Marketing System Offline")
        
        st.markdown("### ⚙️ Display Options")
        
        # Toggle for technical details (only for visualization)
        if st.session_state.current_agent == "visualization":
            show_details = st.toggle(
                "Show Technical Details",
                value=st.session_state.show_technical_details,
                help="Show agent responses and generated code"
            )
            
            if show_details != st.session_state.show_technical_details:
                st.session_state.show_technical_details = show_details
                st.rerun()
            
            if st.session_state.show_technical_details:
                st.info("💬 Agent responses and code are visible")
                
                if st.session_state.viz_messages:
                    last_message = st.session_state.viz_messages[-1]
                    if last_message.get("role") == "assistant" and "python_code" in last_message:
                        with st.expander("🔧 Last Generated Code"):
                            st.code(last_message["python_code"], language="python")
            else:
                st.info("🎯 Clean view - only visualizations shown")
        
        st.markdown("### ℹ️ About")
        if st.session_state.current_agent == "visualization":
            st.markdown("""
            **Visualization Agent:**
            - Natural language to SQL queries
            - Intelligent chart generation
            - Multi-agent coordination
            - Code execution & display
            """)
        elif st.session_state.current_agent == "sales":
            st.markdown("""
            **Sales Agent:**
            - Customer profile analysis
            - SHAP-based insights
            - Personalized email generation
            - Call script creation
            """)
        elif st.session_state.current_agent == "energy":
            st.markdown("""
            **Energy Efficiency Agent:**
            - Smart meter data analysis
            - TOU plan optimization
            - Energy efficiency recommendations
            - Usage pattern insights
            - Cost savings analysis
            """)
        else:  # marketing
            st.markdown("""
            **Marketing Agent:**
            - Multi-specialist marketing system
            - Social media campaign creation
            - Email marketing automation
            - Image generation (no text)
            - Downloadable marketing packages
            """)
        
        st.markdown("### 🛠️ Actions")
        if st.button("🔄 Refresh System"):
            st.cache_resource.clear()
            st.session_state.viz_agent_loaded = False
            st.session_state.sales_agent_loaded = False
            st.session_state.energy_agent_loaded = False
            st.session_state.marketing_agent_loaded = False
            st.rerun()
        
        if st.button("🗑️ Clear Current Chat"):
            if st.session_state.current_agent == "visualization":
                st.session_state.viz_messages = []
            elif st.session_state.current_agent == "sales":
                st.session_state.sales_messages = []
            elif st.session_state.current_agent == "energy":
                st.session_state.energy_messages = []
            else:  # marketing
                st.session_state.marketing_messages = []
            st.rerun()
        
        if st.button("🗑️ Clear All Chats"):
            st.session_state.viz_messages = []
            st.session_state.sales_messages = []
            st.session_state.energy_messages = []
            st.session_state.marketing_messages = []
            st.rerun()
    
    # Display current agent page
    if st.session_state.current_agent == "visualization":
        visualization_agent_page()
    elif st.session_state.current_agent == "sales":
        sales_agent_page()
    elif st.session_state.current_agent == "energy":
        energy_efficiency_agent_page()
    else:  # marketing
        marketing_agent_page()

if __name__ == "__main__":
    main()