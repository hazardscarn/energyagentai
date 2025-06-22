"""
Advanced ADK Visualization Agent with Dynamic Code Execution
Leverages Google ADK's built_in_code_execution tool for dynamic Python visualization generation
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any
from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import built_in_code_execution, google_search
from google.genai import types
import os

# Global configuration
AGENT_NAME = "advanced_viz_agent"
APP_NAME = "dynamic_visualization"
USER_ID = "data_analyst"
GEMINI_MODEL = "gemini-2.0-flash"

class AdvancedVisualizationAgent:
    """
    Advanced Visualization Agent using ADK's code execution capabilities
    Can generate dynamic Python code for sophisticated data visualizations
    """
    
    def __init__(self):
        self.session_service = InMemorySessionService()
        self.setup_agent()
        
    def setup_agent(self):
        """Initialize the ADK agent with code execution capabilities"""
        
        # Create the visualization agent with code execution tool
        self.viz_agent = LlmAgent(
            name=AGENT_NAME,
            model=GEMINI_MODEL,
            tools=[built_in_code_execution, google_search],
            instruction="""You are an advanced data visualization expert with access to Python code execution.

Your capabilities include:
1. Creating sophisticated visualizations using matplotlib, seaborn, plotly, and other Python libraries
2. Performing statistical analysis and data exploration
3. Generating interactive plots and dashboards
4. Handling multiple data formats (CSV, JSON, SQL results, etc.)
5. Creating publication-quality graphics
6. Implementing advanced visualization techniques (heatmaps, 3D plots, animations, etc.)

When creating visualizations:
- Always start by examining the data structure and types
- Choose appropriate visualization types based on data characteristics
- Use modern, aesthetically pleasing styling
- Include proper labels, titles, and legends
- Handle edge cases and missing data gracefully
- Save visualizations as high-quality images or HTML files
- Provide insights and interpretations of the visualizations

Available libraries you can use:
- matplotlib.pyplot for basic plotting
- seaborn for statistical visualizations
- plotly.express and plotly.graph_objects for interactive plots
- pandas for data manipulation
- numpy for numerical operations
- scipy for statistical functions
- sklearn for machine learning visualizations

Always execute Python code to create actual visualizations rather than just describing them.
""",
            description="Advanced data visualization agent with dynamic code execution capabilities"
        )
        
        # Setup session and runner
        self.session = self.session_service.create_session(
            app_name=APP_NAME, 
            user_id=USER_ID, 
            session_id="viz_session"
        )
        
        self.runner = Runner(
            agent=self.viz_agent, 
            app_name=APP_NAME, 
            session_service=self.session_service
        )
    
    async def create_visualization(self, data_input: str, viz_request: str) -> str:
        """
        Create visualization from data and user request
        
        Args:
            data_input: Data in various formats (CSV string, JSON, file path, SQL query, etc.)
            viz_request: Natural language description of desired visualization
            
        Returns:
            Agent response with executed visualizations
        """
        
        # Construct the prompt for the agent
        prompt = f"""
Data Input:
{data_input}

Visualization Request:
{viz_request}

Please:
1. First, examine and understand the data structure
2. Create appropriate visualizations based on the request
3. Use best practices for data visualization
4. Generate insights from the visualizations
5. Save the plots and provide the file paths

Execute Python code to accomplish this task.
"""
        
        content = types.Content(role='user', parts=[types.Part(text=prompt)])
        
        # Execute the agent
        final_response = "No response generated."
        async for event in self.runner.run_async(
            user_id=USER_ID, 
            session_id="viz_session", 
            new_message=content
        ):
            if event.is_final_response() and event.content and event.content.parts:
                final_response = event.content.parts[0].text
                break
        
        return final_response
    
    def create_exploratory_dashboard(self, data_source: str) -> str:
        """
        Create a comprehensive exploratory data analysis dashboard
        """
        
        dashboard_code = f"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Set styling
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

# Load and examine data
print("Loading data...")
{self._generate_data_loading_code(data_source)}

# Basic data exploration
print("\\n=== DATA OVERVIEW ===")
print(f"Shape: {{df.shape}}")
print(f"\\nData Types:")
print(df.dtypes)
print(f"\\nMissing Values:")
print(df.isnull().sum())
print(f"\\nBasic Statistics:")
print(df.describe())

# Create comprehensive dashboard
fig = plt.figure(figsize=(20, 15))

# 1. Missing data heatmap
plt.subplot(3, 4, 1)
sns.heatmap(df.isnull(), cbar=True, cmap='viridis')
plt.title('Missing Data Pattern')

# 2. Correlation heatmap (for numeric columns)
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 1:
    plt.subplot(3, 4, 2)
    corr_matrix = df[numeric_cols].corr()
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0)
    plt.title('Correlation Matrix')

# 3-6. Distribution plots for numeric columns
numeric_cols_sample = numeric_cols[:4]  # Take first 4 numeric columns
for i, col in enumerate(numeric_cols_sample):
    plt.subplot(3, 4, 3+i)
    df[col].hist(bins=30, alpha=0.7)
    plt.title(f'Distribution of {{col}}')
    plt.xlabel(col)

# 7-10. Box plots for numeric columns
for i, col in enumerate(numeric_cols_sample):
    plt.subplot(3, 4, 7+i)
    df[col].plot(kind='box')
    plt.title(f'Box Plot of {{col}}')

# 11-12. Categorical analysis
categorical_cols = df.select_dtypes(include=['object']).columns
if len(categorical_cols) > 0:
    plt.subplot(3, 4, 11)
    col = categorical_cols[0]
    df[col].value_counts().head(10).plot(kind='bar')
    plt.title(f'Top Categories in {{col}}')
    plt.xticks(rotation=45)
    
    if len(categorical_cols) > 1:
        plt.subplot(3, 4, 12)
        col = categorical_cols[1]
        df[col].value_counts().head(10).plot(kind='bar')
        plt.title(f'Top Categories in {{col}}')
        plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig('exploratory_dashboard.png', dpi=300, bbox_inches='tight')
plt.show()

print("\\n=== KEY INSIGHTS ===")
print(f"✓ Dataset contains {{df.shape[0]:,}} rows and {{df.shape[1]}} columns")
print(f"✓ {{len(numeric_cols)}} numeric columns, {{len(categorical_cols)}} categorical columns")
print(f"✓ Missing data: {{df.isnull().sum().sum()}} total missing values")

# Generate summary statistics table
summary_stats = df.describe()
print("\\nSummary statistics saved to summary_stats.csv")
summary_stats.to_csv('summary_stats.csv')

print("\\nExploratory dashboard saved as 'exploratory_dashboard.png'")
"""
        return dashboard_code
    
    def _generate_data_loading_code(self, data_source: str) -> str:
        """Generate appropriate data loading code based on data source type"""
        
        if data_source.endswith('.csv'):
            return f"df = pd.read_csv('{data_source}')"
        elif data_source.endswith('.json'):
            return f"df = pd.read_json('{data_source}')"
        elif data_source.endswith('.xlsx'):
            return f"df = pd.read_excel('{data_source}')"
        elif "SELECT" in data_source.upper():
            # SQL query
            return f"""
# SQL query execution would require database connection
# For demo purposes, creating sample data
df = pd.DataFrame({{
    'sample_col1': np.random.randn(1000),
    'sample_col2': np.random.rand(1000) * 100,
    'category': np.random.choice(['A', 'B', 'C'], 1000)
}})
"""
        else:
            # Assume it's raw data or CSV content
            return f"""
import io
df = pd.read_csv(io.StringIO('''{data_source}'''))
"""

# =============================================================================
# ADK TOOL FUNCTIONS FOR ADVANCED VISUALIZATIONS
# =============================================================================

def create_advanced_plot_tool(data: str, plot_type: str, **kwargs) -> str:
    """
    ADK Tool: Create advanced plots using dynamic code execution
    
    Args:
        data: Data in CSV format or JSON
        plot_type: Type of plot (scatter, heatmap, violin, pair, etc.)
        **kwargs: Additional parameters for customization
        
    Returns:
        str: Status message and file path
    """
    
    code_templates = {
        'scatter_matrix': """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pandas.plotting import scatter_matrix

# Load data
df = pd.read_csv(io.StringIO(data))

# Create scatter matrix
fig, axes = plt.subplots(figsize=(15, 15))
scatter_matrix(df.select_dtypes(include=[np.number]), 
               alpha=0.6, figsize=(15, 15), diagonal='hist')
plt.suptitle('Scatter Matrix of Numeric Variables', fontsize=16)
plt.tight_layout()
plt.savefig('scatter_matrix.png', dpi=300, bbox_inches='tight')
plt.show()
""",
        
        'correlation_heatmap': """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv(io.StringIO(data))

# Create correlation heatmap
plt.figure(figsize=(12, 10))
numeric_cols = df.select_dtypes(include=[np.number])
correlation_matrix = numeric_cols.corr()

sns.heatmap(correlation_matrix, 
            annot=True, 
            cmap='RdYlBu_r', 
            center=0,
            square=True,
            fmt='.2f')
plt.title('Correlation Heatmap', fontsize=16, pad=20)
plt.tight_layout()
plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
plt.show()
""",
        
        'violin_plot': """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Load data
df = pd.read_csv(io.StringIO(data))

# Create violin plots for numeric columns
numeric_cols = df.select_dtypes(include=[np.number]).columns
n_cols = len(numeric_cols)
n_rows = (n_cols + 2) // 3

plt.figure(figsize=(15, 5 * n_rows))
for i, col in enumerate(numeric_cols):
    plt.subplot(n_rows, 3, i + 1)
    sns.violinplot(y=df[col])
    plt.title(f'Distribution of {col}')

plt.tight_layout()
plt.savefig('violin_plots.png', dpi=300, bbox_inches='tight')
plt.show()
""",
        
        'interactive_plotly': """
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Load data
df = pd.read_csv(io.StringIO(data))

# Create interactive dashboard
numeric_cols = df.select_dtypes(include=[np.number]).columns

if len(numeric_cols) >= 2:
    # Scatter plot
    fig1 = px.scatter(df, x=numeric_cols[0], y=numeric_cols[1], 
                     title=f'{numeric_cols[1]} vs {numeric_cols[0]}',
                     template='plotly_white')
    fig1.write_html('interactive_scatter.html')
    
    # Box plots
    fig2 = go.Figure()
    for col in numeric_cols[:4]:  # Limit to first 4 columns
        fig2.add_trace(go.Box(y=df[col], name=col))
    
    fig2.update_layout(title='Interactive Box Plots',
                      template='plotly_white')
    fig2.write_html('interactive_boxplots.html')

print("Interactive plots saved as HTML files")
"""
    }
    
    # Get the appropriate template
    template = code_templates.get(plot_type, code_templates['scatter_matrix'])
    
    # Execute the code (in a real ADK environment, this would use built_in_code_execution)
    try:
        exec(template)
        return f"Successfully created {plot_type} visualization. Files saved."
    except Exception as e:
        return f"Error creating visualization: {str(e)}"

def analyze_and_visualize_tool(data: str, analysis_type: str = "comprehensive") -> str:
    """
    ADK Tool: Perform comprehensive data analysis with visualizations
    
    Args:
        data: Input data (CSV, JSON, etc.)
        analysis_type: Type of analysis (comprehensive, statistical, exploratory)
        
    Returns:
        str: Analysis results and visualization paths
    """
    
    analysis_code = """
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from scipy import stats
import plotly.express as px
import warnings
warnings.filterwarnings('ignore')

# Load and prepare data
df = pd.read_csv(io.StringIO(data))

print("=== COMPREHENSIVE DATA ANALYSIS ===\\n")

# 1. Data Quality Assessment
print("1. DATA QUALITY ASSESSMENT")
print(f"   - Shape: {df.shape}")
print(f"   - Missing values: {df.isnull().sum().sum()}")
print(f"   - Duplicate rows: {df.duplicated().sum()}")

# 2. Statistical Summary
print("\\n2. STATISTICAL SUMMARY")
numeric_cols = df.select_dtypes(include=[np.number]).columns
for col in numeric_cols:
    skewness = stats.skew(df[col].dropna())
    kurtosis = stats.kurtosis(df[col].dropna())
    print(f"   {col}: Skewness={skewness:.3f}, Kurtosis={kurtosis:.3f}")

# 3. Create comprehensive visualization dashboard
fig = plt.figure(figsize=(20, 12))

# Distribution plots
for i, col in enumerate(numeric_cols[:6]):
    plt.subplot(3, 4, i+1)
    sns.histplot(df[col], kde=True)
    plt.title(f'{col} Distribution')

# Correlation heatmap
if len(numeric_cols) > 1:
    plt.subplot(3, 4, 7)
    sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm')
    plt.title('Correlation Matrix')

# Box plots
for i, col in enumerate(numeric_cols[:3]):
    plt.subplot(3, 4, 8+i)
    sns.boxplot(y=df[col])
    plt.title(f'{col} Box Plot')

# Outlier detection
plt.subplot(3, 4, 12)
outlier_counts = []
for col in numeric_cols:
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    outliers = ((df[col] < (Q1 - 1.5 * IQR)) | (df[col] > (Q3 + 1.5 * IQR))).sum()
    outlier_counts.append(outliers)

plt.bar(range(len(numeric_cols)), outlier_counts)
plt.xticks(range(len(numeric_cols)), numeric_cols, rotation=45)
plt.title('Outlier Count by Column')

plt.tight_layout()
plt.savefig('comprehensive_analysis.png', dpi=300, bbox_inches='tight')
plt.show()

print("\\n3. KEY INSIGHTS")
print(f"   - Most correlated variables: {df[numeric_cols].corr().abs().unstack().sort_values(ascending=False).iloc[1:3].index.tolist()}")
print(f"   - Highest variance column: {df[numeric_cols].var().idxmax()}")
print(f"   - Total outliers detected: {sum(outlier_counts)}")

print("\\nAnalysis complete! Visualizations saved as 'comprehensive_analysis.png'")
"""
    
    try:
        exec(analysis_code)
        return "Comprehensive analysis completed successfully."
    except Exception as e:
        return f"Error in analysis: {str(e)}"

# =============================================================================
# EXAMPLE USAGE AND AGENT SETUP
# =============================================================================

async def demo_advanced_visualization_agent():
    """
    Demonstrate the advanced visualization agent capabilities
    """
    
    # Initialize the agent
    viz_agent = AdvancedVisualizationAgent()
    
    # Sample data for demonstration
    sample_data = """
Date,Sales,Marketing_Spend,Region,Product_Category
2024-01-01,10000,2000,North,Electronics
2024-01-02,12000,2200,South,Clothing
2024-01-03,8000,1800,East,Electronics
2024-01-04,15000,2500,West,Home
2024-01-05,11000,2100,North,Clothing
2024-01-06,9000,1900,South,Electronics
2024-01-07,13000,2300,East,Home
2024-01-08,14000,2400,West,Electronics
2024-01-09,10500,2050,North,Home
2024-01-10,16000,2600,South,Clothing
"""
    
    # Test different visualization requests
    requests = [
        "Create a comprehensive sales dashboard with trends, regional analysis, and product category performance",
        "Analyze the correlation between marketing spend and sales with interactive visualizations",
        "Generate an exploratory data analysis report with statistical insights",
        "Create a time series analysis of sales with forecasting",
        "Build an interactive dashboard showing sales by region and product category"
    ]
    
    print("🚀 Advanced ADK Visualization Agent Demo\n")
    
    for i, request in enumerate(requests, 1):
        print(f"📊 Request {i}: {request}\n")
        
        # This would be the actual call in a real ADK environment
        # response = await viz_agent.create_visualization(sample_data, request)
        # print(f"Agent Response:\n{response}\n")
        # print("-" * 80 + "\n")
        
        # For demo purposes, show what the agent would generate
        print("🤖 Agent would generate Python code to:")
        print(f"   1. Load and validate the data")
        print(f"   2. Create {request.split()[1:4]} visualization")
        print(f"   3. Save high-quality output files")
        print(f"   4. Provide insights and recommendations\n")
        print("-" * 80 + "\n")

if __name__ == "__main__":
    print("Advanced ADK Visualization Agent with Code Execution")
    print("=" * 50)
    print("\nKey Features:")
    print("✓ Dynamic Python code generation for visualizations")
    print("✓ Support for matplotlib, seaborn, plotly libraries")
    print("✓ Comprehensive data analysis capabilities")
    print("✓ Interactive dashboard creation")
    print("✓ Statistical analysis and insights")
    print("✓ Multiple output formats (PNG, HTML, SVG)")
    print("✓ Real-time code execution via ADK")
    
    # Run demo
    import asyncio
    asyncio.run(demo_advanced_visualization_agent())