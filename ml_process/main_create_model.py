import os
import pandas as pd
from xgb_process import shap_summary, xgb_model
import yaml
import xgboost as xgb
import json
import numpy as np
import pickle
import argparse

# Load config file named conf.yml
with open('conf.yml') as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)


def main():
    """
    Main function to execute the data processing and model training.
    """
    parser = argparse.ArgumentParser(description='Run XGBoost model training')
    parser.add_argument('--model_type', type=str, required=True, 
                       help='Name/Type of Model (required)')
    parser.add_argument('--target', type=str, 
                       default=conf['model']['features']['target'],
                       help='Target column name for training')
    parser.add_argument('--base_model_dir', type=str, 
                       default='models',
                       help='Base directory for model files')
    parser.add_argument('--base_results_dir', type=str, 
                       default='results',
                       help='Base directory for results files')

    args = parser.parse_args()
    
    # Set model type and create directories
    model_type = args.model_type
    target = args.target
    
    # Create model-specific directories
    model_folder = os.path.join(args.base_model_dir, model_type)
    results_folder = os.path.join(args.base_results_dir, model_type)
    
    os.makedirs(model_folder, exist_ok=True)
    os.makedirs(results_folder, exist_ok=True)
    
    print(f"Model type: {model_type}")
    print(f"Target variable: {target}")
    print(f"Model folder: {model_folder}")
    print(f"Results folder: {results_folder}")

    # Load processed data
    df = pd.read_csv(conf['data']['processed_data_path'])
    cat_cols = conf['model']['features']['cat_features']
    num_cols = conf['model']['features']['num_features']
    id_features = conf['model']['features']['id_features']
    
    # Validate target column exists
    if target not in df.columns:
        raise ValueError(f"Target column '{target}' not found in data. Available columns: {list(df.columns)}")
    
    print(f"Target variable '{target}' distribution:")
    print(df[target].value_counts())

    # Initialize and use the model
    model_instance = xgb_model.XGBoostModel(
        df=df, 
        cat_features=cat_cols, 
        num_features=num_cols, 
        target=target,
        id_features=id_features, 
        mode='dev',
        model_stats=os.path.join(model_folder, f"{model_type}_model_stats.txt")
    )
    model, dtrain, X_train, dtest, X_test = model_instance.train_model()
    X_train = X_train.reset_index(drop=True)
    X_test = X_test.reset_index(drop=True)

    print("Saving model")
    # Save the model to a pickle file
    model_path = os.path.join(model_folder, f"{model_type}_model.pkl")
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)

    # Initialize SHAP analyzer
    analyzer = shap_summary.ShapAnalyzer(
        model=model,
        X_train=X_train,
        dtrain=dtrain,
        cat_features=cat_cols,
        num_features=num_cols
    )

    # Save the local SHAP explanation for X_test and X_train
    print("Getting Local SHAP explanation saved")
    explainer = analyzer.get_explainer()
    base_value = explainer.expected_value

    print(f"Base Value (Expected Value): {base_value}")
    base_value_path = os.path.join(model_folder, f"{model_type}_shap_base_values.txt")
    with open(base_value_path, "w") as file:
        file.write(f"{base_value}\n")

    # Save the shap explainer
    explainer_path = os.path.join(model_folder, f"{model_type}_shap_explainer.pkl")
    with open(explainer_path, 'wb') as f:
        pickle.dump(explainer, f)

    # Calculate SHAP values
    shap_train = pd.DataFrame(
        explainer.shap_values(xgb.DMatrix(X_train[model.feature_names], enable_categorical=True)),
        columns=model.feature_names
    )
    shap_train[id_features] = X_train[id_features]

    shap_test = pd.DataFrame(
        explainer.shap_values(xgb.DMatrix(X_test[model.feature_names], enable_categorical=True)),
        columns=model.feature_names
    )
    shap_test[id_features] = X_test[id_features]

    print("Saving SHAP values")
    # Rename SHAP columns (assuming 'customerid' is in id_features)
    shap_train.columns = ['shapvalue_' + col if col not in id_features else col for col in shap_train.columns]
    shap_test.columns = ['shapvalue_' + col if col not in id_features else col for col in shap_test.columns]

    print("Saving Big Query Import Tables")
    bq_data = pd.concat([X_train, X_test], axis=0)
    bq_shap_data = pd.concat([shap_train, shap_test], axis=0)
    
    bq_data_path = os.path.join(model_folder, f"{model_type}_bq_data.csv")
    bq_shap_path = os.path.join(model_folder, f"{model_type}_bq_shap_data.csv")
    
    bq_data.to_csv(bq_data_path, index=False)
    bq_shap_data.to_csv(bq_shap_path, index=False)

    print("Get SHAP summary and results")
    result_df = analyzer.analyze_shap_values()
    summary_df = analyzer.summarize_shap_df()

    # Convert object types to category and numeric types to their respective numeric types
    for col in summary_df.columns:
        if summary_df[col].dtype == 'object':
            summary_df[col] = summary_df[col].astype('category')
        elif pd.api.types.is_numeric_dtype(summary_df[col]):
            summary_df[col] = pd.to_numeric(summary_df[col])

    summary_df = summary_df.sort_values(
        by=['Feature_Importance_Rank', 'feature_group', 'probability_contribution'],
        ascending=[True, True, True]
    ).reset_index(drop=True)
    
    # Convert the 'Importance Rank' and 'Group' columns to a consistent data type before sorting
    result_df['Importance Rank'] = result_df['Importance Rank'].astype(str)
    result_df['Group'] = result_df['Group'].astype(str)
    result_df = result_df.sort_values(by=['Importance Rank', 'Group'], ascending=[True, True])

    print("Saving summary and result DataFrames to CSV files")
    # Save the summary and result DataFrames to CSV files
    result_df = result_df[[
        'Feature', 'Group', 'SHAP Value', 'Adjusted Probability', 'Probability Change (%)',
        'Feature Importance', 'Importance Rank'
    ]]
    result_df.columns = [
        'Feature', 'Feature_Subset', 'SHAP_Value', 'Adjusted_Probability', 'Probability_Change_Perc',
        'Feature_Importance', 'Importance_Rank'
    ]

    summary_path = os.path.join(model_folder, f"{model_type}_shap_summary_data.csv")
    results_path = os.path.join(model_folder, f"{model_type}_shap_results.csv")
    
    summary_df.to_csv(summary_path, index=False)
    result_df.to_csv(results_path, index=False)
    
    print(f"Training completed successfully!")
    print(f"All outputs saved to: {model_folder}")


if __name__ == "__main__":
    main()