"""
Improved Multi-Agent Marketing System
Generates final, polished, ready-to-use marketing content (no multiple options)
"""

import json
import base64
from typing import Optional, Dict, Any
from google.adk.agents import Agent
from vertexai.generative_models import GenerativeModel
import vertexai
import os

# Initialize Vertex AI
project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)

# ========================================
# VISUAL ELEMENTS EXTRACTION
# ========================================

def _extract_visual_elements(campaign_instructions: str) -> str:
    """Extract what should be visually shown in the image based on campaign instructions"""
    
    instructions_lower = campaign_instructions.lower()
    
    # HVAC and Heating
    if any(term in instructions_lower for term in ['hvac', 'heating', 'furnace', 'heat pump', 'air conditioning', 'ac unit']):
        return """
        - Modern HVAC equipment (sleek furnace, heat pump, or AC unit)
        - Comfortable family in a warm, cozy home interior
        - Professional HVAC technician installing or servicing equipment
        - Cross-section view of efficient heating system in a home
        - Before/after comparison: old vs new heating system
        - Warm, comfortable living room with perfect temperature
        """
    
    # Energy and Efficiency
    elif any(term in instructions_lower for term in ['energy', 'efficiency', 'solar', 'insulation', 'audit']):
        return """
        - Home with solar panels on roof
        - Energy meter showing low usage/savings
        - Well-insulated, efficient home exterior
        - Professional energy auditor with equipment
        - Green, eco-friendly home with energy-saving features
        - Family enjoying lower utility bills in comfortable home
        """
    
    # Smart Home Technology
    elif any(term in instructions_lower for term in ['smart', 'thermostat', 'automation', 'control']):
        return """
        - Modern smart thermostat on wall being controlled by smartphone
        - Family using smart home app to control temperature
        - Sleek, modern smart home devices and interfaces
        - Professional installation of smart home technology
        - Home with integrated smart systems and modern technology
        """
    
    # Plumbing
    elif any(term in instructions_lower for term in ['plumbing', 'water', 'pipes', 'leak', 'drain']):
        return """
        - Professional plumber working on modern plumbing fixtures
        - Beautiful, modern bathroom or kitchen with new fixtures
        - Clean, efficient water systems and pipes
        - Family enjoying reliable water service in their home
        - High-quality plumbing fixtures and installations
        """
    
    # Home Improvement General
    elif any(term in instructions_lower for term in ['home', 'house', 'property', 'renovation', 'upgrade']):
        return """
        - Beautiful, well-maintained home exterior
        - Happy family in front of their improved home
        - Professional contractors working on home improvements
        - Before/after home improvement transformation
        - Modern, updated home interior with quality improvements
        """
    
    # Business Services
    elif any(term in instructions_lower for term in ['business', 'commercial', 'office', 'service']):
        return """
        - Professional service team in action
        - Modern office or commercial building
        - Business owner satisfied with professional service
        - Clean, professional commercial environment
        - Team of experts providing quality business solutions
        """
    
    # Real Estate
    elif any(term in instructions_lower for term in ['real estate', 'property', 'buying', 'selling', 'mortgage']):
        return """
        - Beautiful home for sale with "sold" sign
        - Happy family moving into new home
        - Professional realtor showing property to clients
        - Stunning home exterior in desirable neighborhood
        - Family celebrating successful home purchase
        """
    
    # Technology/Software
    elif any(term in instructions_lower for term in ['software', 'app', 'digital', 'technology', 'online']):
        return """
        - Person successfully using software/app on modern device
        - Clean, modern office environment with technology
        - Professional team working with advanced technology
        - User interface showing successful results/productivity
        - Modern workplace with efficient digital solutions
        """
    
    # Health/Wellness
    elif any(term in instructions_lower for term in ['health', 'wellness', 'fitness', 'medical', 'care']):
        return """
        - Healthy, active people enjoying wellness benefits
        - Modern medical or fitness facility
        - Professional healthcare or wellness providers
        - People achieving health and wellness goals
        - Clean, modern healthcare or fitness environment
        """
    
    # Default for any other service/product
    else:
        return """
        - Professional service provider delivering quality results
        - Satisfied customers enjoying the benefits of the service/product
        - Clean, modern, professional work environment
        - High-quality product or service in use
        - Happy customer experiencing positive outcomes
        - Professional team providing expert service
        """

# ========================================
# IMPROVED SPECIALIST TOOLS - FINAL CONTENT
# ========================================

def email_marketing_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Email marketing specialist - generates ONE final, polished email"""
    
    try:
        email_prompt = f"""
        You are an EMAIL MARKETING SPECIALIST creating ONE final, polished, ready-to-use email campaign.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a SINGLE, complete email campaign that is immediately ready for deployment. 
        No multiple options, no A/B testing suggestions - just one perfect email.
        
        STRUCTURE YOUR RESPONSE EXACTLY LIKE THIS:

        SUBJECT LINE:
        [Write one compelling subject line under 50 characters]

        PREVIEW TEXT:
        [Write preview text that extends the subject line]

        EMAIL CONTENT:
        [Write the complete email body with:
        - Engaging opening that hooks the reader
        - Clear problem identification
        - Strong solution presentation  
        - 3-4 key benefits with specifics
        - One customer testimonial or social proof
        - Clear call-to-action
        - Professional closing]

        CALL TO ACTION:
        [Write the exact CTA button text and action]

        Requirements:
        - Mobile-first formatting (short paragraphs)
        - Professional but conversational tone
        - Specific benefits with numbers/percentages where possible
        - Ready to copy-paste into any email platform
        - No placeholder text - everything should be final
        """
        
        model = GenerativeModel("gemini-2.5-pro-preview-05-06")
        content_response = model.generate_content(email_prompt)
        email_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "email_marketing",
            "content": email_content,
            "structured_output": _parse_email_content(email_content)
        }
        
        if include_image:
            image_result = _generate_email_image(campaign_instructions)
            if image_result["success"]:
                result["image"] = image_result
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "agent_type": "email_marketing"}, indent=2)

def social_media_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Social media specialist - generates ONE final, polished social campaign"""
    
    try:
        social_prompt = f"""
        You are a SOCIAL MEDIA MARKETING SPECIALIST creating ONE final, polished social media campaign.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a SINGLE, complete social media campaign that is immediately ready for posting.
        No multiple options - just one perfect social media campaign.
        
        STRUCTURE YOUR RESPONSE EXACTLY LIKE THIS:

        MAIN POST:
        [Write one engaging social media post under 150 words that includes:
        - Hook that stops scrolling
        - Key value proposition
        - Call for engagement
        - Clear call-to-action]

        HASHTAGS:
        [List 8-10 relevant hashtags for maximum reach]

        PLATFORM NOTES:
        [Brief notes on how to adapt for Facebook, Instagram, LinkedIn]

        ENGAGEMENT STRATEGY:
        [One specific way to encourage comments/interaction]

        Requirements:
        - Conversational, authentic tone
        - Shareable and engaging
        - Ready to post immediately
        - Include emojis where appropriate
        - No placeholder text - everything should be final
        """
        
        model = GenerativeModel("gemini-2.5-pro-preview-05-06")
        content_response = model.generate_content(social_prompt)
        social_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "social_media",
            "content": social_content,
            "structured_output": _parse_social_content(social_content)
        }
        
        if include_image:
            image_result = _generate_social_image(campaign_instructions)
            if image_result["success"]:
                result["image"] = image_result
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "agent_type": "social_media"}, indent=2)

def direct_mail_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Direct mail specialist - generates ONE final, polished direct mail piece"""
    
    try:
        direct_mail_prompt = f"""
        You are a DIRECT MAIL MARKETING SPECIALIST creating ONE final, polished direct mail piece.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a SINGLE, complete direct mail campaign that is immediately ready for printing and mailing.
        No multiple options - just one perfect direct mail piece.
        
        STRUCTURE YOUR RESPONSE EXACTLY LIKE THIS:

        MAIN HEADLINE:
        [Write one large, benefit-driven headline]

        SUB-HEADLINE:
        [Write supporting message that builds on main headline]

        BODY CONTENT:
        [Write scannable content with:
        - Problem statement that resonates
        - Clear solution overview
        - 4-5 specific benefits with details
        - Trust indicators/credentials
        - Urgency element]

        RESPONSE METHODS:
        [List specific ways to respond:
        - Phone number
        - Website URL
        - QR code suggestion
        - Mail-back option]

        DESIGN NOTES:
        [Brief layout suggestions for print design]

        Requirements:
        - Scannable hierarchy for physical mail
        - Direct, benefit-focused language
        - Ready for print production
        - No placeholder text - everything should be final
        """
        
        model = GenerativeModel("gemini-2.5-pro-preview-05-06")
        content_response = model.generate_content(direct_mail_prompt)
        direct_mail_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "direct_mail",
            "content": direct_mail_content,
            "structured_output": _parse_direct_mail_content(direct_mail_content)
        }
        
        if include_image:
            image_result = _generate_direct_mail_image(campaign_instructions)
            if image_result["success"]:
                result["image"] = image_result
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "agent_type": "direct_mail"}, indent=2)

def web_landing_page_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Landing page specialist - generates ONE final, polished landing page"""
    
    try:
        landing_page_prompt = f"""
        You are a WEB LANDING PAGE SPECIALIST creating ONE final, polished landing page.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a SINGLE, complete landing page structure that is immediately ready for development.
        No multiple options - just one perfect landing page.
        
        STRUCTURE YOUR RESPONSE EXACTLY LIKE THIS:

        HERO SECTION:
        Hero Headline: [Main value proposition]
        Sub-headline: [Supporting details]
        Primary CTA Button: [Button text]

        BENEFITS SECTION:
        [List 3-4 key benefits with supporting details]

        SOCIAL PROOF SECTION:
        [Customer testimonial and trust indicators]

        FEATURES SECTION:
        [Detailed offering description with feature highlights]

        CONVERSION SECTION:
        Lead Capture Form Fields: [Specific form fields needed]
        Final CTA: [Conversion-focused call-to-action]
        Urgency Element: [Time-sensitive motivation]

        TECHNICAL NOTES:
        [Mobile optimization and loading speed considerations]

        Requirements:
        - Conversion-focused structure
        - Trust-building elements throughout
        - Ready for web development
        - No placeholder text - everything should be final
        """
        
        model = GenerativeModel("gemini-2.5-pro-preview-05-06")
        content_response = model.generate_content(landing_page_prompt)
        landing_page_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "web_landing_page",
            "content": landing_page_content,
            "structured_output": _parse_landing_page_content(landing_page_content)
        }
        
        if include_image:
            image_result = _generate_landing_page_image(campaign_instructions)
            if image_result["success"]:
                result["image"] = image_result
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"success": False, "error": str(e), "agent_type": "web_landing_page"}, indent=2)

# ========================================
# CONTENT PARSING FUNCTIONS (SAME AS BEFORE)
# ========================================

def _parse_email_content(content: str) -> Dict:
    """Parse email content into structured sections"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    email_indicators = ['subject line:', 'preview text:', 'email content:', 'call to action:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in email_indicators)
        
        if is_section:
            if current_text:
                sections[current_section] = '\n'.join(current_text)
            current_section = line_lower.replace(':', '').strip().replace(' ', '_')
            current_text = []
        else:
            current_text.append(line_clean)
    
    if current_text:
        sections[current_section] = '\n'.join(current_text)
    
    sections["full_content"] = content
    return sections

def _parse_social_content(content: str) -> Dict:
    """Parse social media content into structured sections"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    social_indicators = ['main post:', 'hashtags:', 'platform notes:', 'engagement strategy:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in social_indicators)
        
        if is_section:
            if current_text:
                sections[current_section] = '\n'.join(current_text)
            current_section = line_lower.replace(':', '').strip().replace(' ', '_')
            current_text = []
        else:
            current_text.append(line_clean)
    
    if current_text:
        sections[current_section] = '\n'.join(current_text)
    
    sections["full_content"] = content
    return sections

def _parse_direct_mail_content(content: str) -> Dict:
    """Parse direct mail content into structured sections"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    mail_indicators = ['main headline:', 'sub-headline:', 'body content:', 'response methods:', 'design notes:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in mail_indicators)
        
        if is_section:
            if current_text:
                sections[current_section] = '\n'.join(current_text)
            current_section = line_lower.replace(':', '').strip().replace(' ', '_')
            current_text = []
        else:
            current_text.append(line_clean)
    
    if current_text:
        sections[current_section] = '\n'.join(current_text)
    
    sections["full_content"] = content
    return sections

def _parse_landing_page_content(content: str) -> Dict:
    """Parse landing page content into structured sections"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    landing_indicators = ['hero section:', 'benefits section:', 'social proof:', 'features section:', 'conversion section:', 'technical notes:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in landing_indicators)
        
        if is_section:
            if current_text:
                sections[current_section] = '\n'.join(current_text)
            current_section = line_lower.replace(':', '').strip().replace(' ', '_')
            current_text = []
        else:
            current_text.append(line_clean)
    
    if current_text:
        sections[current_section] = '\n'.join(current_text)
    
    sections["full_content"] = content
    return sections

# ========================================
# IMAGE GENERATION (SAME AS BEFORE)
# ========================================

def _generate_email_image(campaign_instructions: str) -> Dict:
    """Generate email-optimized image"""
    
    # Extract the actual product/service being marketed
    visual_elements = _extract_visual_elements(campaign_instructions)
    
    image_prompt = f"""
    Create a professional, photorealistic image for email marketing.
    
    VISUAL CONTENT TO SHOW:
    {visual_elements}
    
    EMAIL IMAGE REQUIREMENTS:
    - Professional product photography or lifestyle photography style
    - Clean, modern composition suitable for email headers
    - Bright, appealing colors that work in email clients
    - Focus on the actual product, service, or benefit being offered
    - Show real-world usage or results
    - High-quality, commercial-grade appearance
    - ABSOLUTELY NO TEXT, words, letters, or typography anywhere in the image
    - Create visual storytelling through imagery alone
    
    Style: Professional commercial photography, clean background, excellent lighting.
    Focus: Show the actual thing being marketed, not abstract concepts.
    """
    
    return _generate_image_base64(image_prompt, "email marketing")

def _generate_social_image(campaign_instructions: str) -> Dict:
    """Generate social media optimized image"""
    
    visual_elements = _extract_visual_elements(campaign_instructions)
    
    image_prompt = f"""
    Create a vibrant, engaging image for social media marketing.
    
    VISUAL CONTENT TO SHOW:
    {visual_elements}
    
    SOCIAL MEDIA IMAGE REQUIREMENTS:
    - Lifestyle photography showing real people using/benefiting from the product
    - Bright, eye-catching colors that perform well on social feeds
    - Dynamic composition that stops scrolling
    - Show the actual product in use or the results/benefits
    - Professional but approachable feel
    - ABSOLUTELY NO TEXT, words, letters, or typography anywhere in the image
    - Focus on visual storytelling and emotional connection
    
    Style: Lifestyle photography, vibrant colors, human connection, real-world scenarios.
    Focus: Show people enjoying the benefits of what's being marketed.
    """
    
    return _generate_image_base64(image_prompt, "social media marketing")

def _generate_direct_mail_image(campaign_instructions: str) -> Dict:
    """Generate direct mail optimized image"""
    
    visual_elements = _extract_visual_elements(campaign_instructions)
    
    image_prompt = f"""
    Create a high-impact image for direct mail marketing.
    
    VISUAL CONTENT TO SHOW:
    {visual_elements}
    
    DIRECT MAIL IMAGE REQUIREMENTS:
    - Professional product photography with dramatic lighting
    - High contrast and visual impact for print materials
    - Show the actual product, installation, or end result
    - Trust-building imagery (professional technicians, quality equipment)
    - Print-ready quality and resolution
    - ABSOLUTELY NO TEXT, words, letters, or typography anywhere in the image
    - Focus on credibility and quality craftsmanship
    
    Style: Professional commercial photography, dramatic lighting, premium quality feel.
    Focus: Show the professionalism and quality of the service/product.
    """
    
    return _generate_image_base64(image_prompt, "direct mail marketing")

def _generate_landing_page_image(campaign_instructions: str) -> Dict:
    """Generate landing page optimized image"""
    
    visual_elements = _extract_visual_elements(campaign_instructions)
    
    image_prompt = f"""
    Create a conversion-focused hero image for a landing page.
    
    VISUAL CONTENT TO SHOW:
    {visual_elements}
    
    LANDING PAGE IMAGE REQUIREMENTS:
    - Professional hero image showing the end result or benefit
    - Clean, modern composition that builds trust and credibility
    - Show satisfied customers or beautiful end results
    - Wide format suitable for website headers
    - Conversion-optimized visual that supports the value proposition
    - ABSOLUTELY NO TEXT, words, letters, or typography anywhere in the image
    - Focus on the transformation or benefit the customer receives
    
    Style: Professional hero photography, clean backgrounds, aspirational results.
    Focus: Show the ideal outcome the customer wants to achieve.
    """
    
    return _generate_image_base64(image_prompt, "landing page marketing")

def _generate_image_base64(image_prompt: str, image_type: str) -> Dict:
    """Generate image and return as base64"""
    try:
        model = GenerativeModel("gemini-2.0-flash-exp")
        
        # Enhanced prompt with strong anti-text instructions
        enhanced_prompt = f"""
        {image_prompt}
        
        CRITICAL REQUIREMENTS:
        - This is a VISUAL-ONLY image - NO TEXT, NO WORDS, NO LETTERS of any kind
        - Do not include any company names, product names, or written information
        - Focus purely on visual storytelling through photography
        - Create photorealistic imagery that shows the actual subject matter
        - Use professional photography techniques and composition
        - Generate compelling visual content that communicates through imagery alone
        
        AVOID AT ALL COSTS:
        - Any text, typography, or written words
        - Brand names or company information
        - Signs, labels, or written content
        - Abstract representations - show real, tangible things
        
        CREATE: Professional, photorealistic imagery that visually represents the marketing concept.
        """
        
        response = model.generate_content(
            enhanced_prompt,
            generation_config={
                "response_modalities": ["TEXT", "IMAGE"],
                "max_output_tokens": 8192,
                "temperature": 0.3,  # Lower temperature for more consistent results
            }
        )
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, "inline_data") and part.inline_data is not None:
                image_data = part.inline_data.data
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                return {
                    "success": True,
                    "image_base64": image_base64,
                    "format": "PNG",
                    "description": f"Professional {image_type} image",
                    "image_type": image_type
                }
        
        return {"success": False, "error": "No image generated"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========================================
# MAIN COORDINATOR (SAME ROUTING LOGIC)
# ========================================

def route_marketing_request_tool(campaign_instructions: str, requested_medium: str = "auto") -> str:
    """
    Main coordinator tool that routes to appropriate specialist agent
    
    Args:
        campaign_instructions: User's campaign requirements
        requested_medium: Specific medium ('email', 'social_media', 'direct_mail', 'web_landing_page') or 'auto'
    
    Returns:
        JSON with routed campaign results
    """
    
    try:
        # Auto-detect medium if not specified
        if requested_medium == "auto":
            detection_prompt = f"""
            Analyze this marketing campaign request and determine the best medium:
            
            REQUEST: {campaign_instructions}
            
            Choose ONE from: email, social_media, direct_mail, web_landing_page
            
            Consider:
            - Keywords indicating specific medium (email, social, mail, website, landing)
            - Campaign goals (awareness=social, conversion=landing, retention=email, local=direct_mail)
            - Target audience (B2B=email/linkedin, B2C=social/direct_mail, leads=landing)
            
            Respond with just the medium name.
            """
            
            model = GenerativeModel("gemini-2.5-pro-preview-05-06")
            detection_response = model.generate_content(detection_prompt)
            detected_medium = detection_response.text.strip().lower()
            
            # Validate detection
            valid_mediums = ['email', 'social_media', 'direct_mail', 'web_landing_page']
            if detected_medium not in valid_mediums:
                detected_medium = 'email'  # Default fallback
            
            medium = detected_medium
        else:
            medium = requested_medium.lower()
        
        # Route to appropriate specialist agent
        routing_map = {
            'email': email_marketing_tool,
            'social_media': social_media_tool,
            'direct_mail': direct_mail_tool,
            'web_landing_page': web_landing_page_tool
        }
        
        if medium in routing_map:
            specialist_result = routing_map[medium](campaign_instructions, include_image=True)
            specialist_data = json.loads(specialist_result)
            
            # Add routing information
            specialist_data["routing_info"] = {
                "requested_medium": requested_medium,
                "selected_medium": medium,
                "auto_detected": requested_medium == "auto"
            }
            
            return json.dumps(specialist_data, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": f"Unknown medium: {medium}",
                "available_mediums": list(routing_map.keys())
            }, indent=2)
    
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# ========================================
# ADK AGENT SETUP (SAME AS BEFORE)
# ========================================

# Main root agent for ADK
root_agent = Agent(
    name="marketing_coordinator",
    model="gemini-2.0-flash",
    instruction="""
    You are the MARKETING COORDINATOR who intelligently routes campaign requests to specialist agents.
    
    YOUR ROLE:
    🎯 Analyze campaign requests and determine optimal marketing medium
    🔀 Route requests to appropriate specialist agents
    📊 Create final, polished marketing content ready for immediate use
    🎨 Ensure professional quality across all mediums
    
    SPECIALIST AGENTS AVAILABLE:
    📧 Email Marketing Specialist - High-converting email campaigns
    📱 Social Media Specialist - Engaging, viral social content  
    📮 Direct Mail Specialist - High-response physical mail
    🌐 Landing Page Specialist - Conversion-optimized web pages
    
    ROUTING LOGIC:
    - Keywords: Look for medium-specific terms (email, social, mail, website)
    - Goals: Awareness→Social, Conversion→Landing, Retention→Email, Local→Direct Mail
    - Audience: B2B→Email/LinkedIn, B2C→Social/Direct Mail, Leads→Landing Page
    
    Always route to the most appropriate specialist for optimal campaign results.
    Always provide ONE final, polished piece ready for immediate use.
    """,
    description="Marketing coordinator that routes to specialized marketing agents",
    tools=[route_marketing_request_tool]
)