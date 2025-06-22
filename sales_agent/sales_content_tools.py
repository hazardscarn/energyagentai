"""
Sales Content Generation Tools - Updated
File: sales_agent/sales_content_tools.py

Tools for generating personalized sales emails, call scripts, and managing content
"""

import os
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
from .config import salesConfig
from shared_tools.simple_sql_agents import (
    execute_query_json_tool
)
from shared_tools.mlagent import (load_and_score)

config = salesConfig()

# =============================================================================
# ADK TOOL FUNCTIONS
# =============================================================================

def get_sales_eligibility_customer(customer_id: str) -> Dict:
    """
    ADK Tool: Get the list of products and services a customer is eligible for.
    This will look if customer already has a product or service, and if not, it will return the list of products and services they are eligible for
    along with their sales probability.

    Args:
        customer_id: Customer identifier
        
    Returns:
        Dict: Dictionary of customer eligible Products and services with sales probability.
    """
    import numpy as np
    
    def convert_numpy_types(obj):
        """Convert numpy types to native Python types for JSON serialization"""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    try:
        eligible_plans = []

        # Query to get customer data
        sql_query = f"""SELECT * FROM `energyagentai.alberta_energy_ai.customer_base` WHERE customer_id = '{customer_id}'"""
        customer_data_result = execute_query_json_tool(sql_query=sql_query)
        customer_data_json = json.loads(customer_data_result)
        
        if not customer_data_json.get("success", False) or not customer_data_json.get("data"):
            return {
                "success": False,
                "customer_id": customer_id,
                "message": "Customer not found or no data available."
            }
        
        # Get the first (and should be only) customer record
        customer_data = customer_data_json["data"][0]
        
        # Check eligibility for each product/service
        if customer_data.get('green_plan_upsell_target', 1) == 0:
            try:
                green_plan_result = load_and_score(
                    model_name='upsell_green_plan', 
                    customer_data=customer_data, 
                    shap_enabled=False, 
                    bucket_name='albertaenergy-ads'
                )
                # Convert numpy types for JSON serialization
                green_plan_result = convert_numpy_types(green_plan_result)
                eligible_plans.append({
                    "product": "Green Energy Plan",
                    "sales_probability": green_plan_result,
                    "description": "Switch to our Green Energy Plan for sustainable energy solutions."
                })
            except Exception as e:
                print(f"Error scoring green plan: {e}")

        if customer_data.get('hvac_cross_sell_target', 1) == 0:
            try:
                hvac_result = load_and_score(
                    model_name='crosssell_hvac', 
                    customer_data=customer_data, 
                    shap_enabled=False, 
                    bucket_name='albertaenergy-ads'
                )
                hvac_result = convert_numpy_types(hvac_result)
                eligible_plans.append({
                    "product": "HVAC System",
                    "sales_probability": hvac_result,
                    "description": "Upgrade to our energy-efficient HVAC system repair and maintenance services."
                })
            except Exception as e:
                print(f"Error scoring HVAC: {e}")

        if customer_data.get('solar_cross_sell_target', 1) == 0:
            try:
                solar_result = load_and_score(
                    model_name='crosssell_solar', 
                    customer_data=customer_data, 
                    shap_enabled=False, 
                    bucket_name='albertaenergy-ads'
                )
                solar_result = convert_numpy_types(solar_result)
                eligible_plans.append({
                    "product": "Solar Panel Installation",
                    "sales_probability": solar_result,
                    "description": "Install solar panels to reduce your energy bills and carbon footprint."
                })
            except Exception as e:
                print(f"Error scoring solar: {e}")

        if customer_data.get('insurance_cross_sell_target', 1) == 0:
            try:
                insurance_result = load_and_score(
                    model_name='crosssell_insurance', 
                    customer_data=customer_data, 
                    shap_enabled=False, 
                    bucket_name='albertaenergy-ads'
                )
                insurance_result = convert_numpy_types(insurance_result)
                eligible_plans.append({
                    "product": "Home Insurance",
                    "sales_probability": insurance_result,
                    "description": "Protect your home with our comprehensive insurance plans."
                })
            except Exception as e:
                print(f"Error scoring insurance: {e}")

        if customer_data.get('surge_protection_upsell_target', 1) == 0:
            try:
                surge_result = load_and_score(
                    model_name='upsell_surge_protection', 
                    customer_data=customer_data, 
                    shap_enabled=False, 
                    bucket_name='albertaenergy-ads'
                )
                surge_result = convert_numpy_types(surge_result)
                eligible_plans.append({
                    "product": "Surge Protection",
                    "sales_probability": surge_result,
                    "description": "Safeguard your home appliances with our surge protection services."
                })
            except Exception as e:
                print(f"Error scoring surge protection: {e}")

        if customer_data.get('efficiency_analysis_upsell_target', 1) == 0:
            try:
                efficiency_result = load_and_score(
                    model_name='upsell_efficiency_analysis', 
                    customer_data=customer_data, 
                    shap_enabled=False, 
                    bucket_name='albertaenergy-ads'
                )
                efficiency_result = convert_numpy_types(efficiency_result)
                eligible_plans.append({
                    "product": "Energy Efficiency Analysis",
                    "sales_probability": efficiency_result,
                    "description": "Get a detailed analysis of your energy usage and recommendations for savings."
                })
            except Exception as e:
                print(f"Error scoring efficiency analysis: {e}")

        # Sort eligible plans by sales probability in descending order
        def get_prediction(plan):
            prob_result = plan.get('sales_probability', {})
            return prob_result.get('prediction', 0) if isinstance(prob_result, dict) else 0
        
        eligible_plans = sorted(eligible_plans, key=get_prediction, reverse=True)

        # Select the top plan with the highest sales probability
        top_plans = eligible_plans[:1]

        return {
            "success": True,
            "customer_id": customer_id,
            "eligible_products": top_plans,
            "total_eligible": len(eligible_plans),
            "message": "Customer eligibility for products and services retrieved successfully."
        }
    
    except Exception as e:
        return {
            "success": False,
            "customer_id": customer_id,
            "error": str(e),
            "message": "Error retrieving customer eligibility data."
        }

def generate_sales_email_tool(
    customer_id: str,
    customer_data: str,
    sales_promoting_factors: str,
    sales_preventing_factors: str,
    product_name: str = "",
    sales_probability: float = 0.0,
    email_type: str = "sales",
    tone: str = "empathetic"
) -> str:
    """
    ADK Tool: Generate personalized sales email based on customer analysis
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data from SQL
        sales_promoting_factors: SHAP analysis of factors promoting sales
        sales_preventing_factors: SHAP analysis of factors preventing sales
        product_name: Name of the product being sold (optional)
        sales_probability: Probability of sales success (optional)
        email_type: Type of email (sales, win_back, loyalty, survey)
        tone: Email tone (empathetic, professional, urgent, friendly, appreciative)
        
    Returns:
        str: Clean formatted email content ready for display
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Build product context if provided
        product_context = ""
        if product_name:
            product_context = f"""
PRODUCT: {product_name}
SALES PROBABILITY: {sales_probability:.1%}
"""
        
        # Create personalized email generation prompt
        prompt = f"""
You are a sales specialist creating a highly personalized email for customer {customer_id}.

CUSTOMER PROFILE:
{customer_data}
{product_context}
FACTORS PROMOTING SALES (what makes them likely to buy):
{sales_promoting_factors}

FACTORS PREVENTING SALES (what might stop them from buying):
{sales_preventing_factors}

EMAIL SPECIFICATIONS:
- Type: {email_type}
- Tone: {tone}
- Customer ID: {customer_id}
{'- Product Focus: ' + product_name if product_name else ''}

INSTRUCTIONS:
Create a personalized sales email that:

1. LEVERAGES PROMOTING FACTORS: Emphasize aspects that increase their likelihood to buy
2. ADDRESSES PREVENTING FACTORS: Proactively handle objections and concerns that might stop them
3. PERSONALIZES CONTENT: Use specific details from their customer profile
4. PROVIDES SOLUTIONS: Offer concrete solutions to address their potential concerns
5. MAINTAINS RELATIONSHIP: Use the specified tone appropriately for their profile
{'6. HIGHLIGHTS PRODUCT VALUE: Show how ' + product_name + ' solves their specific needs' if product_name else '6. HIGHLIGHTS VALUE: Show how our solutions address their needs'}
7. Email will be from : Alberta Energy Inc

EMAIL STRUCTURE:
- Subject line (compelling and personalized)
- Greeting (use appropriate level of formality)
- Personal recognition (acknowledge their value/situation)
- Address concerns (based on preventing factors)
- Reinforce positives (based on promoting factors)
- Specific offer or solution
- Clear call to action
- Professional closing

TONE GUIDELINES:
- Empathetic: Understanding, caring, acknowledging their concerns
- Professional: Business-focused, formal, respectful
- Urgent: Time-sensitive, clear urgency without being pushy
- Friendly: Warm, approachable, conversational
- Appreciative: Grateful, value-focused, recognition-heavy

Always sign off with name/Signature as Alberta Energy AI. Do not add random signatures or company names.

Return ONLY the email content without any JSON formatting or metadata.
Make the email feel genuinely personal and data-informed, not generic.
"""
        
        # Generate email using Gemini
        model = GenerativeModel(config.primary_model)
        response = model.generate_content(prompt)
        
        # Build header
        header = f"📧 **PERSONALIZED SALES EMAIL FOR {customer_id}**\n"
        if product_name:
            header += f"🎯 **Product:** {product_name}\n"
            header += f"📊 **Sales Probability:** {sales_probability:.1%}\n"
        header += "\n"
        
        return header + response.text
        
    except Exception as e:
        return f"❌ Error generating sales email for {customer_id}: {str(e)}"

def generate_call_script_tool(
    customer_id: str,
    customer_data: str,
    sales_promoting_factors: str,
    sales_preventing_factors: str,
    product_name: str = "",
    sales_probability: float = 0.0,
    call_type: str = "sales",
    approach: str = "consultative"
) -> str:
    """
    ADK Tool: Generate personalized call script based on customer analysis with SHAP reasoning
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data from SQL
        sales_promoting_factors: SHAP analysis of factors promoting sales
        sales_preventing_factors: SHAP analysis of factors preventing sales
        product_name: Name of the product being sold (optional)
        sales_probability: Probability of sales success (optional)
        call_type: Type of call (sales, win_back, check_in, issue_resolution)
        approach: Call approach (consultative, relationship_building, problem_solving, value_reinforcement)
        
    Returns:
        str: Clean formatted call script ready for display with SHAP reasoning
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Build product context if provided
        product_context = ""
        product_focus = ""
        if product_name:
            product_context = f"""
PRODUCT: {product_name}
SALES PROBABILITY: {sales_probability:.1%}
"""
            product_focus = f"- Product Focus: {product_name}"
        
        # Create personalized call script generation prompt with SHAP reasoning
        prompt = f"""
You are a sales specialist creating a detailed call script for customer {customer_id}.

CUSTOMER PROFILE:
{customer_data}
{product_context}
SHAP ANALYSIS - FACTORS PROMOTING SALES (what makes them likely to buy):
{sales_promoting_factors}

SHAP ANALYSIS - FACTORS PREVENTING SALES (what might stop them from buying):
{sales_preventing_factors}

CALL SPECIFICATIONS:
- Type: {call_type}
- Approach: {approach}
- Customer ID: {customer_id}
{product_focus}

INSTRUCTIONS:
Create a comprehensive call script with SHAP-BASED REASONING that:

1. PERSONALIZED OPENING: Reference specific details from their profile
2. DISCOVERY QUESTIONS: Probe based on identified promoting factors
3. ACTIVE LISTENING: Shows understanding of their situation
4. SOLUTION FOCUS: Address concerns with specific solutions based on preventing factors
5. VALUE REINFORCEMENT: Highlight promoting factors and benefits
6. OBJECTION HANDLING: Prepare for likely objections based on preventing factors analysis
7. CLEAR NEXT STEPS: Define specific follow-up actions

CALL SCRIPT STRUCTURE WITH SHAP REASONING:

**OPENING (Building Rapport)**
- Warm, personalized greeting
- Purpose of call (appropriate to approach)
- Permission to continue
- **🧠 SHAP REASONING:** Explain why this opening approach based on their factors

**DISCOVERY PHASE (Understanding Current Situation)**
- Open-ended questions based on promoting factors
- Listen for specific concerns or changes
- Probe deeper on key areas identified in SHAP analysis
- **🧠 SHAP REASONING:** For each question, explain which factors it targets

**ANALYSIS SHARING (When Appropriate)**
- Acknowledge their situation (promoting factors)
- Show understanding of their concerns (preventing factors)
- Position as partner, not vendor
- **🧠 SHAP REASONING:** How this builds on their specific profile

**SOLUTION PRESENTATION**
- Address specific concerns raised (preventing factors)
- Offer concrete solutions or alternatives
- Reinforce value and benefits they appreciate (promoting factors)
- **🧠 SHAP REASONING:** Why these solutions address their specific factors

**OBJECTION HANDLING**
- Anticipated objections based on preventing factors
- Prepared responses with data/solutions
- Alternative options or compromises
- **🧠 SHAP REASONING:** Which preventing factors each response addresses

**CLOSING & NEXT STEPS**
- Summarize agreements or commitments
- Schedule follow-up if needed
- Express appreciation
- **🧠 SHAP REASONING:** Why this closing approach fits their promoting factors

**SCRIPT REASONING SUMMARY**
Explain:
1. Overall strategy based on SHAP analysis
2. Key promoting factors being leveraged
3. Key preventing factors being addressed
4. Why this approach maximizes success{' for ' + product_name if product_name else ''}

APPROACH GUIDELINES:
- Consultative: Focus on understanding and problem-solving (explain which factors support this)
- Relationship Building: Emphasize partnership and long-term value (explain factor basis)
- Problem Solving: Direct focus on resolving specific issues (explain which preventing factors)
- Value Reinforcement: Highlight benefits and positive aspects (explain which promoting factors)

Return ONLY the call script content without any JSON formatting or metadata.
Include specific talking points, questions to ask, and notes about customer-specific factors throughout.
Make every recommendation explainable through the SHAP factor analysis.
"""
        
        # Generate call script using Gemini
        model = GenerativeModel(config.primary_model)
        response = model.generate_content(prompt)
        
        # Build header
        header = f"📞 **PERSONALIZED CALL SCRIPT FOR {customer_id}**\n"
        if product_name:
            header += f"🎯 **Product:** {product_name}\n"
            header += f"📊 **Sales Probability:** {sales_probability:.1%}\n"
        header += "\n"
        
        return header + response.text
        
    except Exception as e:
        return f"❌ Error generating call script for {customer_id}: {str(e)}"

def analyze_customer_profile_tool(
    customer_id: str,
    customer_data: str,
    sales_promoting_factors: str,
    sales_preventing_factors: str
) -> str:
    """
    ADK Tool: Analyze customer profile and provide sales insights
    
    Args:
        customer_id: Customer identifier
        customer_data: Customer profile data from SQL
        sales_promoting_factors: SHAP analysis of factors promoting sales
        sales_preventing_factors: SHAP analysis of factors preventing sales
        
    Returns:
        JSON string with customer analysis and sales recommendations
    """
    try:
        from vertexai.generative_models import GenerativeModel
        
        # Create customer analysis prompt
        prompt = f"""
You are a sales analyst providing insights on customer {customer_id}.

CUSTOMER PROFILE:
{customer_data}

FACTORS PROMOTING SALES:
{sales_promoting_factors}

FACTORS PREVENTING SALES:
{sales_preventing_factors}

ANALYSIS INSTRUCTIONS:
Provide a comprehensive sales analysis including:

1. **SALES OPPORTUNITY ASSESSMENT**
   - Overall opportunity level (Low/Medium/High)
   - Key promoting factors and their impact
   - Specific opportunities that should be pursued

2. **SALES CHALLENGES**
   - Preventing factors that might stop the sale
   - Potential objections to address
   - Barriers to overcome

3. **SALES STRATEGY**
   - Recommended approach (email, call, or both)
   - Best timing for outreach
   - Key messages to emphasize

4. **SPECIFIC RECOMMENDATIONS**
   - Immediate actions to take
   - Long-term relationship building
   - Sales acceleration measures

5. **SUCCESS METRICS**
   - How to measure sales efforts
   - Key indicators to monitor
   - Follow-up schedule

Make recommendations specific and actionable for sales teams.
"""
        
        # Generate analysis using Gemini
        model = GenerativeModel(config.default_model)
        response = model.generate_content(prompt)
        analysis_report = response.text
        
        return json.dumps({
            "success": True,
            "customer_id": customer_id,
            "sales_analysis": analysis_report,
            "analysis_details": {
                "analysis_type": "comprehensive_sales_profile",
                "based_on": "SHAP analysis and customer data",
                "recommendations": "actionable sales strategies"
            },
            "word_count": len(analysis_report.split()),
            "message": "Customer sales analysis completed successfully."
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "customer_id": customer_id,
            "error": str(e),
            "error_type": type(e).__name__
        }, indent=2)