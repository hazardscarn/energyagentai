"""
Enhanced Alberta Energy AI Visualization Agent - tools.py
Centralized Tools Module with Artifact-Based Data Flow
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
from datetime import datetime
from typing import Dict, Any, Optional
import re

# ADK imports
from google.adk.tools import ToolContext
from google.genai import types
from vertexai.generative_models import GenerativeModel

# SQL tools import
from shared_tools.simple_sql_agents import (
    generate_sql_query_tool,
    execute_query_json_tool,
    initialize_sql_components
)

from .config import vizConfig

config = vizConfig()

# Initialize SQL components
initialize_sql_components()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def clean_sql_response(raw_response: str) -> str:
    """Clean SQL response from Flash models that might include extra formatting"""
    if raw_response.strip().startswith('{'):
        try:
            json_data = json.loads(raw_response)
            if 'sql' in json_data:
                return json_data['sql']
            elif 'query' in json_data:
                return json_data['query']
            elif 'sql_query' in json_data:
                return json_data['sql_query']
            else:
                for value in json_data.values():
                    if isinstance(value, str) and 'SELECT' in value.upper():
                        return value
        except json.JSONDecodeError:
            pass
    
    if '```sql' in raw_response:
        sql_match = re.search(r'```sql\s*(.*?)\s*```', raw_response, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
    
    if '```' in raw_response:
        sql_match = re.search(r'```\s*(.*?)\s*```', raw_response, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
    
    response = raw_response.strip()
    prefixes_to_remove = [
        'Here is the SQL query:',
        'SQL Query:',
        'Query:',
        'The SQL query is:',
        'Here\'s the query:',
    ]
    
    for prefix in prefixes_to_remove:
        if response.startswith(prefix):
            response = response[len(prefix):].strip()
    
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    if response.startswith("'") and response.endswith("'"):
        response = response[1:-1]
    
    return response.strip()

def extract_python_code(text: str) -> str:
    """Extract Python code from agent response"""
    if "```python" in text:
        matches = re.findall(r'```python\s*\n(.*?)\n```', text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    if "```" in text:
        matches = re.findall(r'```\s*\n(.*?)\n```', text, re.DOTALL)
        for match in matches:
            if any(keyword in match for keyword in ['import ', 'plt.', 'sns.', 'pd.']):
                return match.strip()
    
    return ""

# =============================================================================
# TOOL 1: SQL DATA RETRIEVAL & ARTIFACT STORAGE
# =============================================================================

async def get_sql_query(user_request: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate SQL query, execute it, and save data as artifact.
    Store only the SQL query and artifact reference in state.
    """
    try:
        print(f"🔍 Processing SQL request: {user_request}")
        
        # Generate SQL query
        raw_sql_result = generate_sql_query_tool(user_request)
        sql_data = json.loads(raw_sql_result)
        
        if not sql_data.get("success"):
            return {"success": False, "error": f"SQL generation failed: {sql_data.get('error')}"}
        
        # Clean SQL query
        cleaned_sql = clean_sql_response(raw_sql_result)
        print(f"📝 Generated SQL: {cleaned_sql}")
        
        # Execute query
        query_result = execute_query_json_tool(cleaned_sql)
        query_data = json.loads(query_result)
        
        if not query_data.get("success"):
            return {"success": False, "error": f"Query execution failed: {query_data.get('error')}"}
        
        tool_context.state['sql_query']=cleaned_sql
        
        
        return {
            "success": True,
            "message": f"Identified the SQL Query needed to pull data for the plots. That query returns {query_data.get("row_count", 0)} rows of data",
            "sql_query": cleaned_sql
                            }        
    except Exception as e:
        error_msg = f"SQL data retrieval failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

# =============================================================================
# TOOL 2: LOAD ARTIFACT AND GENERATE VISUALIZATION CODE
# =============================================================================

async def create_viz_code_from_query(visualization_request: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Load data artifact and use LLM to generate visualization code.
    Uses a separate LLM call (Flash 2.5) to create optimal visualization code.
    """
    try:
        print(f"🎨 Generating visualization code for: {visualization_request}")

        ##Get the SQL query from state
        cleaned_sql = tool_context.state.get('sql_query')

        # Execute query and get the data
        query_result = execute_query_json_tool(cleaned_sql)
        query_data = json.loads(query_result)

        data_rows= query_data.get("data", [])
        columns= query_data.get("columns", [])
        
        if not query_data.get("success"):
            return {"success": False, "error": f"Query execution failed: {query_data.get('error')}"}

        if not data_rows:
            return {"success": False, "error": "No data rows found"}
        if not columns:
            return {"success": False, "error": "No columns found"}

        # Create prompt for visualization code generation
        code_generation_prompt = f"""You are an expert Python data visualization developer. 

                    USER REQUEST: {visualization_request}

                    AVAILABLE DATA:
                    - Columns: {columns}
                    - All data rows: {json.dumps(data_rows, indent=2)}

                    TASK: Generate complete, executable Python visualization code that creates the best possible plot for the user's request.

                    Key capabilities:
                        - Automatically selects best chart types based on data
                        - Handles different data types (categorical, numerical, temporal)
                        - Creates professional, publication-ready visualizations
                        - Generates complete, self-contained Python code
                        - No additional info other than code generated


                    REQUIREMENTS:
                    1. Include ALL the data provided above in the code as hardcoded data_rows
                    2. Create a DataFrame from this data
                    3. Generate the most appropriate visualization for the user's request
                    4. Use matplotlib/seaborn for plotting with professional styling
                    5. Add proper titles, labels, and formatting
                    6. End with plt.show()

                    MANDATORY CODE STRUCTURE:

                    ```python
                    import pandas as pd
                    import matplotlib.pyplot as plt
                    import seaborn as sns
                    import numpy as np

                    # Data from query
                    data_rows = {json.dumps(data_rows, indent=4)}

                    # Create DataFrame
                    df = pd.DataFrame(data_rows)

                    # Create the visualization (adapt based on user request and data)
                    # ... your visualization code here ...

                    plt.show()
                    ```

                    Generate ONLY the executable Python code. No explanations.
                    """
        
        # Use LLM to generate visualization code
        try:
            
            
            model = GenerativeModel(config.viz_code_model)
            response = model.generate_content(code_generation_prompt)
            
            if not response or not response.text:
                return {"success": False, "error": "Failed to generate visualization code - empty LLM response"}
            
            # Extract code from response
            generated_code = extract_python_code(response.text)
            if not generated_code:
                # If no code blocks found, try using the raw response
                generated_code = response.text.strip()
            
            if not generated_code:
                return {"success": False, "error": "Failed to extract code from LLM response"}
            
            # Store generated code in state
            tool_context.state['generated_code'] = generated_code
            tool_context.state['visualization_request'] = visualization_request
            
            print(f"✅ Generated visualization code ({len(generated_code)} characters)")
            
            return {
                "success": True,
                "message": "Visualization code generated successfully",
                "code": generated_code,
                "code_length": len(generated_code),
                "data_info": f"{len(data_rows)} rows, {len(columns)} columns"
            }
            
        except Exception as e:
            return {"success": False, "error": f"LLM code generation failed: {str(e)}"}
        
    except Exception as e:
        error_msg = f"Code generation failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}

# =============================================================================
# TOOL 3: EXECUTE CODE AND SAVE PLOT ARTIFACTS
# =============================================================================

async def execute_code_and_save_plots(tool_context: ToolContext) -> Dict[str, Any]:
    """
    Execute the generated Python code and save any plots as artifacts.
    """
    try:
        print(f"🚀 Executing visualization code...")
        
        # Get generated code from state
        generated_code = tool_context.state.get('generated_code')
        if not generated_code:
            return {"success": False, "error": "No generated code found in state"}
        
        visualization_request = tool_context.state.get('visualization_request', "Unknown")
        
        # Prepare execution environment
        exec_globals = {
            'pd': pd, 
            'plt': plt, 
            'sns': sns, 
            'np': np, 
            'print': print
        }
        
        # Configure matplotlib for headless execution
        plt.switch_backend('Agg')
        plt.ioff()
        
        # Execute the code
        print(f"📊 Executing code for: {visualization_request}")
        exec(generated_code, exec_globals)
        
        # Force drawing and check for figures
        plt.draw()
        current_figures = plt.get_fignums()
        print(f"📊 Matplotlib figures detected: {current_figures}")
        
        if current_figures:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            saved_artifacts = []
            
            for i, fig_num in enumerate(current_figures):
                fig = plt.figure(fig_num)
                fig.set_size_inches(12, 8)
                
                # Convert to bytes
                img_buffer = BytesIO()
                fig.savefig(
                    img_buffer,
                    format='png',
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='white'
                )
                img_buffer.seek(0)
                plot_bytes = img_buffer.getvalue()
                
                # Save as artifact
                filename = f"visualization_{timestamp}_{i}.png"
                plot_artifact = types.Part.from_bytes(data=plot_bytes, mime_type="image/png")
                
                version = await tool_context.save_artifact(filename=filename, artifact=plot_artifact)
                
                artifact_info = {
                    "filename": filename,
                    "version": version,
                    "size_bytes": len(plot_bytes),
                    "figure_number": i,
                    "visualization_request": visualization_request
                }
                saved_artifacts.append(artifact_info)
                print(f"✅ Plot {i} saved as artifact: {filename} (v{version})")
            
            plt.close('all')
            
            # Store artifacts info in session state
            tool_context.state['plot_artifacts'] = saved_artifacts
            
            return {
                "success": True,
                "artifacts_saved": saved_artifacts,
                "message": f"Successfully executed code and saved {len(saved_artifacts)} plot(s)"
            }
        else:
            print("⚠️ No matplotlib figures detected after code execution")
            return {"success": True, "message": "Code executed but no plots were generated"}
            
    except Exception as e:
        plt.close('all')
        error_msg = f"Code execution failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {"success": False, "error": error_msg}