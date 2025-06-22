"""
Enhanced Main Coordinator with Marketing Agent Navigation
Uses Streamlit navigation to separate Marketing Agent as independent system
"""

import streamlit as st
import asyncio
from datetime import datetime
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
import re
import json
import base64
import traceback

try:
    from main_agent.agent import main_coordinator, setup_main_coordinator_session, chat_with_coordinator_live_stream
    MAIN_COORDINATOR_AVAILABLE = True
except ImportError as e:
    MAIN_COORDINATOR_AVAILABLE = False
    print(f"🔍 MAIN AGENT IMPORT ERROR: {str(e)}")
    import traceback
    print(f"🔍 FULL TRACEBACK: {traceback.format_exc()}")
# Import the separate marketing agent system
try:
    from marketing_agent.agent import (
        generate_marketing_package,
        marketing_coordinator_tool,
        root_agent as marketing_root_agent
    )
    MARKETING_AGENT_AVAILABLE = True
except ImportError:
    MARKETING_AGENT_AVAILABLE = False

# =============================================================================
# STREAMLIT APP CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Alberta Energy AI - Multi-Agent Hub",
    page_icon="🤖⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS styling for both pages
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
    
    .marketing-header {
        background: linear-gradient(135deg, #4285F4 0%, #34A853 25%, #FBBC05 50%, #EA4335 75%);
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
    }
    
    .coordinator-message {
        background: #ffffff;
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .marketing-message {
        background: #f8f9fa;
        color: #333;
        padding: 0.8rem 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 0.5rem 0;
        margin-right: 20%;
        border: 1px solid #4285F4;
        box-shadow: 0 2px 4px rgba(66, 133, 244, 0.1);
    }
    
    .viz-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    }
    
    .agent-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e8eaed;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
    
    .success-box {
        background: #e8f5e8;
        border: 1px solid #34a853;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .agent-status {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 500;
    }
    
    .status-ready {
        background: #e8f5e8;
        color: #137333;
    }
    
    .status-working {
        background: #fef7e0;
        color: #ea8600;
    }
    
    .nav-page {
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .nav-page:hover {
        background: #f0f0f0;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

# Initialize session state for coordinator
if "coordinator_runner" not in st.session_state:
    st.session_state.coordinator_runner = None
    st.session_state.coordinator_agent = None
    st.session_state.session_service = None
    st.session_state.coordinator_messages = []
    st.session_state.coordinator_initialized = False

# Initialize session state for marketing
if "marketing_messages" not in st.session_state:
    st.session_state.marketing_messages = []

# Initialize display options
if "show_code" not in st.session_state:
    st.session_state.show_code = False

# =============================================================================
# VISUALIZATION HANDLING FUNCTIONS
# =============================================================================

def extract_python_code(text):
    """Extract Python code from agent response"""
    
    if "```python" in text:
        pattern = r'```python\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    if "```" in text:
        pattern = r'```\s*\n(.*?)\n```'
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            if any(keyword in match for keyword in ['import ', 'plt.', 'sns.', 'pd.', 'matplotlib', 'seaborn']):
                return match.strip()
    
    lines = text.split('\n')
    code_lines = []
    collecting_code = False
    
    for line in lines:
        stripped = line.strip()
        
        if (stripped.startswith(('import ', 'from ')) or 
            stripped.startswith(('data_rows = [')) or
            any(keyword in stripped for keyword in ['plt.', 'sns.', 'pd.', 'np.', 'matplotlib', 'seaborn', 'pyplot'])):
            collecting_code = True
            code_lines.append(line)
        elif collecting_code:
            if (line.strip() == '' or
                stripped.startswith((' ', '\t')) or
                stripped.startswith('#') or
                any(keyword in stripped for keyword in ['plt.', 'sns.', 'pd.', 'np.', '=', 'df', 'fig', 'ax', '.plot', '.bar', '.scatter', '.hist'])):
                code_lines.append(line)
            else:
                break
    
    if code_lines:
        code = '\n'.join(code_lines).strip()
        if len(code) > 20 and any(keyword in code for keyword in ['plt.', 'sns.', 'matplotlib', 'seaborn']):
            return code
    
    return ""

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

# =============================================================================
# COORDINATOR AGENT FUNCTIONS
# =============================================================================

@st.cache_resource
def load_coordinator_agent():
    """Load the main coordinator agent"""
    try:
        agent, runner, session_service = setup_main_coordinator_session()
        return agent, runner, session_service, True
    except Exception as e:
        st.error(f"Failed to load coordinator: {str(e)}")
        return None, None, None, False

def process_coordinator_message(user_input):
    """Process message with main coordinator"""
    
    st.session_state.coordinator_messages.append({
        "role": "user", 
        "content": user_input
    })
    
    status_placeholder = st.empty()
    
    try:
        import asyncio
        
        async def live_tracking():
            final_response = None
            
            async for live_event in chat_with_coordinator_live_stream(
                user_input,
                st.session_state.coordinator_runner,
                st.session_state.session_service
            ):
                if live_event['type'] == 'STATUS':
                    with status_placeholder.container():
                        st.info(f"**{live_event['message']}**")
                
                elif live_event['type'] == 'TOOL_START':
                    with status_placeholder.container():
                        st.info(f"🔧 **{live_event['message']}**")
                
                elif live_event['type'] == 'TOOL_COMPLETE':
                    with status_placeholder.container():
                        st.success(f"**{live_event['message']}**")
                
                elif live_event['type'] == 'AGENT_DELEGATION':
                    with status_placeholder.container():
                        st.warning(f"🤖 **{live_event['message']}**")
                
                elif live_event['type'] == 'FINAL':
                    with status_placeholder.container():
                        st.success(f"**{live_event['message']}**")
                    
                    final_response = live_event['response']
                    break
                
                elif live_event['type'] == 'ERROR':
                    with status_placeholder.container():
                        st.error(f"**{live_event['message']}**")
                    
                    final_response = live_event['response']
                    break
            
            return final_response
        
        response = asyncio.run(live_tracking())
        
        import time
        time.sleep(1)
        status_placeholder.empty()
        
        if response and response.strip():
            python_code = extract_python_code(response)
            
            message_data = {
                "role": "assistant",
                "content": response,
                "id": len(st.session_state.coordinator_messages)
            }
            
            if python_code.strip():
                message_data["python_code"] = python_code
            
            st.session_state.coordinator_messages.append(message_data)
        else:
            st.session_state.coordinator_messages.append({
                "role": "assistant",
                "content": "❌ No response received.",
                "id": len(st.session_state.coordinator_messages)
            })
            
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        st.session_state.coordinator_messages.append({
            "role": "assistant",
            "content": error_msg,
            "id": len(st.session_state.coordinator_messages)
        })
    
    st.rerun()

# =============================================================================
# MARKETING AGENT FUNCTIONS
# =============================================================================

def process_marketing_message(campaign_input, selected_medium):
    """Process message with marketing agent system"""
    
    # Add user message
    st.session_state.marketing_messages.append({
        "role": "user",
        "content": f"Create {selected_medium} campaign: {campaign_input}",
        "timestamp": datetime.now()
    })
    
    # Show agent workflow
    workflow_container = st.container()
    
    with workflow_container:
        # Step 1: Coordinator Analysis
        with st.status("🎯 Marketing Coordinator analyzing request...", expanded=True) as status:
            st.write("📋 Parsing campaign requirements")
            st.write("🔍 Analyzing target audience and goals")
            if selected_medium == "auto":
                st.write("🤖 Auto-detecting optimal marketing medium")
            else:
                st.write(f"📍 Using selected medium: {selected_medium}")
            
            try:
                # Call the ADK marketing coordinator
                result = generate_marketing_package(campaign_input, selected_medium)
                
                if result.get("success"):
                    routing_info = result.get("routing_info", {})
                    detected_medium = routing_info.get("selected_medium", selected_medium)
                    specialist_used = routing_info.get("specialist_used", "unknown")
                    
                    st.write(f"✅ Selected medium: **{detected_medium.replace('_', ' ').title()}**")
                    st.write(f"🔀 Routing to: **{specialist_used.replace('_', ' ').title()}**")
                    status.update(label="✅ Coordinator routing complete", state="complete")
                else:
                    st.error(f"❌ Coordinator failed: {result.get('error')}")
                    status.update(label="❌ Coordinator failed", state="error")
                    return
                    
            except Exception as e:
                st.error(f"❌ ADK Agent Error: {str(e)}")
                status.update(label="❌ Agent execution failed", state="error")
                return
        
        # Step 2: Specialist Agent Execution
        specialist_name = specialist_used.replace('_', ' ').title()
        with st.status(f"🤖 {specialist_name} creating campaign...", expanded=True) as status:
            st.write("📝 Generating optimized marketing content")
            st.write("🎨 Creating campaign-specific image")
            st.write("📦 Preparing downloadable package")
            
            if result.get("image_available"):
                st.write("✅ Professional marketing image generated")
            else:
                st.write("⚠️ Image generation encountered issues")
            
            status.update(label=f"✅ {specialist_name} completed", state="complete")
        
        # Step 3: Package Assembly
        with st.status("📦 Assembling marketing package...", expanded=True) as status:
            st.write("📄 Creating HTML presentation")
            st.write("📝 Preparing raw content files")
            st.write("🖼️ Embedding campaign images")
            st.write("📋 Generating README and instructions")
            
            status.update(label="✅ Package assembly complete", state="complete")
    
    # Add assistant response
    response_content = f"""✅ **Marketing Package Successfully Generated!**

**Campaign Type:** {detected_medium.replace('_', ' ').title()}
**Specialist:** {specialist_name}
**Content Preview:** {result.get('content_preview', 'Content generated successfully')}
**Image Status:** {'✅ Generated' if result.get('image_available') else '❌ Failed'}

Your marketing package is ready for download below!"""
    
    st.session_state.marketing_messages.append({
        "role": "assistant",
        "content": response_content,
        "result_data": result,
        "timestamp": datetime.now()
    })
    
    return result

# =============================================================================
# PAGE FUNCTIONS
# =============================================================================

def coordinator_page():
    """Main Coordinator Page"""
    
    st.markdown("""
    <div class="main-header">
        <h1>🏠⚡ Alberta Energy AI - Main Coordinator</h1>
        <p>Your unified interface for Energy Efficiency, Sales, Visualization, Retention & Portfolio Analysis</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if coordinator is available
    if not MAIN_COORDINATOR_AVAILABLE:
        st.error("❌ **Main Coordinator Agent Not Available**")
        st.markdown("""
        **Setup Instructions:**
        1. Ensure `main_agent/agent.py` exists with proper agent configuration
        2. Import path: `from main_agent.agent import main_coordinator, setup_main_coordinator_session, chat_with_coordinator_live_stream`
        """)
        return
    
    # Sidebar
    with st.sidebar:
        st.title("🤖 Main Coordinator")
        st.markdown("**AI Hub Status**")
        
        # Load coordinator if not done
        if not st.session_state.coordinator_initialized:
            with st.spinner("🚀 Loading AI Coordinator..."):
                agent, runner, session_service, loaded = load_coordinator_agent()
                if loaded:
                    st.session_state.coordinator_agent = agent
                    st.session_state.coordinator_runner = runner  
                    st.session_state.session_service = session_service
                    st.session_state.coordinator_initialized = True
                    st.success("✅ Coordinator Online")
                else:
                    st.error("❌ Failed to load coordinator")
        else:
            st.success("✅ Coordinator Online")
        
        st.markdown("---")
        
        # Available specialists
        st.markdown("### 🎯 Available Specialists")
        st.markdown("""
        **🔋 Energy Efficiency Agent**
        - TOU plan analysis
        - Usage patterns & insights
        - Efficiency recommendations
        
        **🧑‍💼 Sales Agent**  
        - Customer campaign generation
        - Upsell/cross-sell opportunities
        - Email & call scripts
        
        **📊 Data Visualization Agent**
        - Charts & analytics
        - Visual pattern analysis
                    
        **🧑‍🔧 Retention Agent**
        - Customer retention strategies
        - Personalized emails
        - Call scripts for at-risk customers
                    
        **📈 Portfolio Manager**
        - Portfolio analysis
        - Churn reasoning for customers
        - Cross-sell/upsell patterns
        """)
        
        st.markdown("---")
        
        # Display options
        st.markdown("### ⚙️ Display Options")
        
        show_code = st.toggle(
            "Show Generated Code",
            value=st.session_state.show_code,
            help="Show Python code for visualizations"
        )
        st.session_state.show_code = show_code
        
        st.markdown("---")
        
        # Quick examples
        st.markdown("### 💡 Quick Examples")
        examples = [
            "Analyze energy efficiency for customer CUST000042",
            "Create personalized sales campaign for customer CUST00002508",
            "Create a personalized retention email for customer CUST00001515"
            "What is the average churn rate by city?",
            "Create a plot of average churn rate by city",
            "Create a detailed report on what the main causes for churn in calgary"
        ]
        
        for example in examples:
            if st.button(f"📝 {example[:30]}...", key=f"coord_example_{example[:20]}", help=example):
                if st.session_state.coordinator_initialized:
                    process_coordinator_message(example)
                else:
                    st.error("Coordinator not initialized")
        
        st.markdown("---")
        
        # System info
        st.markdown(f"**Messages:** {len(st.session_state.coordinator_messages)}")
        st.markdown(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")
        
        # Clear chat
        if st.button("🗑️ Clear Chat", key="clear_coord_chat"):
            st.session_state.coordinator_messages = []
            st.rerun()
    
    # Main chat interface
    st.markdown("### 💬 Chat with AI Coordinator")
    
    # Display messages
    for message in st.session_state.coordinator_messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        else:
            # Check if this message contains visualization
            if "python_code" in message and message["python_code"].strip():
                # Display text response (if show_code is enabled)
                if st.session_state.show_code:
                    st.markdown(f"""
                    <div class="coordinator-message">
                        <strong>🤖 AI Coordinator:</strong> {message["content"]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="coordinator-message">
                        <strong>🤖 AI Coordinator:</strong> ✅ Analysis complete! Here's your visualization:
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display the actual visualization
                st.markdown('<div class="viz-container">', unsafe_allow_html=True)
                st.markdown("📊 **Generated Visualization:**")
                execute_python_code(message["python_code"], message["id"])
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show code if requested
                if st.session_state.show_code:
                    with st.expander("🔧 View Generated Code"):
                        st.code(message["python_code"], language="python")
            else:
                # Regular text response
                st.markdown(f"""
                <div class="coordinator-message">
                    <strong>🤖 AI Coordinator:</strong> {message["content"]}
                </div>
                """, unsafe_allow_html=True)
    
    # Input area
    st.markdown("---")
    
    # Chat input form
    with st.form("coord_chat_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_input = st.text_input(
                "Ask me anything about energy analysis, sales campaigns, or data visualization:",
                placeholder="e.g., Analyze energy efficiency for customer CUST000001",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.form_submit_button("Send 🚀", type="primary")
    
    # Process input
    if send_button and user_input.strip():
        if st.session_state.coordinator_initialized:
            process_coordinator_message(user_input.strip())
        else:
            st.error("❌ Coordinator not initialized. Please refresh the page.")

def marketing_page():
    """Marketing Agent Page"""
    
    st.markdown("""
    <div class="marketing-header">
        <h1>🎯 Google ADK Marketing Agent System</h1>
        <p>Multi-Agent Marketing Campaign Generator powered by Google Agent Development Kit</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if marketing agent is available
    if not MARKETING_AGENT_AVAILABLE:
        st.error("❌ **Google ADK Marketing Agent System Not Available**")
        st.markdown("""
        **Setup Instructions:**
        1. Save the marketing agent code as `marketing_agent/agent.py`
        2. Ensure Google Cloud Project and Vertex AI are configured
        3. Install dependencies: `pip install google-adk vertexai`
        4. Set environment variables:
           - `GOOGLE_CLOUD_PROJECT="your-project-id"`
           - `GOOGLE_CLOUD_LOCATION="us-central1"`
        """)
        return
    
    # Sidebar
    with st.sidebar:
        st.header("🤖 ADK Agent System")
        
        # Show agent architecture
        st.markdown("### Multi-Agent Architecture")
        st.markdown("""
        **🎯 Marketing Coordinator** *(Root Agent)*
        - Auto-detects optimal marketing medium
        - Routes to specialist agents
        - Creates downloadable packages
        
        **📧 Email Marketing Specialist**
        - Subject line optimization
        - Mobile-first email design
        - Conversion-focused structure
        
        **📱 Social Media Specialist**
        - Platform-specific optimization
        - Engagement-driven content
        - Strategic hashtag research
        
        **📮 Direct Mail Specialist**
        - Physical mail optimization
        - Multi-channel response methods
        - ROI tracking focus
        
        **🌐 Landing Page Specialist**
        - Conversion rate optimization
        - Mobile-first responsive design
        - A/B testing elements
        """)
        
        st.divider()
        
        # Agent status indicators
        st.markdown("### Agent Status")
        agents_status = [
            ("🎯 Coordinator", "Ready"),
            ("📧 Email Agent", "Ready"),
            ("📱 Social Agent", "Ready"), 
            ("📮 Direct Mail Agent", "Ready"),
            ("🌐 Landing Page Agent", "Ready")
        ]
        
        for agent_name, status in agents_status:
            st.markdown(f'**{agent_name}**: <span class="agent-status status-ready">{status}</span>', 
                       unsafe_allow_html=True)
        
        st.divider()
        
        # Quick campaign examples
        st.header("💡 Quick Campaign Examples")
        
        campaign_examples = [
            ("🔥 HVAC Email Campaign", 
             "Create HVAC cross-sell email for Calgary homeowners with old heating systems. Focus on energy savings and government rebates."),
            ("❄️ Winter Heating Social", 
             "Generate social media campaign for winter heating preparation. Target homeowners getting ready for cold season."),
            ("🏠 Smart Thermostat Mail", 
             "Design direct mail for smart thermostat service targeting tech-savvy homeowners. Focus on convenience and energy monitoring."),
            ("⚡ Energy Audit Landing", 
             "Build landing page for free home energy audit service. Target cost-conscious homeowners wanting to reduce bills."),
            ("🌡️ Heat Pump Promotion", 
             "Create comprehensive campaign promoting heat pump upgrades with government incentives and energy efficiency benefits.")
        ]
        
        for title, description in campaign_examples:
            if st.button(title, key=f"marketing_example_{title}", help=description):
                st.session_state.marketing_campaign_input = description
        
        st.markdown("---")
        
        # Clear marketing chat
        if st.button("🗑️ Clear Marketing Chat", key="clear_marketing_chat"):
            st.session_state.marketing_messages = []
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🚀 Generate Marketing Campaign")
        
        # Campaign input
        campaign_input = st.text_area(
            "**Campaign Requirements**",
            value=st.session_state.get("marketing_campaign_input", ""),
            height=120,
            placeholder="""Example: Create email campaign for HVAC upgrades targeting Calgary homeowners with old heating systems. Focus on:
- Energy savings and lower utility bills
- Government rebates and incentives  
- Winter comfort and reliability
- Professional installation services
- 24/7 emergency support""",
            help="Describe your marketing campaign needs in detail. Include target audience, key messages, and campaign goals."
        )
        
        # Medium selection and generation
        col_medium, col_generate = st.columns([2, 1])
        
        with col_medium:
            medium_options = {
                "auto": "🎯 Auto-Detect Best Medium",
                "email": "📧 Email Marketing",
                "social_media": "📱 Social Media",
                "direct_mail": "📮 Direct Mail", 
                "web_landing_page": "🌐 Landing Page"
            }
            
            selected_medium = st.selectbox(
                "**Marketing Medium**",
                options=list(medium_options.keys()),
                format_func=lambda x: medium_options[x],
                help="Choose specific medium or let the ADK coordinator auto-detect the optimal choice"
            )
        
        with col_generate:
            st.markdown("<br>", unsafe_allow_html=True)
            generate_button = st.button(
                "🤖 Generate Package",
                type="primary",
                help="Create complete marketing package using ADK agents",
                disabled=not campaign_input.strip()
            )
    
    with col2:
        st.header("🎯 ADK Agent Routing")
        
        if selected_medium == "auto":
            st.info("**🤖 AI Auto-Detection**\n\nThe Marketing Coordinator will analyze your requirements and automatically route to the best specialist agent.")
        else:
            medium_descriptions = {
                "email": "Routes to **Email Marketing Specialist** for high-converting email campaigns with optimized subject lines and mobile-first design.",
                "social_media": "Routes to **Social Media Specialist** for engaging, platform-optimized content with strategic hashtags.", 
                "direct_mail": "Routes to **Direct Mail Specialist** for high-response physical mail campaigns with multi-channel response methods.",
                "web_landing_page": "Routes to **Landing Page Specialist** for conversion-optimized web pages with A/B testing elements."
            }
            st.info(f"**🎯 Direct Routing**\n\n{medium_descriptions.get(selected_medium, 'Unknown medium')}")
    
    # Display marketing messages
    if st.session_state.marketing_messages:
        st.markdown("---")
        st.header("💬 Marketing Agent Conversations")
        
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
                
                # Show download section if result data exists
                if "result_data" in message:
                    result = message["result_data"]
                    
                    # Success metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    package_info = result.get("package_info", {})
                    routing_info = result.get("routing_info", {})
                    detected_medium = routing_info.get("selected_medium", "social_media")
                    specialist_name = routing_info.get("specialist_used", "unknown").replace('_', ' ').title()
                    
                    with col1:
                        st.metric(
                            "📋 Campaign Type", 
                            package_info.get("medium", detected_medium.replace('_', ' ').title())
                        )
                    
                    with col2:
                        st.metric(
                            "🤖 ADK Agent", 
                            specialist_name
                        )
                    
                    with col3:
                        st.metric(
                            "📅 Generated", 
                            package_info.get("created_at", datetime.now().strftime("%Y-%m-%d %H:%M"))[:16]
                        )
                    
                    with col4:
                        st.metric(
                            "🖼️ Image Status", 
                            "✅ Included" if result.get("image_available") else "❌ Failed"
                        )
                    
                    # Content preview
                    if result.get("content_preview"):
                        with st.expander("👀 Campaign Content Preview", expanded=False):
                            st.markdown("**Generated by ADK Agent System:**")
                            st.text(result["content_preview"])
                    
                    # Download section
                    st.markdown("### 📥 Download Your Marketing Package")
                    
                    # Create download button
                    try:
                        if "zip_data" in result and result["zip_data"]:
                            zip_data = base64.b64decode(result["zip_data"])
                            filename = result.get("filename", f"adk_marketing_package_{detected_medium}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.download_button(
                                    label="📦 Download Complete ADK Marketing Package",
                                    data=zip_data,
                                    file_name=filename,
                                    mime="application/zip",
                                    help="Generated by Google ADK Marketing Agent System",
                                    key=f"download_{message['timestamp'].strftime('%Y%m%d_%H%M%S')}"
                                )
                            
                            with col2:
                                package_size_kb = len(zip_data) // 1024
                                st.info(f"**Package Size:** {package_size_kb} KB")
                        else:
                            st.error("❌ ZIP package data not available")
                    
                    except Exception as e:
                        st.error(f"❌ Download preparation failed: {str(e)}")
    
    # Generate marketing package using ADK agents
    if generate_button and campaign_input.strip():
        result = process_marketing_message(campaign_input, selected_medium)
        st.rerun()

# =============================================================================
# MAIN APP WITH NAVIGATION
# =============================================================================

def main():
    """Main application with navigation"""
    
    # Create navigation
    pages = {
        "🏠 Main Coordinator": coordinator_page,
        "🎯 Marketing Agent": marketing_page
    }
    
    # Streamlit navigation
    selection = st.sidebar.radio(
        "🚀 **Navigate to Agent System:**",
        options=list(pages.keys()),
        index=0,
        help="Switch between different agent systems"
    )
    
    # Add navigation info
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    ### 🤖 About This System
    
    **Main Coordinator**: 
    Unified hub for Energy, Sales, Visualization, Retention & Portfolio agents
    
    **Marketing Agent**: 
    Separate Google ADK multi-agent system for professional marketing campaigns
    
    Each system operates independently with its own specialized agents and capabilities.
    """)
    
    # Run selected page
    pages[selection]()

if __name__ == "__main__":
    main()