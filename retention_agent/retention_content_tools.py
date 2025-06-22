"""
retention Content Generation Tools
File: retention_agent/retention_content_tools.py

Tools for generating personalized retention emails, call scripts, and managing content
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from .config import RetentionConfig
config= RetentionConfig()

# Global instances
_retention_content_manager = None

# =============================================================================
# ADK TOOL FUNCTIONS
# =============================================================================

def generate_retention_email_tool(
    customer_id: str,
    customer_data: str,
    churn_factors: str,
    protective_factors: str,
    email_type: str = "retention",
    tone: str = "empathetic"
) -> str:
    """
    ADK Tool: Generate personalized retention email based on customer analysis
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data from SQL
        churn_factors: SHAP analysis of churn risk factors
        protective_factors: SHAP analysis of protective factors
        email_type: Type of email (retention, win_back, loyalty, survey)
        tone: Email tone (empathetic, professional, urgent, friendly, appreciative)
        
    Returns:
        str: Clean formatted email content ready for display
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Create personalized email generation prompt
        prompt = f"""
You are a retention specialist creating a highly personalized email for customer {customer_id}.

CUSTOMER PROFILE:
{customer_data}

CHURN RISK FACTORS (what might cause them to leave):
{churn_factors}

PROTECTIVE FACTORS (what keeps them loyal):
{protective_factors}

EMAIL SPECIFICATIONS:
- Type: {email_type}
- Tone: {tone}
- Customer ID: {customer_id}

INSTRUCTIONS:
Create a personalized retention email that:

1. ADDRESSES SPECIFIC CONCERNS: Reference the churn risk factors identified in the SHAP analysis
2. BUILDS ON STRENGTHS: Highlight and reinforce the protective factors that keep them loyal
3. PERSONALIZES CONTENT: Use specific details from their customer profile
4. PROVIDES SOLUTIONS: Offer concrete solutions to address their potential concerns
5. MAINTAINS RELATIONSHIP: Use the specified tone appropriately for their profile
6. Email will be from : Alberta Energy Inc

EMAIL STRUCTURE:
- Subject line (compelling and personalized)
- Greeting (use appropriate level of formality)
- Personal recognition (acknowledge their value/loyalty)
- Address concerns (based on churn factors)
- Reinforce positives (based on protective factors)
- Specific offer or solution
- Clear call to action
- Professional closing

TONE GUIDELINES:
- Empathetic: Understanding, caring, acknowledging their concerns
- Professional: Business-focused, formal, respectful
- Urgent: Time-sensitive, clear urgency without being pushy
- Friendly: Warm, approachable, conversational
- Appreciative: Grateful, value-focused, recognition-heavy

Return ONLY the email content without any JSON formatting or metadata.
Make the email feel genuinely personal and data-informed, not generic.
"""
        
        # Generate email using Gemini
        model = GenerativeModel(config.primary_model)
        response = model.generate_content(prompt)
        
        # Return clean email content
        return f"📧 **PERSONALIZED retention EMAIL FOR {customer_id}**\n\n{response.text}"
        
    except Exception as e:
        return f"❌ Error generating retention email for {customer_id}: {str(e)}"

def generate_call_script_tool(
    customer_id: str,
    customer_data: str,
    churn_factors: str,
    protective_factors: str,
    call_type: str = "retention",
    approach: str = "consultative"
) -> str:
    """
    ADK Tool: Generate personalized call script based on customer analysis
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data from SQL
        churn_factors: SHAP analysis of churn risk factors
        protective_factors: SHAP analysis of protective factors
        call_type: Type of call (retention, win_back, check_in, issue_resolution)
        approach: Call approach (consultative, relationship_building, problem_solving, value_reinforcement)
        
    Returns:
        str: Clean formatted call script ready for display
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Create personalized call script generation prompt
        prompt = f"""
You are a retention specialist creating a detailed call script for customer {customer_id}.

CUSTOMER PROFILE:
{customer_data}

CHURN RISK FACTORS (what might cause them to leave):
{churn_factors}

PROTECTIVE FACTORS (what keeps them loyal):
{protective_factors}

CALL SPECIFICATIONS:
- Type: {call_type}
- Approach: {approach}
- Customer ID: {customer_id}

INSTRUCTIONS:
Create a comprehensive call script that:

1. PERSONALIZED OPENING: Reference specific details from their profile
2. DISCOVERY QUESTIONS: Probe based on identified churn factors
3. ACTIVE LISTENING: Shows understanding of their situation
4. SOLUTION FOCUS: Address concerns with specific solutions
5. VALUE REINFORCEMENT: Highlight protective factors and benefits
6. OBJECTION HANDLING: Prepare for likely objections based on analysis
7. CLEAR NEXT STEPS: Define specific follow-up actions

CALL SCRIPT STRUCTURE:

**OPENING (Building Rapport)**
- Warm, personalized greeting
- Purpose of call (appropriate to approach)
- Permission to continue

**DISCOVERY PHASE (Understanding Current Situation)**
- Open-ended questions based on churn factors
- Listen for specific concerns or changes
- Probe deeper on key risk areas identified

**ANALYSIS SHARING (When Appropriate)**
- Acknowledge their loyalty/value (protective factors)
- Show understanding of their situation
- Position as partner, not vendor

**SOLUTION PRESENTATION**
- Address specific concerns raised
- Offer concrete solutions or alternatives
- Reinforce value and benefits they appreciate

**OBJECTION HANDLING**
- Anticipated objections based on churn factors
- Prepared responses with data/solutions
- Alternative options or compromises

**CLOSING & NEXT STEPS**
- Summarize agreements or commitments
- Schedule follow-up if needed
- Express appreciation

APPROACH GUIDELINES:
- Consultative: Focus on understanding and problem-solving
- Relationship Building: Emphasize partnership and long-term value
- Problem Solving: Direct focus on resolving specific issues
- Value Reinforcement: Highlight benefits and positive aspects

Return ONLY the call script content without any JSON formatting or metadata.
Include specific talking points, questions to ask, and notes about customer-specific factors throughout.
"""
        
        # Generate call script using Gemini
        model = GenerativeModel(config.primary_model)
        response = model.generate_content(prompt)
        
        # Return clean call script content
        return f"📞 **PERSONALIZED CALL SCRIPT FOR {customer_id}**\n\n{response.text}"
        
    except Exception as e:
        return f"❌ Error generating call script for {customer_id}: {str(e)}"

def analyze_customer_profile_tool(
    customer_id: str,
    customer_data: str,
    churn_factors: str,
    protective_factors: str
) -> str:
    """
    ADK Tool: Analyze customer profile and provide retention insights
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data from SQL
        churn_factors: SHAP analysis of churn risk factors
        protective_factors: SHAP analysis of protective factors
        
    Returns:
        JSON string with customer analysis and retention recommendations
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Create customer analysis prompt
        prompt = f"""
You are a retention analyst providing insights on customer {customer_id}.

CUSTOMER PROFILE:
{customer_data}

CHURN RISK FACTORS:
{churn_factors}

PROTECTIVE FACTORS:
{protective_factors}

ANALYSIS INSTRUCTIONS:
Provide a comprehensive retention analysis including:

1. **CHURN RISK ASSESSMENT**
   - Overall risk level (Low/Medium/High)
   - Key risk factors and their impact
   - Specific concerns that need addressing

2. **retention STRENGTHS**
   - Protective factors that keep them loyal
   - Positive aspects to build upon
   - Relationship advantages

3. **retention STRATEGY**
   - Recommended approach (email, call, or both)
   - Best timing for outreach
   - Key messages to emphasize

4. **SPECIFIC RECOMMENDATIONS**
   - Immediate actions to take
   - Long-term relationship building
   - Preventive measures

5. **SUCCESS METRICS**
   - How to measure retention efforts
   - Key indicators to monitor
   - Follow-up schedule

Make recommendations specific and actionable for retention teams.
"""
        
        # Generate analysis using Gemini
        model = GenerativeModel(config.default_model)
        response = model.generate_content(prompt)
        analysis_report = response.text
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "retention_analysis": analysis_report,
            "analysis_details": {
                "analysis_type": "comprehensive_retention_profile",
                "based_on": "SHAP analysis and customer data",
                "recommendations": "actionable retention strategies"
            },
            "word_count": len(analysis_report.split()),
            "message": "Customer retention analysis completed successfully."
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)