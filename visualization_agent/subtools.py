"""
Enhanced Alberta Energy AI Visualization Agent - subtools.py
Helper functions and utilities (now mostly moved to tools.py)
"""

import json
import re
from typing import Optional, Dict, List, Any

# =============================================================================
# SQL RESPONSE CLEANING UTILITIES
# =============================================================================

def clean_sql_response(raw_response: str) -> str:
    """
    Clean SQL response from Flash models that might include extra formatting.
    
    Args:
        raw_response: Raw response from generate_sql_query_tool
        
    Returns:
        str: Clean SQL query
    """
    # Handle if response is JSON
    if raw_response.strip().startswith('{'):
        try:
            # Try to parse as JSON and extract SQL
            json_data = json.loads(raw_response)
            if 'sql' in json_data:
                return json_data['sql']
            elif 'query' in json_data:
                return json_data['query']
            elif 'sql_query' in json_data:
                return json_data['sql_query']
            else:
                # Look for any value that looks like SQL
                for value in json_data.values():
                    if isinstance(value, str) and 'SELECT' in value.upper():
                        return value
        except json.JSONDecodeError:
            pass
    
    # Handle if response has markdown SQL blocks
    if '```sql' in raw_response:
        # Extract SQL from markdown code block
        sql_match = re.search(r'```sql\s*(.*?)\s*```', raw_response, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
    
    if '```' in raw_response:
        # Extract from any code block
        sql_match = re.search(r'```\s*(.*?)\s*```', raw_response, re.DOTALL)
        if sql_match:
            return sql_match.group(1).strip()
    
    # Remove common prefixes that Flash models might add
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
    
    # Remove quotes if the entire response is quoted
    if response.startswith('"') and response.endswith('"'):
        response = response[1:-1]
    if response.startswith("'") and response.endswith("'"):
        response = response[1:-1]
    
    return response.strip()

def is_valid_sql(sql_query: str) -> bool:
    """
    Basic validation to check if string looks like valid SQL.
    
    Args:
        sql_query: String to validate
        
    Returns:
        bool: True if looks like valid SQL
    """
    if not sql_query or not isinstance(sql_query, str):
        return False
    
    sql_upper = sql_query.upper().strip()
    
    # Check for SQL keywords
    if not sql_upper.startswith('SELECT'):
        return False
    
    # Check for basic SQL structure
    required_keywords = ['SELECT', 'FROM']
    for keyword in required_keywords:
        if keyword not in sql_upper:
            return False
    
    # Check for obvious non-SQL content
    invalid_starts = ['{', '[', '<', 'HTTP']
    for invalid in invalid_starts:
        if sql_query.strip().startswith(invalid):
            return False
    
    return True

# =============================================================================
# CODE EXTRACTION UTILITIES
# =============================================================================

def extract_python_code(text: str) -> str:
    """Extract Python code from agent response"""
    # Try markdown blocks first
    if "```python" in text:
        matches = re.findall(r'```python\s*\n(.*?)\n```', text, re.DOTALL)
        if matches:
            return matches[0].strip()
    
    if "```" in text:
        matches = re.findall(r'```\s*\n(.*?)\n```', text, re.DOTALL)
        for match in matches:
            if any(keyword in match for keyword in ['import ', 'plt.', 'sns.', 'pd.']):
                return match.strip()
    
    # Extract from unformatted text
    lines = text.split('\n')
    code_lines = []
    collecting = False
    
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith(('import ', 'from ', 'data_rows = [')) or 
            any(keyword in stripped for keyword in ['plt.', 'sns.', 'pd.'])):
            collecting = True
            code_lines.append(line)
        elif collecting:
            if (line.strip() == '' or stripped.startswith((' ', '\t', '#')) or
                any(keyword in stripped for keyword in ['plt.', 'sns.', 'pd.', '=', 'df'])):
                code_lines.append(line)
            else:
                break
    
    if code_lines:
        code = '\n'.join(code_lines).strip()
        if len(code) > 20 and any(keyword in code for keyword in ['plt.', 'sns.']):
            return code
    
    return ""

# =============================================================================
# DATA VALIDATION UTILITIES
# =============================================================================

def validate_data_structure(data: Dict[str, Any]) -> bool:
    """
    Validate that data structure contains required fields.
    
    Args:
        data: Data dictionary to validate
        
    Returns:
        bool: True if valid structure
    """
    required_fields = ['data_rows', 'columns', 'row_count']
    
    for field in required_fields:
        if field not in data:
            return False
    
    # Validate data_rows is a list
    if not isinstance(data['data_rows'], list):
        return False
    
    # Validate columns is a list
    if not isinstance(data['columns'], list):
        return False
    
    # Validate row_count is a number
    if not isinstance(data['row_count'], (int, float)):
        return False
    
    return True

def format_data_summary(data: Dict[str, Any]) -> str:
    """
    Create a formatted summary of data structure.
    
    Args:
        data: Data dictionary
        
    Returns:
        str: Formatted summary
    """
    if not validate_data_structure(data):
        return "Invalid data structure"
    
    row_count = data['row_count']
    columns = data['columns']
    sample_rows = data['data_rows'][:3] if data['data_rows'] else []
    
    summary = f"""Data Summary:
- Rows: {row_count:,}
- Columns: {len(columns)} ({', '.join(columns)})
- Sample data: {len(sample_rows)} rows shown
"""
    
    if sample_rows:
        summary += "\nSample rows:\n"
        for i, row in enumerate(sample_rows, 1):
            summary += f"  {i}: {row}\n"
    
    return summary.strip()

# =============================================================================
# ARTIFACT UTILITIES
# =============================================================================

def create_artifact_metadata(
    artifact_type: str,
    filename: str,
    version: int,
    description: str = "",
    **kwargs
) -> Dict[str, Any]:
    """
    Create standardized artifact metadata.
    
    Args:
        artifact_type: Type of artifact (e.g., 'sql_data', 'visualization')
        filename: Artifact filename
        version: Artifact version
        description: Optional description
        **kwargs: Additional metadata fields
        
    Returns:
        Dict containing metadata
    """
    metadata = {
        "artifact_type": artifact_type,
        "filename": filename,
        "version": version,
        "description": description,
        "created_at": None,  # Will be set by calling code
        **kwargs
    }
    
    return metadata

def parse_artifact_filename(filename: str) -> Dict[str, str]:
    """
    Parse artifact filename to extract components.
    
    Args:
        filename: Artifact filename
        
    Returns:
        Dict with parsed components
    """
    # Expected formats:
    # sql_data_20250806_143022.json
    # visualization_20250806_143045_0.png
    
    parts = filename.split('_')
    if len(parts) < 3:
        return {"type": "unknown", "timestamp": "", "index": ""}
    
    artifact_type = '_'.join(parts[:-2])  # Everything except last 2 parts
    timestamp_part = '_'.join(parts[-2:]).split('.')[0]  # Remove extension
    
    # Check if there's an index at the end
    timestamp_parts = timestamp_part.split('_')
    if len(timestamp_parts) == 3:  # date_time_index
        timestamp = '_'.join(timestamp_parts[:2])
        index = timestamp_parts[2]
    else:
        timestamp = timestamp_part
        index = ""
    
    return {
        "type": artifact_type,
        "timestamp": timestamp,
        "index": index,
        "extension": filename.split('.')[-1] if '.' in filename else ""
    }

# =============================================================================
# LEGACY FUNCTIONS (DEPRECATED - Use tools.py instead)
# =============================================================================

# Note: The following functions have been moved to tools.py
# and are kept here only for backward compatibility.
# New code should import from tools.py directly.

async def get_sql_data(*args, **kwargs):
    """DEPRECATED: Use get_sql_data_and_save_artifact from tools.py instead"""
    raise DeprecationWarning("This function has been moved to tools.py. Use get_sql_data_and_save_artifact instead.")

async def execute_python_code(*args, **kwargs):
    """DEPRECATED: Use execute_code_and_save_plots from tools.py instead"""
    raise DeprecationWarning("This function has been moved to tools.py. Use execute_code_and_save_plots instead.")

# =============================================================================
# VERSION INFO
# =============================================================================

__version__ = "6.0.0"
__description__ = "Helper utilities for enhanced multi-agent system"