"""
Updated Streamlit Interface for Google ADK Marketing Agent System
Works with the multi-agent marketing system built using Google ADK
"""

import streamlit as st
import base64
import json
from datetime import datetime
from typing import Dict, Any

# Import the Google ADK marketing agent system
try:
    # Import from the provided agent code (marketing_agent.agent module)
    from marketing_agent.agent import (
        generate_marketing_package,
        marketing_coordinator_tool,
        root_agent
    )
    ADK_AGENT_AVAILABLE = True
except ImportError:
    try:
        # Alternative import if using different structure
        from marketing_agent.agent import (
            generate_marketing_package,
            marketing_coordinator_tool,
            root_agent
        )
        ADK_AGENT_AVAILABLE = True
    except ImportError:
        st.error("❌ Google ADK Marketing Agent System not found")
        ADK_AGENT_AVAILABLE = False

# Import for proper error handling
import traceback

def main():
    """Main Streamlit interface for Google ADK Marketing Agents"""
    
    st.set_page_config(
        page_title="🤖 ADK Marketing Agent System",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS for Google-style design
    st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #4285F4 0%, #34A853 25%, #FBBC05 50%, #EA4335 75%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
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
    </style>
    """, unsafe_allow_html=True)
    
    # Main header
    st.markdown('<h1 class="main-header">🤖 Google ADK Marketing Agent System</h1>', unsafe_allow_html=True)
    st.markdown("**Multi-Agent Marketing Campaign Generator powered by Google Agent Development Kit**")
    
    if not ADK_AGENT_AVAILABLE:
        st.error("❌ **Google ADK Marketing Agent System Not Available**")
        st.markdown("""
        **Setup Instructions:**
        1. Save the provided agent code as `marketing_agent/agent.py`
        2. Ensure Google Cloud Project and Vertex AI are configured
        3. Install dependencies: `pip install google-adk vertexai streamlit`
        4. Set environment variables:
           - `GOOGLE_CLOUD_PROJECT="your-project-id"`
           - `GOOGLE_CLOUD_LOCATION="us-central1"`
        """)
        st.stop()
    
    # Agent System Status in Sidebar
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
            if st.button(title, key=f"example_{title}", help=description):
                st.session_state.campaign_input = description
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("🚀 Generate Marketing Campaign")
        
        # Campaign input
        campaign_input = st.text_area(
            "**Campaign Requirements**",
            value=st.session_state.get("campaign_input", ""),
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
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
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
    
    # Generate marketing package using ADK agents
    if generate_button and campaign_input.strip():
        
        # Show agent workflow
        st.markdown("---")
        st.header("🤖 ADK Agent Workflow")
        
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
                        st.stop()
                        
                except Exception as e:
                    st.error(f"❌ ADK Agent Error: {str(e)}")
                    status.update(label="❌ Agent execution failed", state="error")
                    st.stop()
            
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
        
        # Display Results
        st.markdown("---")
        st.header("🎉 Campaign Generation Complete!")
        
        # Success metrics
        col1, col2, col3, col4 = st.columns(4)
        
        package_info = result.get("package_info", {})
        
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
            with st.expander("👀 Campaign Content Preview", expanded=True):
                st.markdown("**Generated by ADK Agent System:**")
                st.text(result["content_preview"])
        
        # Download section
        st.markdown("### 📥 Download Your Marketing Package")
        
        # Create download button with better error handling
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
                        help="Generated by Google ADK Marketing Agent System"
                    )
                
                with col2:
                    package_size_kb = len(zip_data) // 1024
                    st.info(f"**Package Size:** {package_size_kb} KB")
                    
                    # Debug info
                    if result.get("zip_size"):
                        st.caption(f"Original size: {result['zip_size']} bytes")
            else:
                st.error("❌ ZIP package data not available")
                if "error" in result:
                    st.error(f"Error details: {result['error']}")
        
        except Exception as e:
            st.error(f"❌ Download preparation failed: {str(e)}")
            # Show debug info
            with st.expander("🔧 Debug Information"):
                st.write("Result keys:", list(result.keys()) if result else "No result")
                if result.get("zip_data"):
                    st.write("ZIP data length:", len(result["zip_data"]))
                st.write("Full error:", traceback.format_exc())
        
        # Package contents
        contents = package_info.get("contents", [])
        if contents:
            st.markdown("**📋 Package Contents:**")
            for item in contents:
                if item:  # Skip None items
                    if "html" in item:
                        st.write(f"• 📄 **{item}** - Professional presentation with embedded image")
                    elif "txt" in item:
                        st.write(f"• 📝 **{item}** - Raw content for copy-paste implementation")
                    elif "png" in item:
                        st.write(f"• 🖼️ **{item}** - AI-generated campaign image")
                    else:
                        st.write(f"• 📋 **{item}** - Instructions and documentation")
        
        # Usage guide
        with st.expander("📖 How to Use Your ADK-Generated Package", expanded=False):
            st.markdown(f"""
            ### Implementation Guide for {detected_medium.replace('_', ' ').title()} Campaign
            
            **1. Download & Extract**
            - Click the download button above to get your complete package
            - Extract the ZIP file to access all marketing materials
            - Review the HTML presentation for a complete overview
            
            **2. Campaign Implementation**
            - **Content**: Copy from the text file for your marketing platform
            - **Images**: Use the PNG file in your marketing materials
            - **Structure**: Follow the format provided by the {specialist_name}
            
            **3. Platform-Specific Deployment**
            """)
            
            if detected_medium == "email":
                st.markdown("""
                - Import content into your email marketing platform (Mailchimp, Constant Contact, etc.)
                - Use the PNG image as an email header or inline image
                - Test across different email clients for compatibility
                - Set up tracking for open rates and click-through rates
                """)
            elif detected_medium == "social_media":
                st.markdown("""
                - Upload the PNG image to your social media platforms
                - Copy the post content and adapt hashtags for each platform
                - Schedule posts for optimal engagement times
                - Monitor engagement metrics and respond to comments
                """)
            elif detected_medium == "direct_mail":
                st.markdown("""
                - Work with your print designer to incorporate the content and image
                - Ensure image is high-resolution for print quality
                - Test different response mechanisms (QR codes, phone, website)
                - Track response rates by postal code or demographic
                """)
            elif detected_medium == "web_landing_page":
                st.markdown("""
                - Provide content to your web developer or use in page builders
                - Use the PNG image as a hero banner or supporting visual
                - Implement conversion tracking and A/B testing
                - Optimize page load speed and mobile responsiveness
                """)
            
            st.markdown("""
            **4. Performance Optimization**
            - Customize content to match your brand voice and visual identity
            - Add your company contact information and legal disclaimers
            - Set up analytics to track campaign performance
            - Prepare follow-up campaigns based on initial results
            
            **5. ADK Agent System Benefits**
            - Content optimized by specialized marketing agents
            - Images generated specifically for your campaign context
            - Professional formatting ready for immediate use
            - Consistent quality across all marketing mediums
            """)
        
        # Success message
        st.success(f"""
        ✅ **Marketing Package Successfully Generated!**
        
        Your {detected_medium.replace('_', ' ').title()} campaign has been created by the **{specialist_name}** 
        using Google's Agent Development Kit. The package includes professional content, 
        custom images, and implementation guidance.
        """)

def show_adk_info():
    """Display information about Google ADK"""
    st.markdown("""
    ### About Google Agent Development Kit (ADK)
    
    **Google ADK** is an open-source, code-first framework for building sophisticated AI agent systems. 
    This marketing application demonstrates ADK's multi-agent orchestration capabilities:
    
    **🏗️ Multi-Agent Architecture**
    - **Coordinator Agent**: Routes requests to specialist agents
    - **Specialist Agents**: Domain experts for each marketing medium
    - **Tool Integration**: Custom functions for content generation and image creation
    
    **🔧 ADK Features Used**
    - Model-agnostic design (works with Gemini, GPT-4, Claude, etc.)
    - Hierarchical agent delegation and coordination
    - Structured tool calling and response handling
    - State management and context sharing
    
    **🚀 Production Ready**
    - Built-in evaluation and testing frameworks
    - Containerized deployment options
    - Integration with Google Cloud and Vertex AI
    - Agent-to-Agent (A2A) protocol support
    
    Learn more: [Google ADK Documentation](https://google.github.io/adk-docs/)
    """)

if __name__ == "__main__":
    main()
    
    # Show ADK info in sidebar
    with st.sidebar:
        st.divider()
        with st.expander("ℹ️ About Google ADK"):
            show_adk_info()