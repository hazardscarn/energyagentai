"""
Truly Dynamic Alberta Energy AI Visualization Agent - agent.py
Multi-Agent Architecture - Each agent with single tool type
"""

import sys
import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Import SQL tools
from shared_tools.simple_sql_agents import (
    generate_sql_query_tool,
    execute_query_json_tool,
    initialize_sql_components
)

# ADK imports
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.code_executors import BuiltInCodeExecutor
from google.adk.tools import FunctionTool, ToolContext

# Initialize SQL components
initialize_sql_components()

# =============================================================================
# SQL DATA TOOL
# =============================================================================

def get_sql_data(user_request: str, tool_context: ToolContext) -> Dict[str, Any]:
    """Get SQL data and store in state for agents"""
    try:
        print(f"🔍 Getting SQL data for: {user_request}")
        
        # Generate and execute SQL
        sql_result = generate_sql_query_tool(user_request)
        sql_data = json.loads(sql_result)
        
        if not sql_data.get("success"):
            return {"success": False, "error": f"SQL generation failed: {sql_data.get('error')}"}
        
        sql_query = sql_data.get("sql_query")
        query_result = execute_query_json_tool(sql_query)
        query_data = json.loads(query_result)
        
        if not query_data.get("success"):
            return {"success": False, "error": f"Query execution failed: {query_data.get('error')}"}
        
        # Store complete data in state for agents
        tool_context.state['sql_data'] = {
            "data_rows": query_data.get("data", []),
            "columns": query_data.get("columns", []),
            "row_count": query_data.get("row_count", 0),
            "sql_query": sql_query,
            "user_request": user_request
        }
        
        return {
            "success": True,
            "message": f"Retrieved {query_data.get('row_count', 0)} rows with {len(query_data.get('columns', []))} columns",
            "data_preview": query_data.get("data", [])[:3]  # Show first 3 rows for context
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# =============================================================================
# AGENT 1: SQL DATA RETRIEVAL AGENT (TOOLS ONLY)
# =============================================================================

sql_data_agent = LlmAgent(
    name="sql_data_retrieval_agent",
    model="gemini-2.5-pro-preview-05-06",
    description="Retrieves SQL data based on user requests",
    instruction="""You are a SQL Data Retrieval Specialist.

Your job is to:
1. Take the user's natural language request
2. Use the get_sql_data tool to retrieve relevant data
3. Store the data in session state for other agents

Always use the get_sql_data tool with the user's original request.
Provide clear feedback about the data retrieval process.""",
    
    # Only SQL tool - single tool type
    tools=[FunctionTool(get_sql_data)],
    
    # Store result for next agent
    output_key="sql_retrieval_result"
)

# =============================================================================
# AGENT 2: INTELLIGENT VISUALIZATION GENERATOR (PURE AI)
# =============================================================================

visualization_generator = LlmAgent(
    name="intelligent_visualization_generator",
    model="gemini-2.5-pro-preview-05-06",
    description="Creates intelligent Python visualization code by analyzing data and user requirements",
    instruction="""You are an expert data visualization developer with deep knowledge of Python, matplotlib, seaborn, and plotly.

Your job is to analyze the data in state['sql_data'] and the user's request, then generate complete, executable Python visualization code.
MAKE SURE YOU ONLY GENERATE CODE AS OUTPUT AND NOTHING ELSE.
NO EXPLANATIONS, NO TEXT, JUST EXECUTABLE PYTHON CODE.

CRITICAL REQUIREMENT - SELF-CONTAINED CODE:
- The generated code MUST be completely self-contained and executable
- Include the ACTUAL data from state['sql_data']['data_rows'] directly in the code as hardcoded data
- Do NOT use state['sql_data'] in the generated code output
- Create the DataFrame directly from hardcoded data_rows list

ANALYZE THE DATA INTELLIGENTLY:
1. **Data Structure**: Look at columns, data types, row count from state['sql_data']
2. **Data Patterns**: Understand what the data represents  
3. **User Intent**: Parse what visualization they actually want
4. **Best Practices**: Choose optimal chart types for the data

GENERATE SMART CODE STRUCTURE:

    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import numpy as np

    # Data from SQL query (embed actual data here)
    data_rows = [
        {'column1': actual_value1, 'column2': actual_value2},
        {'column1': actual_value3, 'column2': actual_value4},
        # Include ALL actual rows from state['sql_data']['data_rows']
    ]

    # Create DataFrame
    df = pd.DataFrame(data_rows)

    # Your intelligent visualization code here
    plt.show()

EXAMPLES OF INTELLIGENT DECISIONS:

Single row with multiple numeric columns → Bar chart of columns
Time series data → Line charts with trends
Categorical vs numeric → Grouped bar charts or box plots
Distribution requests → Histograms or density plots
Comparison requests → Side-by-side charts

OUTPUT REQUIREMENTS:

*Generate ONLY complete, executable Python code
*Start with necessary imports
*Include the ACTUAL data from state['sql_data']['data_rows'] as hardcoded data_rows = [...]
*Create DataFrame from the hardcoded data: df = pd.DataFrame(data_rows)
*Add appropriate visualizations with professional styling
*Include insights and statistics
*End with plt.show()
*NO explanations, NO text, JUST EXECUTABLE PYTHON CODE
*NO state access in generated code - everything self-contained

*MAKE SURE YOU ONLY GENERATE CODE AS OUTPUT AND NOTHING ELSE.
*NO EXPLANATIONS, NO TEXT, JUST EXECUTABLE PYTHON CODE.

THE CODE MUST BE SELF-CONTAINED WITH HARDCODED DATA FROM state['sql_data']['data_rows'].
Be intelligent about chart selection - analyze the actual data and request to create the perfect visualization.""",
# No tools - pure AI intelligence
output_key="generated_code"
)



# =============================================================================
# AGENT 3: CODE EXECUTION AGENT (CODE EXECUTOR ONLY)
# =============================================================================

# code_executor_agent = LlmAgent(
#     name="code_execution_agent",
#     model="gemini-2.5-pro-preview-05-06",
#     description="Executes Python visualization code generated by other agents",
#     instruction="""You are a Python Code Execution Specialist.

# Your job is to:
# 1. Take the Python code from state['generated_code']
# 2. Execute it using your code execution capability
# 3. Handle any execution errors gracefully

# Always execute the code that was generated by the visualization agent.
# If there are errors, report them clearly.""",
    
#     # Only code executor - single capability type
#     code_executor=BuiltInCodeExecutor(),
    
#     output_key="execution_result"
# )

# =============================================================================
# ROOT COORDINATOR: SEQUENTIAL AGENT (CLEAN & EFFICIENT)
# =============================================================================

root_agent = SequentialAgent(
    name="alberta_energy_viz_coordinator",
    description="Coordinates the complete visualization workflow using specialized agents",
    
    # Sequential execution: SQL → Visualization → Execution
    sub_agents=[
        sql_data_agent,           # Retrieves data using SQL tools
        visualization_generator,   # Generates intelligent code (pure AI)
    ]
)

__version__ = "4.0.0"
__author__ = "Alberta Energy AI Team"
__description__ = "Multi-agent architecture - clean sequential coordination"

__all__ = [
    "root_agent",
    "sql_data_agent",
    "visualization_generator", 
    "code_executor_agent"
]

if __name__ == "__main__":
    print("🚀 Intelligent Alberta Energy AI Visualization Agent")
    print("=" * 60)
    print("✅ Multi-Agent Architecture")
    print("✅ Each agent has single tool type (ADK compatible)")
    print("✅ True AI intelligence for visualization")
    print("✅ No hardcoded plot functions")
    print("✅ SQL → AI Analysis → Code Generation → Execution")
    print("✅ Ready for any visualization request!")