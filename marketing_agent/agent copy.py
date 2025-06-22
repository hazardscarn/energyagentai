"""
Marketing Agent - Root agent that creates marketing content, generates images, and manages downloads
File: marketing_agent/agent.py
COMPLETE UPDATED FILE
"""

import os
import json
from datetime import datetime
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from vertexai.preview.reasoning_engines import AdkApp

# Import image generation tool from shared_tools
from shared_tools.image_gen import generate_marketing_image_tool

# Import marketing content tools (relative import since we're in marketing_agent folder)
from .marketing_content_tools import (
    generate_marketing_copy_tool,
    save_marketing_content_tool,
    create_download_package_tool,
    register_session_image_tool,
    list_session_content_tool
)

# Import config (relative import)
from .config import MarketingConfig

# Initialize configuration
config = MarketingConfig()

def create_root_marketing_agent():
    """Create comprehensive root marketing agent with all capabilities"""
    
    marketing_agent = Agent(
        name="root_marketing_agent",
        model=config.default_model,
        instruction="""
        You are a comprehensive Marketing Content Manager - a professional marketing assistant that helps create complete marketing campaigns.
        
        YOUR CAPABILITIES:
        🎨 Content Creation:
        - Generate marketing copy for emails, ads, social media, landing pages
        - Create professional marketing images optimized for different channels
        - Customize tone, length, and style based on campaign needs
        
        💾 Content Management:
        - Save all generated content to organized files
        - Track content across user sessions
        - Create downloadable packages with all materials
        
        📄 Document Creation:
        - Package all content into professional Word documents
        - Embed images directly into the documents
        - Provide clickable download links through the web interface
        - Generate ready-to-use marketing materials
        
        WORKFLOW FOR MARKETING REQUESTS:
        1. UNDERSTAND: Ask clarifying questions about the campaign
        2. CREATE: Generate marketing copy and/or images
        3. SAVE: Save content to files for the user session
        4. PACKAGE: Create Word documents with embedded images when requested
        5. DELIVER: Provide clickable download links for professional documents
        
        TOOLS AVAILABLE:
        - generate_marketing_copy_tool: Create marketing copy for any campaign type
        - generate_marketing_image_tool: Generate professional marketing images
        - save_marketing_content_tool: Save content to organized files
        - register_session_image_tool: Track images in user session
        - list_session_content_tool: Show all content created in session
        - create_download_package_tool: Create downloadable Word documents with embedded images
        
        BEST PRACTICES:
        - Always ask about campaign goals, target audience, and brand guidelines
        - Generate both copy and images when appropriate
        - Save content immediately after generation
        - Register images with the session for document packaging
        - Offer to create Word documents after generating multiple items
        - Provide clickable download links for professional documents
        
        SESSION MANAGEMENT:
        - Track all content created in each user session
        - Organize files by type (content vs images)
        - Create professional Word documents with embedded images
        - Maintain professional file naming conventions
        
        Be proactive in suggesting complementary content (if they ask for copy, suggest matching images, etc.)
        Always end by offering to create a Word document or generate additional materials.
        """,
        description="Comprehensive marketing agent that creates copy, generates images, manages files, and provides Word documents",
        tools=[
            generate_marketing_copy_tool,
            generate_marketing_image_tool,
            save_marketing_content_tool,
            register_session_image_tool,
            list_session_content_tool,
            create_download_package_tool
        ]
    )
    
    return marketing_agent

# Create the root agent - THIS IS WHAT ADK LOOKS FOR
root_agent = create_root_marketing_agent()

def create_marketing_app():
    """Create and configure the Marketing Manager ADK application"""
    app = AdkApp(agent=root_agent)
    return app

def test_comprehensive_agent():
    """Test the comprehensive marketing agent"""
    
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("⚠️  GOOGLE_CLOUD_PROJECT not found. Please set up environment variables.")
        return
    
    # Create runner
    runner = Runner(
        agent=root_agent,
        session_service=InMemorySessionService()
    )
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "Email Campaign Creation",
            "message": """Create a complete email marketing campaign for our new fitness app launch. 
            Target audience: Health-conscious millennials. 
            Key message: Transform your fitness routine with AI-powered workouts.
            I need both copy and images."""
        },
        {
            "name": "Social Media Campaign", 
            "message": """Generate social media content for our Black Friday sale. 
            Product: Smart home devices.
            Audience: Tech-savvy homeowners.
            Tone: Urgent but friendly.
            Need multiple images for different platforms."""
        },
        {
            "name": "Product Launch Package",
            "message": """Create marketing materials for launching our new eco-friendly water bottles.
            Target: Environmentally conscious consumers.
            Include professional product images and compelling copy for ads."""
        }
    ]
    
    print("=== Testing Comprehensive Marketing Agent ===\n")
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"Test {i}: {scenario['name']}")
        print(f"Request: {scenario['message'][:100]}...")
        
        try:
            result = runner.run(
                user_id="test_marketer",
                session_id=f"test_session_{i}",
                message=scenario['message']
            )
            print(f"✅ Success - Response length: {len(result.text)} characters")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 60)

def run_interactive_marketing_agent():
    """Run the marketing agent interactively"""
    
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("⚠️  Please set up environment variables first.")
        print("Required: GOOGLE_CLOUD_PROJECT")
        print("Ensure Vertex AI authentication is configured (gcloud auth or service account)")
        return
    
    # Create runner
    runner = Runner(
        agent=root_agent,
        session_service=InMemorySessionService()
    )
    
    print("🚀 Marketing Content Manager Ready!")
    print("I can help you create comprehensive marketing campaigns with copy and images.")
    print("\nExample requests:")
    print("  • 'Create an email campaign for our product launch'")
    print("  • 'Generate social media content for our sale'") 
    print("  • 'Make marketing materials for our new service'")
    print("  • 'Show me what content I've created'")
    print("  • 'Create a Word document with all my content'")
    print("\nType 'quit' to exit.\n")
    
    session_id = f"marketing_session_{int(datetime.now().timestamp())}"
    user_id = "marketer"
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                # Offer download package before exiting
                print("\n📄 Before you go, would you like me to create a Word document with all your content?")
                download_choice = input("Create Word document? (y/n): ").strip().lower()
                
                if download_choice in ['y', 'yes']:
                    result = runner.run(
                        user_id=user_id,
                        session_id=session_id,
                        message="Create a Word document with all the content I've generated"
                    )
                    print(f"\nAgent: {result.text}")
                
                print("\n👋 Thanks for using Marketing Content Manager!")
                break
            
            if not user_input:
                continue
            
            # Get agent response
            result = runner.run(
                user_id=user_id,
                session_id=session_id,
                message=user_input
            )
            
            print(f"\nAgent: {result.text}\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

def setup_environment():
    """Display setup instructions"""
    print("=== Marketing Content Manager Setup ===")
    print()
    print("1. Required Environment Variables:")
    print("   export GOOGLE_CLOUD_PROJECT='energyagentai'")
    print("   export GOOGLE_CLOUD_LOCATION='us-central1'")
    print()
    print("2. Required Authentication (choose one):")
    print("   # For development:")
    print("   gcloud auth application-default login")
    print("   gcloud config set project energyagentai")
    print()
    print("   # For production:")
    print("   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account.json'")
    print()
    print("3. Required Dependencies:")
    print("   pip install google-adk google-cloud-aiplatform vertexai pillow python-docx")
    print()
    print("4. Directory Structure Created:")
    print("   marketing_outputs/")
    print("   ├── session_id/")
    print("   │   ├── content/          # Marketing copy files")
    print("   │   └── images/           # Generated images")
    print("   └── downloads/            # Word documents")
    print()
    print("5. File Organization:")
    print("   • All content saved automatically")
    print("   • Images registered with sessions")
    print("   • Word documents include embedded images")
    print("   • Professional document formatting")
    print()

# For ADK Web UI and CLI
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "setup":
            setup_environment()
        elif sys.argv[1] == "test":
            test_comprehensive_agent()
        elif sys.argv[1] == "interactive":
            run_interactive_marketing_agent()
        elif sys.argv[1] == "app":
            app = create_marketing_app()
            print("Marketing ADK App created - ready for deployment")
        else:
            print("Usage: python agent.py [setup|test|interactive|app]")
    else:
        # Default: run interactive mode
        run_interactive_marketing_agent()