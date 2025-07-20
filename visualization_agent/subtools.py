import json
import re
from typing import Optional, Dict
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