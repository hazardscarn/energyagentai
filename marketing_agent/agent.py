import json
import base64
import zipfile
from io import BytesIO
from datetime import datetime
from typing import Optional, Dict, Any
from google.adk.agents import Agent
import os


from google import genai
from google.genai import types

# For text generation  
import vertexai
from vertexai.generative_models import GenerativeModel

project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
vertexai.init(project=project_id, location=location)

# ========================================
# FIXED IMAGE GENERATION WITH BETTER ERROR HANDLING
# ========================================

def _generate_specialist_image(campaign_instructions: str, specialist_type: str) -> Dict:
    """Generate specialist-specific marketing image using Vertex AI - FIXED VERSION"""
    
    try:
        print(f"Generating {specialist_type} image...")
        
        # Get specific visual elements for the campaign
        visual_elements = _extract_visual_elements(campaign_instructions, specialist_type)
        
        # Create specific, detailed image prompt
        image_prompt = f"""
        Create a professional, photorealistic marketing image showing:
        
        {visual_elements}
        
        Style: Professional commercial photography, excellent lighting, high quality
        
        Requirements:
        - NO text, words, or letters in the image
        - Professional, clean, modern look
        - Show people benefiting from the service
        - Photorealistic and commercially viable
        """
        

        
        client = genai.Client(
            vertexai=True,
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai"),
            location="global",
        )
        
        model = "gemini-2.0-flash-preview-image-generation"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_text(text=image_prompt)
                ]
            ),
        ]
        
        # FIXED: Use the exact config from your working example
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            max_output_tokens=8192,
            response_modalities=["TEXT", "IMAGE"],  # CRITICAL: Must include both TEXT and IMAGE
            safety_settings=[
                types.SafetySetting(
                    category="HARM_CATEGORY_HATE_SPEECH",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_DANGEROUS_CONTENT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_HARASSMENT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_IMAGE_HATE",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_IMAGE_DANGEROUS_CONTENT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_IMAGE_HARASSMENT",
                    threshold="OFF"
                ),
                types.SafetySetting(
                    category="HARM_CATEGORY_IMAGE_SEXUALLY_EXPLICIT",
                    threshold="OFF"
                )
            ],
        )
        
        # FIXED: Use streaming like your working example
        image_data = None
        text_response = ""
        
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            # Collect text response
            if hasattr(chunk, 'text') and chunk.text:
                text_response += chunk.text
            
            # Look for image data in each chunk
            if hasattr(chunk, 'candidates') and chunk.candidates:
                for candidate in chunk.candidates:
                    if hasattr(candidate, 'content') and candidate.content:
                        if hasattr(candidate.content, 'parts') and candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'inline_data') and part.inline_data:
                                    if part.inline_data.data:
                                        image_data = part.inline_data.data
                                        break
        
        # Process the image data if found
        if image_data and len(image_data) > 100:  # Ensure we have actual image data
            if isinstance(image_data, bytes):
                image_data_b64 = base64.b64encode(image_data).decode('utf-8')
            else:
                image_data_b64 = str(image_data)
            
            print(f"✅ Image generated successfully ({len(image_data)} bytes)")
            return {
                "success": True,
                "image_data": image_data_b64,
                "format": "PNG",
                "description": f"Professional {specialist_type.replace('_', ' ')} marketing image",
                "specialist_type": specialist_type,
                "size_bytes": len(image_data),
                "text_response": text_response
            }
        else:
            print("❌ No image data found in streaming response")
            return {
                "success": False,
                "error": "No image data found in response",
                "text_response": text_response
            }
        
    except Exception as e:
        print(f"❌ Image generation error: {str(e)}")
        return {
            "success": False,
            "error": f"Image generation failed: {str(e)}",
            "specialist_type": specialist_type
        }

def _get_simple_visual_description(campaign_instructions: str, specialist_type: str) -> str:
    """Get simplified visual description for more reliable image generation"""
    
    instructions_lower = campaign_instructions.lower()
    
    # Simple base descriptions
    if any(term in instructions_lower for term in ['hvac', 'heating', 'furnace']):
        base = "HVAC technician installing modern heating system at home"
    elif any(term in instructions_lower for term in ['energy', 'solar', 'green']):
        base = "Energy consultant showing homeowner energy savings"
    elif any(term in instructions_lower for term in ['smart', 'thermostat']):
        base = "Family using smart home technology"
    else:
        base = "Professional home service technician at work"
    
    # Add specialist-specific context
    if specialist_type == "email":
        return f"{base}, professional and trustworthy"
    elif specialist_type == "social_media":
        return f"{base}, happy and engaging"
    elif specialist_type == "direct_mail":
        return f"{base}, high-impact and attention-grabbing"
    elif specialist_type == "web_landing_page":
        return f"{base}, modern and conversion-focused"
    else:
        return base

def _extract_visual_elements(campaign_instructions: str, specialist_type: str = "general") -> str:
    """Extract specific visual elements based on campaign content and specialist type"""
    
    instructions_lower = campaign_instructions.lower()
    
    # Base visual elements based on campaign content
    if any(term in instructions_lower for term in ['hvac', 'heating', 'furnace', 'heat pump', 'air conditioning']):
        base_scene = """
        Modern home with professional HVAC installation:
        - Clean, uniformed technician working with modern equipment
        - Happy family comfortable in their home
        - Professional HVAC system or heat pump
        - Beautiful home interior showing comfort
        """
    elif any(term in instructions_lower for term in ['energy', 'solar', 'efficiency', 'audit', 'green']):
        base_scene = """
        Energy efficiency consultation scene:
        - Professional energy consultant with modern tools
        - Homeowner learning about energy savings
        - Solar panels or energy-efficient home features
        - Modern home showing sustainable improvements
        """
    elif any(term in instructions_lower for term in ['smart', 'thermostat', 'automation', 'technology']):
        base_scene = """
        Smart home technology in use:
        - Family using smartphone to control home systems
        - Modern smart thermostat on wall
        - Comfortable home environment
        - Technology making life easier
        """
    else:
        base_scene = """
        Professional home service:
        - Expert service professional at work
        - Satisfied homeowner
        - Quality home improvements
        - Modern, well-maintained home
        - Green Energy solutions if applicable
        - Technology integration if applicable
        """
    
    return base_scene

# ========================================
# ALL SPECIALIST TOOLS (SAME AS BEFORE BUT WITH BETTER IMAGE HANDLING)
# ========================================

def email_marketing_specialist_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Email marketing specialist - creates high-converting email campaigns"""
    
    try:
        email_prompt = f"""
        You are an EMAIL MARKETING SPECIALIST creating a high-converting email campaign.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a complete email marketing campaign that's immediately ready for deployment.
        
        Structure your response EXACTLY like this:

        SUBJECT LINE:
        [Compelling subject line under 50 characters with urgency/benefit]

        EMAIL CONTENT:
        [Professional email content with clear structure: hook, value proposition, benefits, call-to-action]

        MOBILE OPTIMIZATION:
        [Brief notes on mobile-first design considerations]

        A/B TEST VARIANTS:
        [2-3 alternative subject lines for testing]

        CONVERSION STRATEGY:
        [Specific tactics to maximize open and click-through rates]

        Requirements:
        - Professional, trustworthy tone
        - Clear value proposition
        - Strong call-to-action
        - Mobile-optimized structure
        - Ready to send immediately
        """
        
        model = GenerativeModel("gemini-2.0-flash")
        content_response = model.generate_content(email_prompt)
        email_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "email_marketing_specialist", 
            "content": email_content,
            "structured_output": _parse_email_content(email_content)
        }
        
        if include_image:
            print("🖼️ Email specialist generating image...")
            image_result = _generate_specialist_image(campaign_instructions, "email")
            result["image"] = image_result
            if image_result["success"]:
                print("✅ Email image generated successfully")
            else:
                print(f"⚠️ Email image generation failed: {image_result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        import traceback
        print(f"Email marketing specialist error: {traceback.format_exc()}")
        return json.dumps({
            "success": False,
            "error": str(e), 
            "agent_type": "email_marketing_specialist"
        }, indent=2)

def social_media_specialist_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Social media specialist - creates social campaigns"""
    
    try:
        social_prompt = f"""
        You are a SOCIAL MEDIA MARKETING SPECIALIST creating ONE final, polished social campaign.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a complete social media campaign that's immediately ready for posting.
        
        Structure your response EXACTLY like this:

        MAIN POST:
        [Engaging social media post under 150 words with hook, value prop, CTA]

        HASHTAGS:
        [8-10 relevant hashtags for maximum reach]

        PLATFORM ADAPTATION:
        [Brief notes for Facebook, Instagram, LinkedIn optimization]

        ENGAGEMENT STRATEGY:
        [Specific way to encourage comments/interaction]

        Requirements:
        - Conversational, authentic tone
        - Shareable and engaging
        - Include emojis where appropriate
        - Ready to post immediately
        """
        
        model = GenerativeModel("gemini-2.0-flash")
        content_response = model.generate_content(social_prompt)
        social_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "social_media_specialist", 
            "content": social_content,
            "structured_output": _parse_social_content(social_content)
        }
        
        if include_image:
            print("🖼️ Social specialist generating image...")
            image_result = _generate_specialist_image(campaign_instructions, "social_media")
            result["image"] = image_result
            if image_result["success"]:
                print("✅ Social image generated successfully")
            else:
                print(f"⚠️ Social image generation failed: {image_result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        import traceback
        print(f"Social media specialist error: {traceback.format_exc()}")
        return json.dumps({
            "success": False,
            "error": str(e), 
            "agent_type": "social_media_specialist"
        }, indent=2)

def direct_mail_specialist_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Direct mail specialist - creates high-response physical mail campaigns"""
    
    try:
        direct_mail_prompt = f"""
        You are a DIRECT MAIL MARKETING SPECIALIST creating a high-response physical mail campaign.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a complete direct mail campaign that's immediately ready for printing and mailing.
        
        Structure your response EXACTLY like this:

        HEADLINE:
        [Powerful, attention-grabbing headline for the mail piece]

        MAIN MESSAGE:
        [Compelling direct mail copy with clear benefits and urgency]

        CALL-TO-ACTION:
        [Multiple response options: phone, website, QR code, mail-back card]

        DESIGN SPECIFICATIONS:
        [Layout recommendations for postcard/letter format]

        RESPONSE TRACKING:
        [Methods to track response rates and ROI]

        Requirements:
        - Direct, benefit-focused language
        - Strong visual hierarchy
        - Multiple response mechanisms
        - Print-optimized format
        - High-impact messaging
        """
        
        model = GenerativeModel("gemini-2.0-flash")
        content_response = model.generate_content(direct_mail_prompt)
        direct_mail_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "direct_mail_specialist", 
            "content": direct_mail_content,
            "structured_output": _parse_direct_mail_content(direct_mail_content)
        }
        
        if include_image:
            print("🖼️ Direct mail specialist generating image...")
            image_result = _generate_specialist_image(campaign_instructions, "direct_mail")
            result["image"] = image_result
            if image_result["success"]:
                print("✅ Direct mail image generated successfully")
            else:
                print(f"⚠️ Direct mail image generation failed: {image_result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        import traceback
        print(f"Direct mail specialist error: {traceback.format_exc()}")
        return json.dumps({
            "success": False,
            "error": str(e), 
            "agent_type": "direct_mail_specialist"
        }, indent=2)

def web_landing_page_specialist_tool(campaign_instructions: str, include_image: bool = True) -> str:
    """Landing page specialist - creates conversion-optimized web pages"""
    
    try:
        landing_page_prompt = f"""
        You are a LANDING PAGE SPECIALIST creating a conversion-optimized web page.
        
        CAMPAIGN INSTRUCTIONS: {campaign_instructions}
        
        Create a complete landing page strategy that's immediately ready for development.
        
        Structure your response EXACTLY like this:

        HERO SECTION:
        [Compelling headline, subheadline, and primary CTA for above-the-fold]

        VALUE PROPOSITION:
        [Clear benefits and unique selling points in scannable format]

        SOCIAL PROOF:
        [Testimonials, reviews, certifications, trust indicators]

        CONVERSION ELEMENTS:
        [Forms, CTAs, urgency tactics, risk reversal]

        MOBILE OPTIMIZATION:
        [Mobile-first design considerations and responsive elements]

        A/B TEST ELEMENTS:
        [Key elements to test for conversion optimization]

        Requirements:
        - Conversion-focused structure
        - Trust-building elements
        - Clear user journey
        - Mobile-first design
        - Ready for development
        """
        
        model = GenerativeModel("gemini-2.0-flash")
        content_response = model.generate_content(landing_page_prompt)
        landing_page_content = content_response.text
        
        result = {
            "success": True,
            "agent_type": "web_landing_page_specialist", 
            "content": landing_page_content,
            "structured_output": _parse_landing_page_content(landing_page_content)
        }
        
        if include_image:
            print("🖼️ Landing page specialist generating image...")
            image_result = _generate_specialist_image(campaign_instructions, "web_landing_page")
            result["image"] = image_result
            if image_result["success"]:
                print("✅ Landing page image generated successfully")
            else:
                print(f"⚠️ Landing page image generation failed: {image_result.get('error', 'Unknown error')}")
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        import traceback
        print(f"Landing page specialist error: {traceback.format_exc()}")
        return json.dumps({
            "success": False,
            "error": str(e), 
            "agent_type": "web_landing_page_specialist"
        }, indent=2)

# ========================================
# COORDINATOR WITH PROPER ROUTING (SAME AS BEFORE)
# ========================================

def marketing_coordinator_tool(campaign_instructions: str, requested_medium: str = "auto") -> str:
    """Marketing coordinator with proper routing to all specialists"""
    
    try:
        print(f"🎯 Coordinator analyzing request: {campaign_instructions[:100]}...")
        
        # Auto-detect medium if not specified
        if requested_medium == "auto":
            medium = _detect_marketing_medium(campaign_instructions)
            print(f"🤖 Auto-detected medium: {medium}")
        else:
            medium = requested_medium.lower()
            print(f"📍 Using requested medium: {medium}")
        
        # Route to appropriate specialist
        specialist_result = None
        
        if medium == "email":
            print(f"🔀 Routing to Email Marketing Specialist...")
            specialist_result = email_marketing_specialist_tool(campaign_instructions, include_image=True)
            
        elif medium == "social_media":
            print(f"🔀 Routing to Social Media Specialist...")
            specialist_result = social_media_specialist_tool(campaign_instructions, include_image=True)
            
        elif medium == "direct_mail":
            print(f"🔀 Routing to Direct Mail Specialist...")
            specialist_result = direct_mail_specialist_tool(campaign_instructions, include_image=True)
            
        elif medium == "web_landing_page":
            print(f"🔀 Routing to Landing Page Specialist...")
            specialist_result = web_landing_page_specialist_tool(campaign_instructions, include_image=True)
            
        else:
            print(f"⚠️ Unknown medium '{medium}', falling back to social media...")
            specialist_result = social_media_specialist_tool(campaign_instructions, include_image=True)
            medium = "social_media"
        
        specialist_data = json.loads(specialist_result)
        
        if not specialist_data.get("success", False):
            return specialist_result
        
        print("📦 Creating downloadable package...")
        
        # Create downloadable package
        package_result = _create_downloadable_package(specialist_data, campaign_instructions, medium)
        
        # Add routing information
        package_result["routing_info"] = {
            "requested_medium": requested_medium,
            "selected_medium": medium, 
            "auto_detected": requested_medium == "auto",
            "specialist_used": specialist_data.get("agent_type", medium)
        }
        
        return json.dumps(package_result, indent=2)
        
    except Exception as e:
        import traceback
        print(f"Coordinator error: {traceback.format_exc()}")
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)

# ========================================
# PACKAGE CREATION (IMPROVED TO HANDLE MISSING IMAGES)
# ========================================

def _create_downloadable_package(specialist_data: Dict, campaign_instructions: str, medium: str) -> Dict:
    """Create downloadable ZIP package with improved error handling"""
    
    try:
        print("📦 Creating ZIP package...")
        
        # Create in-memory ZIP file
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Add HTML presentation file
            html_content = _create_html_presentation(specialist_data, campaign_instructions, medium)
            zip_file.writestr(f"marketing_campaign_{medium}.html", html_content.encode('utf-8'))
            print("✅ HTML file added to package")
            
            # Add text content file
            zip_file.writestr(f"campaign_content_{medium}.txt", specialist_data["content"].encode('utf-8'))
            print("✅ Text content added to package")
            
            # Add image file if available
            image_included = False
            image_status = "not_generated"
            
            if specialist_data.get("image", {}).get("success") and "image_data" in specialist_data["image"]:
                try:
                    image_data = specialist_data["image"]["image_data"]
                    
                    if isinstance(image_data, str):
                        image_bytes = base64.b64decode(image_data)
                    else:
                        image_bytes = image_data
                    
                    zip_file.writestr(f"campaign_image_{medium}.png", image_bytes)
                    image_included = True
                    image_status = "included"
                    print("✅ Image added to ZIP package")
                except Exception as img_error:
                    print(f"⚠️ Failed to add image to package: {str(img_error)}")
                    image_status = "failed_to_add"
            else:
                print("⚠️ No image to add to package")
                image_status = "generation_failed"
            
            # Add README file with image status
            readme_content = f"""
Marketing Campaign Package
=========================

Campaign Type: {medium.replace('_', ' ').title()}
Generated by: {specialist_data.get('agent_type', 'Marketing Specialist')}
Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Files Included:
- marketing_campaign_{medium}.html - Professional presentation
- campaign_content_{medium}.txt - Raw content for copy-paste
- campaign_image_{medium}.png - Campaign image {'✅ Included' if image_included else '❌ Not available'}

Image Status: {image_status}
{f"Image Error: {specialist_data.get('image', {}).get('error', 'Unknown')}" if not image_included else ""}

Usage Instructions:
1. Open the HTML file to see the complete presentation
2. Copy content from the text file for your marketing platform
3. Use the PNG image in your marketing materials (if available)
4. Customize as needed for your brand

Campaign Requirements:
{campaign_instructions}

Generated by Multi-Agent Marketing System
Specialist: {specialist_data.get('agent_type', 'Unknown')}

Note: If image generation failed, you can use stock photos or create custom visuals
based on the campaign content and specifications provided.
"""
            zip_file.writestr("README.txt", readme_content.encode('utf-8'))
            print("✅ README added to package")
        
        # Get ZIP data and encode properly
        zip_buffer.seek(0)
        zip_bytes = zip_buffer.getvalue()
        zip_data_b64 = base64.b64encode(zip_bytes).decode('utf-8')
        
        print(f"✅ ZIP package created successfully ({len(zip_bytes)} bytes)")
        
        return {
            "success": True,
            "medium": medium,
            "specialist_used": specialist_data.get("agent_type"),
            "content_preview": specialist_data["content"][:200] + "...",
            "image_available": image_included,
            "image_status": image_status,
            "zip_data": zip_data_b64,
            "zip_size": len(zip_bytes),
            "filename": f"marketing_campaign_{medium}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            "package_info": {
                "medium": medium.replace("_", " ").title(),
                "specialist": specialist_data.get("agent_type", "").replace("_", " ").title(),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "contents": [
                    f"marketing_campaign_{medium}.html",
                    f"campaign_content_{medium}.txt",
                    f"campaign_image_{medium}.png" if image_included else "campaign_image_placeholder.txt",
                    "README.txt"
                ]
            }
        }
        
    except Exception as e:
        print(f"❌ Package creation error: {str(e)}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Package creation failed: {str(e)}"
        }

# ========================================
# HELPER FUNCTIONS (SAME AS BEFORE)
# ========================================

def _detect_marketing_medium(campaign_instructions: str) -> str:
    """Auto-detect the best marketing medium"""
    
    try:
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
        
        model = GenerativeModel("gemini-2.0-flash")
        response = model.generate_content(detection_prompt)
        detected_medium = response.text.strip().lower()
        
        valid_mediums = ['email', 'social_media', 'direct_mail', 'web_landing_page']
        return detected_medium if detected_medium in valid_mediums else 'social_media'
        
    except Exception:
        return 'social_media'

def _parse_email_content(content: str) -> Dict:
    """Parse email content into structured format"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    indicators = ['subject line:', 'email content:', 'mobile optimization:', 'a/b test variants:', 'conversion strategy:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in indicators)
        
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
    """Parse social media content into structured format"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    indicators = ['main post:', 'hashtags:', 'platform adaptation:', 'engagement strategy:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in indicators)
        
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
    """Parse direct mail content into structured format"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    indicators = ['headline:', 'main message:', 'call-to-action:', 'design specifications:', 'response tracking:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in indicators)
        
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
    """Parse landing page content into structured format"""
    sections = {}
    lines = content.split('\n')
    current_section = "full_content"
    current_text = []
    
    indicators = ['hero section:', 'value proposition:', 'social proof:', 'conversion elements:', 'mobile optimization:', 'a/b test elements:']
    
    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue
            
        line_lower = line_clean.lower()
        is_section = any(indicator in line_lower for indicator in indicators)
        
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

def _create_html_presentation(specialist_data: Dict, campaign_instructions: str, medium: str) -> str:
    """Create HTML presentation with embedded content and image"""
    
    content = specialist_data["content"]
    medium_title = medium.replace("_", " ").title()
    specialist_name = specialist_data.get("agent_type", "").replace("_", " ").title()
    
    # Embed image as base64 if available
    image_html = ""
    if specialist_data.get("image", {}).get("success") and "image_data" in specialist_data["image"]:
        try:
            image_data = specialist_data["image"]["image_data"]
            if isinstance(image_data, str):
                image_base64 = image_data
            else:
                image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            image_html = f'''
            <div class="image-container">
                <img src="data:image/png;base64,{image_base64}" alt="Campaign Image" class="campaign-image">
                <p class="image-caption">Generated by {specialist_name}</p>
            </div>
            '''
        except Exception as e:
            image_html = f'''
            <div class="image-container">
                <div class="image-placeholder">
                    <p>⚠️ Image display error: {str(e)}</p>
                    <p>Campaign content available below</p>
                </div>
            </div>
            '''
    else:
        error_msg = specialist_data.get("image", {}).get("error", "Image generation temporarily unavailable")
        image_html = f'''
        <div class="image-container">
            <div class="image-placeholder">
                <p>⚠️ Image not available</p>
                <p>Reason: {error_msg}</p>
                <p>Campaign content available below</p>
            </div>
        </div>
        '''
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{medium_title} Marketing Campaign</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 900px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{
                background: white;
                padding: 40px;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #2c3e50;
                text-align: center;
                border-bottom: 3px solid #3498db;
                padding-bottom: 15px;
                margin-bottom: 30px;
            }}
            .specialist-info {{
                background: linear-gradient(135deg, #6c5ce7 0%, #a29bfe 100%);
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: center;
            }}
            .campaign-meta {{
                background: linear-gradient(135deg, #74b9ff 0%, #0984e3 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 20px 0;
            }}
            .image-container {{
                text-align: center;
                margin: 30px 0;
            }}
            .campaign-image {{
                max-width: 100%;
                height: auto;
                border-radius: 10px;
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }}
            .image-placeholder {{
                background: #fff3cd;
                border: 2px dashed #ffc107;
                padding: 30px;
                border-radius: 10px;
                color: #856404;
            }}
            .image-caption {{
                font-style: italic;
                color: #666;
                margin-top: 10px;
            }}
            .content-section {{
                background: #f8f9fa;
                border-left: 5px solid #3498db;
                padding: 25px;
                margin: 25px 0;
                white-space: pre-wrap;
                font-family: 'Georgia', serif;
                border-radius: 5px;
            }}
            .usage-info {{
                background: linear-gradient(135deg, #00b894 0%, #00a085 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin: 25px 0;
            }}
            .timestamp {{
                text-align: center;
                color: #7f8c8d;
                font-size: 0.9em;
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #ecf0f1;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎯 {medium_title} Marketing Campaign</h1>
            
            <div class="specialist-info">
                <strong>🤖 Created by: {specialist_name}</strong>
            </div>
            
            <div class="campaign-meta">
                <strong>📋 Campaign Details</strong><br>
                <strong>Type:</strong> {medium_title} Marketing<br>
                <strong>Generated:</strong> {datetime.now().strftime("%B %d, %Y at %H:%M")}<br>
                <strong>Requirements:</strong> {campaign_instructions}
            </div>
            
            {image_html}
            
            <h2>📝 Campaign Content</h2>
            <div class="content-section">{content}</div>
            
            <div class="usage-info">
                <strong>📦 Multi-Agent Marketing System Results</strong><br><br>
                This campaign was created by our specialized <strong>{specialist_name}</strong> who is an expert in {medium_title.lower()} marketing.<br><br>
                <strong>Ready to Use:</strong> All content is optimized for {medium_title.lower()} and ready for immediate deployment.
            </div>
            
            <div class="timestamp">
                Generated by Multi-Agent Marketing System<br>
                Specialist: {specialist_name}<br>
                {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_template

# ========================================
# SIMPLIFIED INTERFACE FUNCTION
# ========================================

def generate_marketing_package(campaign_instructions: str, medium: str = "auto") -> Dict:
    """
    Generate marketing package using multi-agent system
    
    Args:
        campaign_instructions: What kind of campaign is needed
        medium: Marketing medium or 'auto'
    
    Returns:
        Dictionary with success status and package data
    """
    try:
        result_json = marketing_coordinator_tool(campaign_instructions, medium)
        return json.loads(result_json)
    except Exception as e:
        import traceback
        print(f"Generate marketing package error: {traceback.format_exc()}")
        return {
            "success": False,
            "error": f"Failed to generate marketing package: {str(e)}"
        }

# ========================================
# ADK AGENT DEFINITIONS (ALL SPECIALISTS)
# ========================================

def create_email_marketing_agent():
    """Create email marketing specialist agent"""
    return Agent(
        name="email_marketing_specialist", 
        model="gemini-2.0-flash",
        instruction="""
        You are an EMAIL MARKETING SPECIALIST focused on creating high-converting email campaigns.
        
        EXPERTISE:
        📧 Subject line optimization for maximum open rates
        📱 Mobile-first email design and structure
        💰 Conversion-focused content that drives action
        📊 A/B testing strategies and optimization
        
        Always create professional, trustworthy email campaigns that are immediately ready for deployment.
        Focus on building trust, providing value, and driving conversions.
        """,
        description="Email marketing specialist for high-converting email campaigns",
        tools=[email_marketing_specialist_tool]
    )

def create_social_media_agent():
    """Create social media marketing specialist agent"""
    return Agent(
        name="social_media_specialist", 
        model="gemini-2.0-flash",
        instruction="""
        You are a SOCIAL MEDIA MARKETING SPECIALIST focused on creating viral, engaging content.
        
        EXPERTISE:
        📱 Platform-specific optimization (Facebook, Instagram, LinkedIn, Twitter)
        #️⃣ Strategic hashtag research and implementation
        💬 Engagement-driven copy that drives interaction
        🔄 Shareable content that amplifies reach
        
        Always create one final, polished social media campaign that's immediately ready for posting.
        Focus on building community, driving engagement, and increasing brand visibility.
        """,
        description="Social media specialist for engaging, viral content",
        tools=[social_media_specialist_tool]
    )

def create_direct_mail_agent():
    """Create direct mail marketing specialist agent"""
    return Agent(
        name="direct_mail_specialist", 
        model="gemini-2.0-flash",
        instruction="""
        You are a DIRECT MAIL MARKETING SPECIALIST focused on creating high-response physical mail campaigns.
        
        EXPERTISE:
        📮 High-impact print design and messaging
        📞 Multi-channel response optimization (phone, web, QR)
        📊 Response tracking and ROI measurement
        🎯 Local targeting and geographic optimization
        
        Always create direct mail campaigns that are immediately ready for printing and distribution.
        Focus on maximum response rates and clear ROI tracking.
        """,
        description="Direct mail specialist for high-response physical campaigns",
        tools=[direct_mail_specialist_tool]
    )

def create_landing_page_agent():
    """Create landing page specialist agent"""
    return Agent(
        name="web_landing_page_specialist", 
        model="gemini-2.0-flash",
        instruction="""
        You are a LANDING PAGE SPECIALIST focused on creating conversion-optimized web pages.
        
        EXPERTISE:
        🌐 Conversion rate optimization and user experience
        📱 Mobile-first responsive design
        🔍 A/B testing and performance optimization
        🛡️ Trust-building and credibility elements
        
        Always create landing page strategies that are immediately ready for development.
        Focus on maximum conversion rates and user trust.
        """,
        description="Landing page specialist for conversion-optimized web pages",
        tools=[web_landing_page_specialist_tool]
    )

def create_marketing_coordinator_agent():
    """Create main marketing coordinator agent"""
    return Agent(
        name="marketing_coordinator",
        model="gemini-2.0-flash",
        instruction="""
        You are the MARKETING COORDINATOR who manages a team of specialist marketing agents.
        
        YOUR TEAM:
        📧 Email Marketing Specialist - High-converting email campaigns
        📱 Social Media Specialist - Engaging, viral social content
        📮 Direct Mail Specialist - High-response physical mail  
        🌐 Landing Page Specialist - Conversion-optimized web pages
        
        YOUR ROLE:
        🎯 Analyze campaign requests and determine optimal marketing medium
        🔀 Route requests to the most appropriate specialist agent
        📦 Coordinate the creation of complete marketing packages
        🎨 Ensure consistent quality across all marketing mediums
        
        Always route to the most appropriate specialist for optimal campaign results.
        Create complete downloadable packages with content and images.
        """,
        description="Marketing coordinator managing specialist marketing agents",
        tools=[marketing_coordinator_tool]
    )

# Create all agents
email_agent = create_email_marketing_agent()
social_agent = create_social_media_agent()
direct_mail_agent = create_direct_mail_agent()
landing_page_agent = create_landing_page_agent()
coordinator_agent = create_marketing_coordinator_agent()

# Main root agent for ADK
root_agent = coordinator_agent

if __name__ == "__main__":
    # Test the image generation fix
    test_instructions = "Create campaign for HVAC upgrades targeting Calgary homeowners with oil heating"
    
    print("🧪 Testing image generation fix...")
    result = generate_marketing_package(test_instructions, "direct_mail")
    print(f"Success: {result.get('success')}")
    print(f"Medium: {result.get('medium')}")
    print(f"Image Available: {result.get('image_available')}")
    print(f"Image Status: {result.get('image_status')}")
    
    if not result.get('image_available'):
        print("Note: Campaign content and ZIP package still created successfully without image")