from google.adk.agents import Agent, SequentialAgent
from google.cloud import bigquery
import json
import pandas as pd
def calculate_clv_from_query_results_tool_simple(sql_query: str) -> str:
    """
    ADK Tool: Calculate CLV from SQL query results
    
    Args:
        sql_query (str): SQL query that returns customer data
    
    Returns:
        str: CLV analysis results
    """
    try:

        _project_id = "energyagentai"
        client = bigquery.Client(project=_project_id)
        cleaned_sql = sql_query.replace('```sql', '').replace('```', '').strip()
        df = client.query(cleaned_sql).to_dataframe()
        
        if len(df) == 0:
            return "No customers found matching the query criteria"
        
        # Check for required columns
        required_columns = ["customer_id", "annual_income", "monthly_usage_kwh", "satisfaction_score"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            return f"Missing required columns for CLV calculation: {missing_columns}"
        
        # CLV calculation
        df['satisfaction_factor'] = df['satisfaction_score'] * 0.1 / 5
        df['annual_usage_kwh'] = df['monthly_usage_kwh'] * 12
        df['clv'] = df['annual_usage_kwh'] * df['satisfaction_factor']
        
        # Calculate stats
        avg_clv = df['clv'].mean()
        total_clv = df['clv'].sum()
        num_customers = len(df)
        
        report = f"""
## CLV Analysis Results

**Total Customers:** {num_customers}
**Average CLV:** ${avg_clv:.2f}
**Total CLV:** ${total_clv:.2f}

**Top 5 Customers by CLV:**
{df.nlargest(5, 'clv')[['customer_id', 'clv']].to_string(index=False)}
"""
        
        return report
        
    except Exception as e:
        return f"Error calculating CLV: {str(e)}"