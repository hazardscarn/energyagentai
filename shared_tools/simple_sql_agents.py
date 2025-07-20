"""
Google ADK Agent with SQL Tools
Using the 3 simple SQL components as tools with similar query examples
"""

from google.adk.agents import Agent
from google.cloud import bigquery
from vertexai.language_models import TextEmbeddingModel
from vertexai.generative_models import GenerativeModel
import json
import pandas as pd
from datetime import datetime


# Global instances to avoid recreating
_sql_developer = None
_project_id = "energyagentai"
_dataset_name = "alberta_energy_ai"

def initialize_sql_components():
    """Initialize SQL components (call once)"""
    global _sql_developer
    if _sql_developer is None:
        _sql_developer = SQLQueryDeveloper(_project_id, _dataset_name)

class SQLQueryDeveloper:
    """Agent that develops SQL queries from natural language"""
    
    def __init__(self, project_id: str, dataset_name: str):
        self.project_id = project_id
        self.dataset_name = dataset_name
        self.client = bigquery.Client(project=project_id)
        self.embedding_model = TextEmbeddingModel.from_pretrained('text-embedding-005')
        self.llm = GenerativeModel("gemini-2.5-flash")
    
    def get_embedding(self, text: str):
        """Generate embedding for text"""
        embeddings = self.embedding_model.get_embeddings([text])
        return embeddings[0].values
    
    def search_schema(self, user_question: str):
        """Search for relevant tables and columns"""
        try:
            user_embedding = self.get_embedding(user_question)
            
            # Get table matches
            table_sql = f"""
            SELECT base.content as table_content 
            FROM vector_search(
                TABLE `{self.project_id}.{self.dataset_name}.table_details_embeddings`, 
                "embedding", 
                (SELECT {user_embedding} as qe), 
                top_k=> 5, 
                distance_type=>"COSINE"
            ) 
            WHERE 1-distance > 0.3
            """
            
            # Get column matches  
            column_sql = f"""
            SELECT base.content as column_content 
            FROM vector_search(
                TABLE `{self.project_id}.{self.dataset_name}.tablecolumn_details_embeddings`, 
                "embedding", 
                (SELECT {user_embedding} as qe), 
                top_k=> 10, 
                distance_type=>"COSINE"
            ) 
            WHERE 1-distance > 0.3
            """
            
            # Execute queries
            table_results = self.client.query(table_sql).to_dataframe()
            column_results = self.client.query(column_sql).to_dataframe()
            
            table_info = "\n".join(table_results["table_content"].tolist()) if len(table_results) > 0 else "No tables found"
            column_info = "\n".join(column_results["column_content"].tolist()) if len(column_results) > 0 else "No columns found"
            
            return table_info, column_info
            
        except Exception as e:
            return f"Error: {str(e)}", f"Error: {str(e)}"

    def search_similar_queries(self, user_question: str):
        """Search for similar SQL query examples"""
        try:
            user_embedding = self.get_embedding(user_question)
            
            # Search for similar SQL examples from the known good queries
            similar_sql = f"""
            SELECT 
                base.example_user_question,
                base.example_generated_sql,
                (1-distance) as similarity_score
            FROM vector_search(
                TABLE `{self.project_id}.{self.dataset_name}.example_prompt_sql_embeddings`, 
                "embedding", 
                (SELECT {user_embedding} as qe), 
                top_k=> 5, 
                distance_type=>"COSINE"
            ) 
            WHERE 1-distance > 0.2
            ORDER BY similarity_score DESC
            """
            
            # Execute query
            similar_results = self.client.query(similar_sql).to_dataframe()
            
            if len(similar_results) > 0:
                # Format similar queries for the prompt
                similar_examples = []
                for _, row in similar_results.iterrows():
                    similarity_pct = round(row['similarity_score'] * 100, 1)
                    example = f"""Question: {row['example_user_question']}
SQL: {row['example_generated_sql']}
(Similarity: {similarity_pct}%)"""
                    similar_examples.append(example)
                
                return "\n\n".join(similar_examples)
            else:
                return "No similar query examples found"
                
        except Exception as e:
            return f"Error searching similar queries: {str(e)}"

    def generate_sql(self, user_question: str) -> str:
        """Generate SQL query from natural language question"""
        try:
            # Search for relevant schema
            table_info, column_info = self.search_schema(user_question)
            
            # Search for similar SQL examples
            similar_queries = self.search_similar_queries(user_question)
            
            # Create enhanced SQL generation prompt
            sql_prompt = f"""
You are an expert SQL analyst for Alberta Energy AI. Generate a precise BigQuery SQL query based on the user question, available schema, and similar query examples.

REQUIREMENTS:
- Use only the tables and columns provided in the schema
- Follow BigQuery SQL syntax exactly
- Include appropriate WHERE clauses for filtering
- Use proper JOIN syntax when needed
- Learn from the similar query examples below but adapt for the current question
- Return ONLY the SQL query, no explanations or formatting
- Use the full table path format: `energyagentai.alberta_energy_ai.table_name`
- Make sure when you filter for categrical columns, you convert them to lower case using LOWER(column_name) = 'value' for case-insensitive matching
- Be aware of the case sensitivity of BigQuery, especially for string comparisons
- DO NOT add unnecessary formatting like triple backticks or SQL tags

AVAILABLE TABLES:
{table_info}

AVAILABLE COLUMNS:
{column_info}

SIMILAR QUERY EXAMPLES (for reference and pattern learning):
{similar_queries}

USER QUESTION: {user_question}

Based on the schema and learning from similar examples above, generate the SQL query:
"""
            
            # Generate SQL using LLM
            response = self.llm.generate_content(sql_prompt)
            generated_sql = response.candidates[0].text.strip()
            
            # Clean the SQL
            generated_sql = generated_sql.replace('```sql', '').replace('```', '').strip()

            # print(sql_prompt)
            print(f"Generated SQL: {generated_sql}")
            
            return generated_sql
            
        except Exception as e:
            raise Exception(f"Error generating SQL: {str(e)}")

# ADK Tool Functions
def generate_sql_query_tool(user_question: str) -> str:
    """
    ADK Tool: Generate SQL query from natural language
    
    Args:
        user_question: Natural language question about data
        
    Returns:
        JSON string with generated SQL query
    """
    global _sql_developer
    
    try:
        initialize_sql_components()
        sql_query = _sql_developer.generate_sql(user_question)
        print(f"Generated SQL: {sql_query}")
        
        return json.dumps({
            "success": True,
            "sql_query": sql_query,
            "user_question": user_question,
            "message": "SQL query generated successfully using similar query examples. Use execute_query tools to run it."
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "user_question": user_question
        }, indent=2)

def execute_query_dataframe_tool(sql_query: str) -> str:
    """
    ADK Tool: Execute SQL query and return DataFrame info

    
    Args:
        sql_query: SQL query to execute
        
    Returns:
        JSON string with DataFrame information and sample data
    """
    global _project_id
    
    def convert_to_json_safe(value):
        """Convert any value to JSON-safe format, handling all date/datetime types including NaT"""
        import numpy as np
        from datetime import datetime, date, time
        
        # Handle None/NaN values first
        if value is None:
            return None
        
        # Handle pandas NaT (Not a Time) values
        if pd.isna(value):
            return None
        
        # Handle regular NaN values for floats
        if isinstance(value, float) and np.isnan(value):
            return None
        
        # Handle pandas/numpy datetime types (but check for NaT first)
        elif hasattr(value, 'strftime'):
            try:
                return value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'hour') else value.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                # This catches NaT values that have strftime but can't use it
                return None
        
        # Handle pandas Timestamp
        elif hasattr(value, 'to_pydatetime'):
            try:
                return value.to_pydatetime().strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                return None
        
        # Handle numpy types
        elif isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(value)
        elif isinstance(value, (np.floating, np.float64, np.float32, np.float16)):
            return float(value)
        elif isinstance(value, np.bool_):
            return bool(value)
        
        # Handle regular Python types
        elif isinstance(value, (int, float, bool, str)):
            return value
        
        # Convert everything else to string
        else:
            return str(value)
    
    try:
        client = bigquery.Client(project=_project_id)
        
        # Clean SQL
        cleaned_sql = sql_query.replace('```sql', '').replace('```', '').strip()
        
        # Execute query
        results = client.query(cleaned_sql).to_dataframe()
        
        # Convert sample data to JSON-safe format
        sample_df = results.head(5).copy()
        
        # Apply conversion to all columns in sample data
        sample_data = []
        for _, row in sample_df.iterrows():
            json_safe_row = {}
            for column, value in row.items():
                json_safe_row[column] = convert_to_json_safe(value)
            sample_data.append(json_safe_row)
        
        # Get improved data type information
        data_types = {}
        for col in results.columns:
            dtype_str = str(results[col].dtype)
            if 'datetime' in dtype_str:
                data_types[col] = 'datetime'
            elif 'int' in dtype_str:
                data_types[col] = 'integer'
            elif 'float' in dtype_str:
                data_types[col] = 'float'
            elif 'bool' in dtype_str:
                data_types[col] = 'boolean'
            elif 'object' in dtype_str:
                data_types[col] = 'string'
            else:
                data_types[col] = dtype_str
        
        return json.dumps({
            "success": True,
            "sql_executed": cleaned_sql,
            "dataframe_info": {
                "row_count": len(results),
                "column_count": len(results.columns),
                "columns": list(results.columns),
                "data_types": data_types,
                "memory_usage_mb": round(results.memory_usage(deep=True).sum() / 1024 / 1024, 2)
            },
            "sample_data": sample_data,
            "message": f"DataFrame created with {len(results)} rows and {len(results.columns)} columns"
        }, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "sql_attempted": sql_query
        }, indent=2)

def execute_query_json_tool(sql_query: str) -> str:
    """
    ADK Tool: Execute SQL query and return complete results as JSON

    
    Args:
        sql_query: SQL query to execute
        
    Returns:
        JSON string with complete query results
    """
    global _project_id
    
    def convert_to_json_safe(value):
        """Convert any value to JSON-safe format, handling all date/datetime types including NaT"""
        import numpy as np
        from datetime import datetime, date, time
        
        # Handle None/NaN values first
        if value is None:
            return None
        
        # Handle pandas NaT (Not a Time) values
        if pd.isna(value):
            return None
        
        # Handle regular NaN values for floats
        if isinstance(value, float) and np.isnan(value):
            return None
        
        # Handle pandas/numpy datetime types (but check for NaT first)
        elif hasattr(value, 'strftime'):
            try:
                return value.strftime('%Y-%m-%d %H:%M:%S') if hasattr(value, 'hour') else value.strftime('%Y-%m-%d')
            except (ValueError, AttributeError):
                # This catches NaT values that have strftime but can't use it
                return None
        
        # Handle pandas Timestamp
        elif hasattr(value, 'to_pydatetime'):
            try:
                return value.to_pydatetime().strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, AttributeError):
                return None
        
        # Handle numpy integers
        elif isinstance(value, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(value)
        
        # Handle numpy floats
        elif isinstance(value, (np.floating, np.float64, np.float32, np.float16)):
            return float(value)
        
        # Handle numpy booleans
        elif isinstance(value, np.bool_):
            return bool(value)
        
        # Handle regular Python types
        elif isinstance(value, (int, float, bool, str)):
            return value
        
        # Convert everything else to string as fallback
        else:
            return str(value)
    
    try:
        client = bigquery.Client(project=_project_id)
        
        # Clean SQL
        cleaned_sql = sql_query.replace('```sql', '').replace('```', '').strip()
        
        # Execute query
        results = client.query(cleaned_sql).to_dataframe()
        
        # Convert DataFrame to JSON-safe format using improved conversion
        json_safe_data = []
        
        for _, row in results.iterrows():
            json_safe_row = {}
            for column, value in row.items():
                json_safe_row[column] = convert_to_json_safe(value)
            json_safe_data.append(json_safe_row)
        
        # Get column information with proper type handling
        column_info = {}
        for col in results.columns:
            dtype_str = str(results[col].dtype)
            # Simplify dtype names for readability
            if 'datetime' in dtype_str:
                column_info[col] = 'datetime'
            elif 'int' in dtype_str:
                column_info[col] = 'integer'
            elif 'float' in dtype_str:
                column_info[col] = 'float'
            elif 'bool' in dtype_str:
                column_info[col] = 'boolean'
            elif 'object' in dtype_str:
                column_info[col] = 'string'
            else:
                column_info[col] = dtype_str
        
        # Convert to JSON
        result = {
            "success": True,
            "sql_executed": cleaned_sql,
            "row_count": len(results),
            "column_count": len(results.columns),
            "columns": list(results.columns),
            "column_types": column_info,
            "data": json_safe_data,
            "message": f"Query executed successfully. Returned {len(results)} rows."
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "sql_attempted": sql_query
        }, indent=2)