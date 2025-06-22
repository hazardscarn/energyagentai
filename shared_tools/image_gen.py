"""
Image Generation Tool for Marketing Agent
File: shared_tools/image_gen.py
COMPLETE UPDATED FILE - Uses Vertex AI instead of API keys
"""

import os
import json
import pathlib
from typing import Optional
from datetime import datetime
from PIL import Image
import vertexai
from vertexai.generative_models import GenerativeModel

# Global instances
_image_generator = None

def initialize_image_generator():
    """Initialize Image Generator (call once)"""
    global _image_generator
    if _image_generator is None:
        _image_generator = MarketingImageGenerator()

class MarketingImageGenerator:
    """Enhanced image generator for marketing campaigns with session integration"""
    
    def __init__(self):
        # Initialize Vertex AI
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        
        vertexai.init(project=project_id, location=location)
        
        # Initialize Gemini model for image generation
        self.model = GenerativeModel("gemini-2.0-flash-exp")
        
        # Base output directory - will be organized by session
        self.base_output_dir = "marketing_outputs"
        os.makedirs(self.base_output_dir, exist_ok=True)
    
    def get_session_image_dir(self, session_id: str = "default") -> str:
        """Get or create image directory for a session"""
        session_dir = f"{self.base_output_dir}/{session_id}/images"
        os.makedirs(session_dir, exist_ok=True)
        return session_dir
    
    def enhance_marketing_prompt(self, prompt: str, image_type: str) -> str:
        """Enhanced prompt engineering for marketing images"""
        
        type_enhancements = {
            "marketing": """
                Create a professional, high-quality marketing image suitable for business use.
                Focus on clean composition, excellent lighting, and modern aesthetic.
                Use colors that convey trust and professionalism.
            """,
            "email": """
                Design an email marketing header image that's visually striking yet clean.
                Optimize for email viewing with bold, clear visuals and good contrast.
                Ensure it works well at different screen sizes.
            """,
            "social": """
                Generate a social media marketing image with vibrant, engaging visuals.
                Use dynamic composition and colors that perform well on social platforms.
                Make it shareable and eye-catching for social media feeds.
            """,
            "promotional": """
                Create a promotional marketing image with attention-grabbing elements.
                Use bold colors, dynamic composition, and visual elements that convey value.
                Incorporate design elements that suggest urgency or special offers.
            """,
            "product": """
                Design a clean, professional product marketing image.
                Use studio-quality lighting and composition suitable for e-commerce.
                Focus on highlighting product features with premium presentation.
            """,
            "brand": """
                Generate a brand-focused marketing image that conveys quality and trust.
                Use sophisticated design elements and premium visual aesthetics.
                Create imagery that reinforces brand values and professionalism.
            """,
            "landing_page": """
                Create a hero image for landing pages that converts visitors.
                Use compelling visuals that support the page's main value proposition.
                Ensure strong visual hierarchy and professional presentation.
            """,
            "newsletter": """
                Design a newsletter header image that's professional and approachable.
                Use clean, readable design with consistent branding elements.
                Create trustworthy visuals suitable for regular communication.
            """
        }
        
        enhancement = type_enhancements.get(image_type, type_enhancements["marketing"])
        
        enhanced_prompt = f"""
        {enhancement.strip()}
        
        User request: {prompt}
        
        IMPORTANT REQUIREMENTS:
        - NO TEXT, words, or letters should appear in the image
        - Focus entirely on visual elements, composition, and colors
        - Professional quality suitable for business/marketing use
        - High-resolution, clean, modern aesthetic
        - Appropriate for {image_type} marketing purposes
        - Use professional lighting and composition
        - Ensure visual appeal and brand-appropriate design
        
        Create a purely visual marketing image that communicates through design elements only.
        """
        
        return enhanced_prompt
    
    def save_generated_image(self, response, output_path: str) -> bool:
        """Save generated image from Vertex AI Gemini response"""
        try:
            # For Vertex AI Gemini responses, images are in response.candidates[0].content.parts
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data is not None:
                    # Decode base64 image data and save
                    image_data = part.inline_data.data
                    pathlib.Path(output_path).write_bytes(image_data)
                    return True
                elif hasattr(part, "file_data") and part.file_data is not None:
                    # Handle file_data format if present
                    # This is for cases where Vertex AI returns file references
                    print("File data format detected - this requires additional handling")
                    return False
            return False
        except Exception as e:
            print(f"Error saving image: {e}")
            return False
    
    def resize_for_marketing(self, image_path: str, width: int = 1024, height: int = 533) -> bool:
        """Resize image to marketing-friendly dimensions"""
        try:
            img = Image.open(image_path)
            resized_img = img.resize((width, height), Image.Resampling.LANCZOS)
            resized_img.save(image_path, quality=95, optimize=True)
            return True
        except Exception as e:
            print(f"Error resizing image: {e}")
            return False
    
    def generate_marketing_image(self, prompt: str, image_type: str = "marketing", 
                                session_id: str = "default", filename: Optional[str] = None,
                                resize: bool = True) -> dict:
        """Generate marketing image with session management"""
        try:
            # Get session directory
            session_image_dir = self.get_session_image_dir(session_id)
            
            # Generate filename if not provided
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{image_type}_image_{timestamp}.png"
            
            # Ensure .png extension
            if not filename.endswith('.png'):
                filename += '.png'
            
            output_path = os.path.join(session_image_dir, filename)
            
            # Enhance prompt for better marketing images
            enhanced_prompt = self.enhance_marketing_prompt(prompt, image_type)
            
            # Generate image using Vertex AI Gemini
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config={
                    "response_modalities": ["TEXT", "IMAGE"],
                    "max_output_tokens": 8192,
                    "temperature": 0.4,
                }
            )
            
            # Save the image
            save_success = self.save_generated_image(response, output_path)
            if not save_success:
                return {
                    "success": False,
                    "error": "Failed to save generated image",
                    "output_path": ""
                }
            
            # Resize for marketing use
            if resize:
                resize_success = self.resize_for_marketing(output_path, 1024, 533)
                dimensions = "1024x533 (marketing optimized)" if resize_success else "1024x533 (resize failed)"
            else:
                dimensions = "original"
            
            # Get file information
            file_size = os.path.getsize(output_path)
            file_size_mb = round(file_size / (1024 * 1024), 2)
            
            return {
                "success": True,
                "output_path": output_path,
                "filename": filename,
                "image_type": image_type,
                "session_id": session_id,
                "original_prompt": prompt,
                "enhanced_prompt": enhanced_prompt[:150] + "..." if len(enhanced_prompt) > 150 else enhanced_prompt,
                "file_size_mb": file_size_mb,
                "dimensions": dimensions,
                "message": f"Marketing image generated successfully: {filename}"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "output_path": ""
            }

# ADK Tool Function - Updated for session integration
def generate_marketing_image_tool(
    prompt: str, 
    image_type: str = "marketing", 
    filename: Optional[str] = None, 
    resize_for_email: bool = True,
    session_id: str = "default_session"
) -> str:
    """
    ADK Tool: Generate marketing image with session management
    
    Args:
        prompt: Text description of the image to generate
        image_type: Type of marketing image ('marketing', 'email', 'social', 'promotional', 'product', 'brand', 'landing_page', 'newsletter')
        filename: Optional custom filename for the image
        resize_for_email: Whether to resize image to marketing-friendly dimensions (1024x533)
        session_id: Session identifier for organizing files
        
    Returns:
        JSON string with image generation results and file information
    """
    global _image_generator
    
    try:
        # Initialize generator if needed
        initialize_image_generator()
        
        # Generate the image
        result = _image_generator.generate_marketing_image(
            prompt=prompt,
            image_type=image_type,
            session_id=session_id,
            filename=filename,
            resize=resize_for_email
        )
        
        if result["success"]:
            print(f"Generated marketing image: {result['filename']} for session: {result['session_id']}")
            
            # Also register the image with the session automatically
            try:
                # Import here to avoid circular imports
                from marketing_agent.marketing_content_tools import register_session_image_tool
                
                register_result = register_session_image_tool(
                    session_id=result['session_id'],
                    image_path=result['output_path'],
                    image_type=result['image_type'],
                    filename=result['filename']
                )
                register_info = json.loads(register_result)
            except ImportError:
                # If marketing_content_tools not available, skip registration
                register_info = {"success": False, "message": "Registration skipped - tools not available"}
            
            return json.dumps({
                "success": True,
                "message": result["message"],
                "image_details": {
                    "filename": result["filename"],
                    "output_path": result["output_path"],
                    "image_type": result["image_type"],
                    "session_id": result["session_id"],
                    "file_size_mb": result["file_size_mb"],
                    "dimensions": result["dimensions"]
                },
                "prompt_info": {
                    "original_prompt": result["original_prompt"],
                    "enhanced_prompt": result["enhanced_prompt"]
                },
                "session_registration": register_info,
                "next_steps": [
                    "Image automatically registered with session",
                    "Use create_download_package_tool to package all content",
                    "Generate more content with generate_marketing_copy_tool"
                ]
            }, indent=2)
        else:
            return json.dumps({
                "success": False,
                "error": result["error"],
                "error_type": result.get("error_type", "Unknown"),
                "prompt": prompt,
                "image_type": image_type,
                "session_id": session_id
            }, indent=2)
            
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "prompt": prompt,
            "image_type": image_type,
            "session_id": session_id,
            "troubleshooting": {
                "check_vertex_ai": "Ensure Vertex AI is properly initialized and authenticated",
                "check_permissions": "Verify Vertex AI API access and permissions", 
                "check_project": "Ensure GOOGLE_CLOUD_PROJECT environment variable is set",
                "check_disk_space": "Ensure sufficient disk space for image generation"
            }
        }, indent=2)

# Standalone test function
def test_marketing_image_generation():
    """Test the marketing image generation with session management"""
    print("Testing Marketing Image Generation with Vertex AI...")
    
    # Check for required environment variables
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("⚠️  GOOGLE_CLOUD_PROJECT environment variable not found.")
        print("Please set it to your Google Cloud Project ID.")
        return
    
    test_cases = [
        {
            "prompt": "Professional business team collaborating in modern office",
            "image_type": "marketing",
            "session_id": "test_session_1"
        },
        {
            "prompt": "Black Friday sale with shopping bags and discount elements",
            "image_type": "promotional", 
            "session_id": "test_session_1"
        },
        {
            "prompt": "Eco-friendly water bottle with nature background",
            "image_type": "product",
            "session_id": "test_session_1"
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['image_type']} image")
        result = generate_marketing_image_tool(**test_case)
        
        # Parse and display result
        result_data = json.loads(result)
        if result_data["success"]:
            print(f"✅ Success: {result_data['image_details']['filename']}")
            print(f"📁 Location: {result_data['image_details']['output_path']}")
        else:
            print(f"❌ Error: {result_data['error']}")

if __name__ == "__main__":
    # Run test
    test_marketing_image_generation()