from google.cloud import storage
import pickle
import pandas as pd
import xgboost as xgb
import numpy as np
import tempfile
import os
from typing import Dict, List, Union, Optional

from google.cloud import bigquery
from google.cloud import storage
from tabulate import tabulate


_project_id = "energyagentai"
_dataset_name = "alberta_energy_ai"
client = bigquery.Client(project='energyagentai')


class SimpleXGBoostScorer:
    """
    Simple tool for loading and scoring XGBoost models from GCS with optional SHAP summary
    """
    
    def __init__(self, bucket_name: str = 'albertaenergy-ads'):
        self.bucket_name = bucket_name
        self.client = storage.Client()
        self.bucket = self.client.bucket(bucket_name)
        
        # Feature definitions (matching your existing pipeline)
        self.cat_features = [
            'customer_segment', 'customer_type', 'home_ownership', 'employment_status',
            'education_level', 'city', 'heating_type', 'seasonal_usage_pattern',
            'current_rate_plan', 'contract_type', 'previous_provider', 'green_energy_preference',
            'tech_savviness', 'price_sensitivity', 'communication_preference', 'paperless_billing',
            'oil_gas_employment', 'economic_sensitivity', 'regulated_utility_consideration',
            'payment_method', 'business_type', 'business_size'
        ]
        
        self.num_features = [
            'tenure_months', 'age', 'annual_income', 'household_size', 'home_value',
            'credit_score', 'service_address', 'monthly_usage_kwh', 'peak_demand_kw',
            'property_age', 'rate_plan_changes', 'satisfaction_score', 'nps_score',
            'app_usage_monthly', 'website_visits_monthly', 'call_center_interactions_12m',
            'competitive_quotes_received', 'late_payment_rate', 'avg_monthly_bill',
            'complaint_history', 'service_interruptions_12m', 'bill_shock_events'
        ]
        
        # Cache for models, categories, and SHAP explainers
        self._models = {}
        self._categories = None
        self._shap_explainers = {}
        
        # Hardcoded base values for each model
        self.base_values = {
            'churn_model.pkl': -0.14260683953762054,
            'crosssell_hvac_model.pkl': 0.5818970799446106,
            'crosssell_insurance_model.pkl': 0.5098369717597961,
            'crosssell_solar_model.pkl': 0.16068263351917267,
            'upsell_efficiency_analysis_model.pkl': 0.22734493017196655,
            'upsell_green_plan_model.pkl': -0.5518404841423035,
            'upsell_surge_protection_model.pkl': -0.06109029799699783
        }
    
    def load_categories_from_gcs(self, categories_filename: str = 'train_categories.json'):
        """Load training categories from GCS bucket"""
        if self._categories is not None:
            return self._categories
        
        try:
            blob = self.bucket.blob(f'categories/{categories_filename}')
            categories_json = blob.download_as_text()
            import json
            self._categories = json.loads(categories_json)
            print(f'Successfully loaded categories: {categories_filename}')
            return self._categories
            
        except Exception as e:
            print(f'Error loading categories {categories_filename}: {str(e)}')
            return None
    
    def load_object_from_gcs(self, object_name: str, folder: str):
        """Generic function to load any pickle object from GCS"""
        # Check appropriate cache
        if folder == 'models' and object_name in self._models:
            return self._models[object_name]
        elif folder == 'shap_explainer' and object_name in self._shap_explainers:
            return self._shap_explainers[object_name]
        
        try:
            blob = self.bucket.blob(f'{folder}/{object_name}')
            object_bytes = blob.download_as_bytes()
            loaded_object = pickle.loads(object_bytes)
            
            # Cache the object
            if folder == 'models':
                self._models[object_name] = loaded_object
            elif folder == 'shap_explainer':
                self._shap_explainers[object_name] = loaded_object
            
            print(f'Successfully loaded {folder}/{object_name}')
            return loaded_object
            
        except Exception as e:
            print(f'Error loading {folder}/{object_name}: {str(e)}')
            return None
    
    def prepare_features(self, data: Union[Dict, List[Dict], pd.DataFrame], 
                        use_training_categories: bool = True) -> pd.DataFrame:
        """
        Prepare features using the same logic as your existing pipeline
        """
        # Convert to DataFrame
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
        
        # Clean column names (matching your existing pipeline)
        df.columns = df.columns.str.replace(' ', '').str.lower()
        
        # Load training categories if requested
        training_categories = None
        if use_training_categories:
            training_categories = self.load_categories_from_gcs()
        
        # Process categorical features
        for col in self.cat_features:
            if col in df.columns:
                df[col] = (df[col]
                          .astype(str)
                          .replace('nan', 'unknown')
                          .str.lower()
                          .str.strip()
                          .replace('', 'unknown')
                          .fillna('unknown'))
                
                # Apply training categories if available
                if training_categories and col in training_categories:
                    valid_categories = training_categories[col]
                    df[col] = df[col].apply(lambda x: x if x in valid_categories else 'unknown')
                    df[col] = pd.Categorical(df[col], categories=valid_categories)
                else:
                    df[col] = df[col].astype('category')
            else:
                # Handle missing columns
                if training_categories and col in training_categories:
                    df[col] = pd.Categorical(['unknown'] * len(df), categories=training_categories[col])
                else:
                    df[col] = pd.Categorical(['unknown'] * len(df))
        
        # Process numerical features
        for col in self.num_features:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            else:
                df[col] = 0
        
        # Return only the features needed for prediction
        feature_cols = self.cat_features + self.num_features
        return df[feature_cols]
    
    def sigmoid(self, x):
        """Sigmoid function to convert log-odds to probabilities."""
        return 1 / (1 + np.exp(-x))
    
    def create_shap_summary(self, shap_values: np.ndarray, X: pd.DataFrame, base_value: float):
        """
        Create SHAP summary like the original ShapAnalyzer - groups features and averages SHAP contributions
        Works for any dataset size (1 customer or 100+ customers)
        """
        try:
            base_probability = self.sigmoid(base_value)
            results = []
            feature_importances = {}

            # Calculate feature importances (mean absolute SHAP values)
            for feature in self.cat_features + self.num_features:
                if feature in X.columns:
                    feature_idx = X.columns.get_loc(feature)
                    feature_shap_values = shap_values[:, feature_idx]
                    feature_importances[feature] = np.mean(np.abs(feature_shap_values))

            # Create importance rankings
            importance_df = pd.DataFrame(list(feature_importances.items()), columns=['Feature', 'Importance'])
            importance_df.sort_values('Importance', ascending=False, inplace=True)
            importance_df['Rank'] = range(1, len(importance_df) + 1)
            importance_ranks = importance_df.set_index('Feature')['Rank'].to_dict()

            # Process each feature and group by ranges/categories
            for feature in self.cat_features + self.num_features:
                if feature not in X.columns:
                    continue
                    
                feature_values = X[feature]
                feature_idx = X.columns.get_loc(feature)
                feature_shap_values = shap_values[:, feature_idx]
                
                # Create dataframe with feature values and SHAP values
                df = pd.DataFrame({feature: feature_values, 'SHAP Value': feature_shap_values})

                # Group by ranges (numeric) or categories (categorical)
                if feature in self.num_features:
                    try:
                        df['Group'] = pd.qcut(df[feature], 10, duplicates='drop')
                    except ValueError:
                        # If qcut fails, use unique values
                        df['Group'] = df[feature]
                else:
                    df['Group'] = df[feature]

                # Calculate average SHAP values for each group
                group_avg = df.groupby('Group', observed=True)['SHAP Value'].mean().reset_index()
                group_avg['Adjusted Probability'] = self.sigmoid(base_value + group_avg['SHAP Value'])
                group_avg['Probability Change (%)'] = (group_avg['Adjusted Probability'] - base_probability) * 100
                group_avg['Feature'] = feature
                group_avg['Feature Importance'] = feature_importances[feature]
                group_avg['Importance Rank'] = importance_ranks[feature]
                results.append(group_avg)

            # Combine all results
            result_df = pd.concat(results, ignore_index=True)
            
            # Create summary dataframe (like original summarize_shap_df)
            summary_results = []
            for _, row in result_df.iterrows():
                feature = row['Feature']
                effect = "increases" if row['Probability Change (%)'] > 0 else "decreases"
                change = abs(row['Probability Change (%)'])
                feature_importance_rank = row['Importance Rank']
                shap_value = row['SHAP Value']

                # Format group for intervals vs categorical
                if isinstance(row['Group'], pd.Interval):
                    group = str(row['Group'])
                else:
                    group = row['Group']

                summary_results.append({
                    'feature': feature,
                    'feature_group': group,
                    'feature_effect': effect,
                    'probability_contribution': change,
                    'Feature_Importance_Rank': feature_importance_rank,
                    'SHAP_Value': shap_value
                })

            summary_df = pd.DataFrame(summary_results)
            
            # Sort by importance rank and probability contribution
            if len(summary_df) > 0:
                summary_df = summary_df.sort_values(
                    by=['Feature_Importance_Rank', 'probability_contribution'],
                    ascending=[True, False]
                ).reset_index(drop=True)
            
            return summary_df
            
        except Exception as e:
            print(f"Error creating SHAP summary: {str(e)}")
            return pd.DataFrame()
    
    def score_model(self, model_name: str, features: Union[Dict, List[Dict], pd.DataFrame], 
                   shap_enabled: bool = False) -> Dict:
        """
        Score XGBoost model with given features, optionally with grouped SHAP summary
        
        Args:
            model_name: Name of model (e.g., 'crosssell_hvac')
            features: Input features for prediction (single customer or multiple)
            shap_enabled: Whether to include grouped SHAP summary analysis
            
        Returns:
            Dict with prediction(s) and optionally 'shap_summary_data' DataFrame
            showing average feature contributions grouped by ranges/categories
        """
        try:
            # Construct filenames
            model_filename = f"{model_name}_model.pkl"
            shap_filename = f"{model_name}_shap_explainer.pkl"
            
            # Load model
            model = self.load_object_from_gcs(model_filename, 'models')
            if model is None:
                return {'error': f'Failed to load model: {model_filename}'}
            
            # Prepare features
            X = self.prepare_features(features)
            
            # Create DMatrix for prediction
            dmatrix = xgb.DMatrix(X, enable_categorical=True)
            
            # Make predictions
            predictions = model.predict(dmatrix)
            
            # Prepare basic response
            result = {
                'model_name': model_name,
                'predictions': predictions.tolist(),
                'average_prediction': float(np.mean(predictions)),
                'num_samples': len(X)
            }
            
            # Add single prediction for convenience if only one sample
            if len(predictions) == 1:
                result['prediction'] = predictions[0]
            
            # Add SHAP summary if requested
            if shap_enabled:
                explainer = self.load_object_from_gcs(shap_filename, 'shap_explainer')
                if explainer is None:
                    result['shap_warning'] = f'Could not load SHAP explainer: {shap_filename}'
                else:
                    try:
                        # Calculate SHAP values
                        shap_values = explainer.shap_values(dmatrix)
                        base_value = self.base_values.get(model_filename, 0)
                        
                        # Create SHAP summary
                        shap_summary_df = self.create_shap_summary(shap_values, X, base_value)
                        
                        result['base_value'] = base_value
                        result['shap_summary_data'] = shap_summary_df
                        
                    except Exception as e:
                        result['shap_error'] = f'SHAP calculation failed: {str(e)}'
            
            return result
            
        except Exception as e:
            return {'error': f'Scoring failed: {str(e)}'}

# Simple convenience functions
def load_and_score(model_name: str, customer_data: Dict, shap_enabled: bool = False, 
                  bucket_name: str = 'albertaenergy-ads') -> Dict:
    """
    Simple function to load model and score a single customer
    """
    scorer = SimpleXGBoostScorer(bucket_name)
    return scorer.score_model(model_name, customer_data, shap_enabled)

def batch_score(model_name: str, customers_data: List[Dict], shap_enabled: bool = False,
               bucket_name: str = 'albertaenergy-ads') -> Dict:
    """
    Simple function to score multiple customers at once
    """
    scorer = SimpleXGBoostScorer(bucket_name)
    return scorer.score_model(model_name, customers_data, shap_enabled)


def analyze_model_with_shap_tool(sql_query: str, model_name: str, target_event: str = "positive") -> str:
    """
    ADK Tool: Analyze ML model using SHAP with provided SQL query
    
    Args:
        sql_query (str): SQL query to retrieve customer data
        model_name (str): Model to analyze (churn, crosssell_hvac, etc.)
        target_event (str): positive or negative factors
    
    Returns:
        str: SHAP analysis results
    """
    try:
        # Set up SHAP analysis
        shap_enabled = True
        bucket_name = 'albertaenergy-ads'
        scorer = SimpleXGBoostScorer(bucket_name)
        client = bigquery.Client(project=_project_id)
        
        # Ensure we have SELECT * for model scoring - replace any specific column selection
        cleaned_query = sql_query.strip()
        upper_query = cleaned_query.upper()
        if upper_query.startswith('SELECT'):
            from_pos = upper_query.find(' FROM ')
            if from_pos > 0:
                select_part = cleaned_query[:from_pos + 1]
                from_part = cleaned_query[from_pos + 1:]
                
                # Check if it's not already SELECT *
                if not 'SELECT *' in select_part.upper():
                    cleaned_query = f"SELECT * {from_part}"
                    print(f"Modified query for model scoring: {cleaned_query}")
        
        # Execute SQL query
        customer_df = client.query(cleaned_query).to_dataframe()
        
        if len(customer_df) == 0:
            return "No customers found matching the query criteria"
        
        # Score the model
        results = scorer.score_model(model_name, customer_df, shap_enabled)
        
        if 'error' in results:
            return f"Model scoring failed: {results['error']}"
        
        avg_prediction = results.get('average_prediction', 0.0)
        num_customers = results.get('num_samples', 0)
        
        # Get SHAP summary and filter by target event
        if 'shap_summary_data' not in results:
            return "SHAP analysis not available for this model"
        
        shap_summary = results['shap_summary_data']
        
        # Filter for target event
        if target_event.lower() == "positive":
            filtered_shap = shap_summary[shap_summary['SHAP_Value'] > 0].copy()
        else:
            filtered_shap = shap_summary[shap_summary['SHAP_Value'] < 0].copy()
        
        if len(filtered_shap) == 0:
            return f"No {target_event} contributing factors found for {model_name}"
        
        # Sort by probability contribution
        filtered_shap = filtered_shap.sort_values('probability_contribution', ascending=False).reset_index(drop=True)
        
        # Create the analysis report
        model_display = model_name.replace('_', ' ').title()
        event_direction = "increases" if target_event.lower() == "positive" else "decreases"
        
        report = f"""
## {model_display} Analysis Results

**Average Prediction Probability:** {avg_prediction:.3f} ({avg_prediction*100:.1f}%)
**Customers Analyzed:** {num_customers}
**Analysis Focus:** Factors that {event_direction} the prediction probability

### Top 5 Contributing Factors:
"""
        
        # Add top factors
        top_factors = filtered_shap.head(15)
        for i, (_, row) in enumerate(top_factors.iterrows(), 1):
            effect_desc = "increases" if row['SHAP_Value'] > 0 else "decreases"
            report += f"{i}. **{row['feature'].replace('_', ' ').title()}** ({row['feature_group']}): {effect_desc} probability by {row['probability_contribution']:.2f}%\n"
        
        # Add detailed table
        report += f"\n### Detailed Analysis\n\n"
        display_columns = ['feature', 'feature_group', 'probability_contribution', 'SHAP_Value']
        display_shap = filtered_shap[display_columns].head(30)
        
        report += tabulate(display_shap, headers=['Feature', 'Group', 'Probability Change (%)', 'SHAP Value'], 
                          tablefmt='pipe', showindex=False, floatfmt='.3f')
        
        return report
        
    except Exception as e:
        return f"Error in SHAP analysis: {str(e)}"



# Example usage
if __name__ == "__main__":
    # Initialize scorer
    scorer = SimpleXGBoostScorer()
    
    # # Your test customer data
    # test_customer = {
    #     "customer_segment": "price_sensitive_family",
    #     "customer_type": "residential", 
    #     "home_ownership": "rent",
    #     "employment_status": "retired",
    #     "education_level": "college_diploma",
    #     "city": "medicine_hat",
    #     "heating_type": "natural_gas",
    #     "seasonal_usage_pattern": "balanced",
    #     "current_rate_plan": "fixed_rate_5yr",
    #     "contract_type": "month_to_month",
    #     "previous_provider": "unknown",
    #     "green_energy_preference": True,
    #     "tech_savviness": "high",
    #     "price_sensitivity": "high", 
    #     "communication_preference": "email",
    #     "paperless_billing": True,
    #     "oil_gas_employment": False,
    #     "economic_sensitivity": "medium",
    #     "regulated_utility_consideration": "low",
    #     "payment_method": "auto_pay",
    #     "business_type": "unknown",
    #     "business_size": "unknown",
    #     "tenure_months": 85,
    #     "age": 66,
    #     "annual_income": 45369,
    #     "household_size": 3,
    #     "home_value": 2972,
    #     "credit_score": 749,
    #     "service_address": 1,
    #     "monthly_usage_kwh": 25.7,
    #     "peak_demand_kw": 12.9,
    #     "property_age": 3,
    #     "rate_plan_changes": 0,
    #     "satisfaction_score": 381,
    #     "nps_score": 98,
    #     "app_usage_monthly": 0,
    #     "website_visits_monthly": 2,
    #     "call_center_interactions_12m": 0,
    #     "competitive_quotes_received": 0,
    #     "late_payment_rate": 0.18,
    #     "avg_monthly_bill": 445.86,
    #     "complaint_history": 0,
    #     "service_interruptions_12m": 0,
    #     "bill_shock_events": 0
    # }
    
    test_customer= client.query(f"""SELECT * FROM `energyagentai.alberta_energy_ai.customer_base` WHERE
    annual_income > 100000 AND age > 65""").to_dataframe()
    #print(test_customer)
    


    
    print("\n=== Model Scoring with SHAP Summary ===")
    result_with_shap = scorer.score_model('crosssell_hvac', test_customer, shap_enabled=True)
    print(f"Prediction: {result_with_shap.get('average_prediction')}")
    
    if 'shap_summary_data' in result_with_shap:
        shap_summary = result_with_shap['shap_summary_data']
        print(f"\nSHAP Summary ({len(shap_summary)} feature groups):")
        print(shap_summary.head(10))
        
        print(f"\nTop 5 most impactful feature groups:")
        top_features = shap_summary.nlargest(5, 'probability_contribution')
        for _, row in top_features.iterrows():
            print(f"  {row['feature']} (group: {row['feature_group']}): {row['feature_effect']} probability by {row['probability_contribution']:.3f}%")
    
    print("\n=== Using Convenience Function ===")
    quick_result = load_and_score('upsell_green_plan', test_customer, shap_enabled=True)
    print(f"Prediction: {quick_result.get('average_prediction')}")
    if 'shap_summary_data' in quick_result:
        shap_df = quick_result['shap_summary_data']
        print(f"Total feature groups: {len(shap_df)}")
        if len(shap_df) > 0:
            most_impactful = shap_df.nlargest(1, 'probability_contribution').iloc[0]
            print(f"Most impactful group: {most_impactful['feature']} ({most_impactful['feature_group']})")
        else:
            print("No feature groups found")
        print(shap_df)