"""
Simplified Visualization Agent for ADK - Shared Tools
Focuses on SQL-to-visualization workflow only
Structure follows simple_sql_agents.py pattern
"""

import json
import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Any
from google.cloud import bigquery
import os

# Global configuration
_project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "energyagentai")
_chart_generator = None

def initialize_chart_generator():
    """Initialize chart generator (call once)"""
    global _chart_generator
    if _chart_generator is None:
        _chart_generator = SimpleChartGenerator()

class SimpleChartGenerator:
    """
    Simple chart generation focused on SQL results visualization
    """
    
    def __init__(self):
        self.business_colors = {
            'primary': '#2E86AB',
            'success': '#10B981',
            'warning': '#F59E0B',
            'danger': '#EF4444',
            'info': '#3B82F6',
            'muted': '#6B7280'
        }

    def create_chart_from_sql_results(self, sql_results_json: str, chart_type: str = "bar", 
                                    title: str = "", x_column: str = "", y_column: str = "") -> str:
        """Create chart directly from SQL query results"""
        try:
            # Parse SQL results (from execute_query_json_tool format)
            results = json.loads(sql_results_json) if isinstance(sql_results_json, str) else sql_results_json
            
            if not results.get('success', False):
                return f"Error: SQL query failed - {results.get('error', 'Unknown error')}"
            
            data = results.get('data', [])
            columns = results.get('columns', [])
            
            if not data or not columns:
                return "Error: No data to visualize"
            
            # Auto-select columns if not specified
            if not x_column:
                # Find first categorical or string column
                for col in columns:
                    sample_val = data[0].get(col) if data else None
                    if sample_val and not isinstance(sample_val, (int, float)):
                        x_column = col
                        break
                if not x_column:
                    x_column = columns[0]
            
            if not y_column:
                # Find first numeric column
                for col in columns:
                    if col != x_column:
                        sample_val = data[0].get(col) if data else None
                        if sample_val and isinstance(sample_val, (int, float)):
                            y_column = col
                            break
                if not y_column:
                    y_column = columns[1] if len(columns) > 1 else columns[0]
            
            # Prepare chart data
            x_values = [row.get(x_column, '') for row in data]
            y_values = [row.get(y_column, 0) for row in data]
            
            # Create chart based on type
            if chart_type == "pie":
                trace = {
                    'type': 'pie',
                    'labels': x_values,
                    'values': y_values,
                    'marker': {'colors': [self.business_colors['primary'], self.business_colors['success'], 
                                         self.business_colors['warning'], self.business_colors['info']]}
                }
            elif chart_type == "line":
                trace = {
                    'type': 'scatter',
                    'mode': 'lines+markers',
                    'x': x_values,
                    'y': y_values,
                    'line': {'color': self.business_colors['primary'], 'width': 3},
                    'marker': {'color': self.business_colors['primary'], 'size': 6}
                }
            elif chart_type == "scatter":
                trace = {
                    'type': 'scatter',
                    'mode': 'markers',
                    'x': x_values,
                    'y': y_values,
                    'marker': {'color': self.business_colors['primary'], 'size': 8}
                }
            else:  # Default to bar
                trace = {
                    'type': 'bar',
                    'x': x_values,
                    'y': y_values,
                    'marker': {'color': self.business_colors['primary']}
                }
            
            # Generate HTML
            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>{title or 'Chart'}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/plotly.js/2.26.0/plotly.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f8f9fa;
        }}
        .chart-container {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .chart-title {{
            font-size: 24px;
            font-weight: 600;
            color: #333;
            margin-bottom: 20px;
            text-align: center;
        }}
        .chart-info {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-size: 14px;
            color: #1565c0;
        }}
    </style>
</head>
<body>
    <div class="chart-container">
        <div class="chart-title">{title or f'{chart_type.title()} Chart'}</div>
        <div class="chart-info">
            📊 <strong>Chart Type:</strong> {chart_type.title()} | 
            📈 <strong>Data Points:</strong> {len(data)} | 
            🔍 <strong>X-Axis:</strong> {x_column} | 
            📊 <strong>Y-Axis:</strong> {y_column}
        </div>
        <div id="chart" style="width:100%;height:500px;"></div>
    </div>

    <script>
        var trace = {json.dumps(trace)};
        
        var layout = {{
            xaxis: {{
                title: '{x_column.replace("_", " ").title()}',
                tickangle: -45
            }},
            yaxis: {{
                title: '{y_column.replace("_", " ").title()}'
            }},
            margin: {{l: 80, r: 30, t: 50, b: 100}},
            plot_bgcolor: '#ffffff',
            paper_bgcolor: '#ffffff'
        }};
        
        var config = {{
            responsive: true,
            displayModeBar: true
        }};
        
        Plotly.newPlot('chart', [trace], layout, config);
    </script>
</body>
</html>
"""
            return html_content
            
        except Exception as e:
            return f"Error creating chart: {str(e)}"

    def create_kpi_cards(self, kpis: List[Dict]) -> str:
        """Create simple KPI cards"""
        cards_html = ""
        for kpi in kpis:
            value = kpi.get('value', 0)
            if isinstance(value, (int, float)):
                if value >= 1000000:
                    formatted_value = f"{value/1000000:.1f}M"
                elif value >= 1000:
                    formatted_value = f"{value/1000:.1f}K"
                else:
                    formatted_value = f"{value:,.0f}"
            else:
                formatted_value = str(value)
            
            trend = kpi.get('trend', 0)
            trend_color = "#10B981" if trend > 0 else "#EF4444" if trend < 0 else "#6B7280"
            trend_arrow = "↗️" if trend > 0 else "↘️" if trend < 0 else "➡️"
            
            cards_html += f"""
            <div style="
                background: white;
                border-radius: 12px;
                padding: 20px;
                margin: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                min-width: 200px;
                text-align: center;
            ">
                <div style="font-size: 24px; margin-bottom: 10px;">{kpi.get('icon', '📊')}</div>
                <div style="font-size: 32px; font-weight: bold; color: #2E86AB; margin-bottom: 5px;">
                    {formatted_value}
                </div>
                <div style="font-size: 16px; font-weight: 600; color: #333; margin-bottom: 5px;">
                    {kpi.get('title', '')}
                </div>
                <div style="font-size: 14px; color: {trend_color};">
                    {trend_arrow} {abs(trend):.1f}%
                </div>
            </div>
            """
        
        return f"""
        <div style="
            display: flex;
            flex-wrap: wrap;
            justify-content: center;
            gap: 10px;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
            margin: 20px 0;
        ">
            {cards_html}
        </div>
        """

# =============================================================================
# SIMPLIFIED ADK TOOL FUNCTIONS
# =============================================================================

def create_chart_from_sql_tool(sql_query: str, chart_type: str = "bar", title: str = "") -> str:
    """
    ADK Tool: Execute SQL and create chart from results
    
    Args:
        sql_query: SQL query to execute
        chart_type: Type of chart (bar, line, pie, scatter)
        title: Chart title
        
    Returns:
        str: HTML string with chart
    """
    global _project_id, _chart_generator
    
    try:
        initialize_chart_generator()
        
        # Execute SQL query
        client = bigquery.Client(project=_project_id)
        cleaned_sql = sql_query.replace('```sql', '').replace('```', '').strip()
        
        print(f"Executing SQL: {cleaned_sql}")
        
        results = client.query(cleaned_sql).to_dataframe()
        
        if results.empty:
            return "<p>No data returned from SQL query.</p>"
        
        # Convert to the expected format
        sql_results = {
            "success": True,
            "data": results.to_dict('records'),
            "columns": list(results.columns),
            "row_count": len(results)
        }
        
        return _chart_generator.create_chart_from_sql_results(
            json.dumps(sql_results), chart_type, title
        )
        
    except Exception as e:
        return f"<p>Error executing SQL and creating chart: {str(e)}</p>"

def create_kpi_dashboard_simple_tool(kpis_json: str) -> str:
    """
    ADK Tool: Create simple KPI dashboard
    
    Args:
        kpis_json: JSON string with KPI data
        Format: [{"title": "Revenue", "value": 150000, "trend": 12.5, "icon": "💰"}]
    
    Returns:
        str: HTML string with KPI dashboard
    """
    global _chart_generator
    
    try:
        initialize_chart_generator()
        kpis = json.loads(kpis_json) if isinstance(kpis_json, str) else kpis_json
        return _chart_generator.create_kpi_cards(kpis)
    except Exception as e:
        return f"<p>Error creating KPI dashboard: {str(e)}</p>"

def create_multiple_charts_tool(sql_query: str, chart_types: str = '["bar", "pie"]') -> str:
    """
    ADK Tool: Execute SQL and create multiple chart types
    
    Args:
        sql_query: SQL query to execute
        chart_types: JSON array of chart types
        
    Returns:
        str: HTML with multiple charts
    """
    try:
        chart_type_list = json.loads(chart_types) if isinstance(chart_types, str) else chart_types
        
        charts = []
        for chart_type in chart_type_list:
            chart_html = create_chart_from_sql_tool(sql_query, chart_type, f"{chart_type.title()} Chart")
            if not chart_html.startswith("<p>Error"):
                charts.append(f'<div style="margin: 20px 0;">{chart_html}</div>')
        
        if not charts:
            return "<p>No charts could be created.</p>"
        
        return f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 12px;">
            <h2 style="text-align: center; color: #333; margin-bottom: 30px;">
                📊 Data Visualization Dashboard
            </h2>
            {''.join(charts)}
        </div>
        """
        
    except Exception as e:
        return f"<p>Error creating multiple charts: {str(e)}</p>"