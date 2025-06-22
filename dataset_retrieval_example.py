# working_example.py
"""
Simple working example showing dataset retrieval for further analysis
"""

from fixed_separated_sql_agent import create_fixed_sql_agent
from vertexai.preview.reasoning_engines import AdkApp
import pandas as pd
import json

def main():
    """Simple example: Get customer data and analyze it immediately"""
    
    PROJECT_ID = "energyagentai"
    DATASET_NAME = "alberta_energy_ai"
    
    print("🚀 Simple Immediate Dataset Access Example")
    print("="*50)
    
    # Create agent - now with immediate access, no persistent storage
    agent, sql_tools = create_fixed_sql_agent(PROJECT_ID, DATASET_NAME)
    app = AdkApp(agent=agent)
    
    # Example 1: Get specific customer data
    print("\n📊 Getting specific customer data...")
    
    for event in app.stream_query(
        user_id="example_1", 
        message="Give me all the data for customer CUST00000001"
    ):
        # Look for successful completion in response
        if 'content' in event and 'parts' in event['content']:
            for part in event['content']['parts']:
                if 'function_response' in part:
                    try:
                        response_data = json.loads(part['function_response']['response']['result'])
                        if response_data.get('success') and 'complete_data' in response_data:
                            print(f"✅ Query executed successfully!")
                            print(f"📏 Dataset: {response_data['dataset_info']['row_count']} rows, {response_data['dataset_info']['column_count']} columns")
                    except:
                        pass
    
    # Now access the actual DataFrame immediately
    try:
        print(f"\n🔬 Analyzing the retrieved data...")
        
        # Get the full DataFrame - no dataset ID needed!
        df = sql_tools.get_current_dataset()
        
        print(f"📏 Dataset shape: {df.shape}")
        print(f"📐 Columns: {list(df.columns)}")
        
        # Do some analysis
        print(f"\n📈 Analysis Results:")
        if 'annual_income' in df.columns:
            print(f"   💰 Annual Income: ${df['annual_income'].iloc[0]:,}")
        if 'city' in df.columns:
            print(f"   🏙️  City: {df['city'].iloc[0]}")
        if 'monthly_usage_kwh' in df.columns:
            print(f"   ⚡ Monthly Usage: {df['monthly_usage_kwh'].iloc[0]:,} kWh")
        if 'is_churned' in df.columns:
            print(f"   📊 Churn Status: {'Churned' if df['is_churned'].iloc[0] else 'Active'}")
        
        # Show first few columns of the data
        print(f"\n📋 Sample Data:")
        print(df.head(1).to_string())
        
        # This DataFrame is now ready for further analysis!
        print(f"\n✅ SUCCESS: You have immediate access to the full pandas DataFrame!")
        print(f"   Memory usage: {df.memory_usage(deep=True).sum() / 1024 / 1024:.2f} MB")
        
        # Clear from memory when done (optional)
        print(f"\n🗑️  {sql_tools.clear_current_dataset()}")
        
    except Exception as e:
        print(f"❌ Error accessing dataset: {e}")
    
    # Example 2: Get a summary answer (not dataset)
    print(f"\n" + "="*50)
    print("📈 Getting summary answer...")
    
    for event in app.stream_query(
        user_id="example_2",
        message="How many customers are there in total?"
    ):
        if 'content' in event and 'parts' in event['content']:
            for part in event['content']['parts']:
                if 'text' in part:
                    print(f"🤖 {part['text']}")
    
    print(f"\n🎉 Key Benefits:")
    print(f"   ✅ Immediate DataFrame access (no dataset IDs)")
    print(f"   ✅ No persistent memory accumulation")
    print(f"   ✅ Automatic memory cleanup")
    print(f"   ✅ Simple and efficient workflow")
    
    # Example 2: Get a summary answer (not dataset)
    print(f"\n" + "="*50)
    print("📈 Getting summary answer...")
    
    for event in app.stream_query(
        user_id="example_2",
        message="How many customers are there in total?"
    ):
        if 'content' in event and 'parts' in event['content']:
            for part in event['content']['parts']:
                if 'text' in part:
                    print(f"🤖 {part['text']}")

def extract_dataset_id_from_response(app_response):
    """Helper function to extract dataset_id from ADK response"""
    dataset_id = None
    
    for event in app_response:
        if 'content' in event and 'parts' in event['content']:
            for part in event['content']['parts']:
                if 'function_response' in part:
                    try:
                        response_data = json.loads(part['function_response']['response']['result'])
                        if 'dataset_id' in response_data:
                            dataset_id = response_data['dataset_id']
                            break
                    except:
                        continue
        if dataset_id:
            break
    
    return dataset_id

def advanced_example():
    """Example with multiple queries (each replaces the previous)"""
    
    PROJECT_ID = "energyagentai"
    DATASET_NAME = "alberta_energy_ai"
    
    print("\n🔬 Advanced Example: Sequential Dataset Access")
    print("="*50)
    
    agent, sql_tools = create_fixed_sql_agent(PROJECT_ID, DATASET_NAME)
    app = AdkApp(agent=agent)
    
    # Get multiple datasets sequentially (each replaces the previous)
    requests = [
        "Get me all customers in Calgary",
        "Retrieve customers with income over 100000"
    ]
    
    for i, request in enumerate(requests, 1):
        print(f"\n📊 Request {i}: {request}")
        
        # Execute the query
        for event in app.stream_query(
            user_id=f"advanced_{i}",
            message=request
        ):
            pass  # Process response
        
        # Access the current dataset immediately
        try:
            df = sql_tools.get_current_dataset()
            print(f"   ✅ Dataset {i}: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Do quick analysis
            if 'annual_income' in df.columns:
                avg_income = df['annual_income'].mean()
                print(f"   💰 Average income: ${avg_income:,.2f}")
            
            if 'city' in df.columns:
                cities = df['city'].value_counts().head(3)
                print(f"   🏙️  Top cities: {dict(cities)}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n💡 Note: Each new query replaces the previous dataset in memory")
    print(f"   This prevents memory accumulation and keeps usage efficient!")


if __name__ == "__main__":
    main()
    
    # Uncomment to try advanced example
    # advanced_example()