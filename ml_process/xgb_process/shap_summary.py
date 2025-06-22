import pandas as pd
import numpy as np
import xgboost as xgb
import shap
import os

class ShapAnalyzer:

    def __init__(self, model, X_train,dtrain, cat_features, num_features):
        self.model = model
        self.X_train = X_train
        self.dtrain = dtrain
        self.cat_features = cat_features
        self.num_features = num_features
        self.explainer = shap.TreeExplainer(model)
        self.shap_values = self.explainer.shap_values(dtrain)
        # Check if expected_value is a scalar or an array
        if isinstance(self.explainer.expected_value, np.ndarray):
            # For multi-class, you might want to handle differently or specify which class to focus on
            self.base_value = self.explainer.expected_value[0]  # assuming interest in the first class
        else:
            self.base_value = self.explainer.expected_value
        self.result_df = None
        self.importance_df=None
    
    def get_shap_value(self):
        return self.shap_values
    
    def get_explainer(self):
        return self.explainer

    def sigmoid(self, x):
        """ Sigmoid function to convert log-odds to probabilities. """
        return 1 / (1 + np.exp(-x))

    def analyze_shap_values(self):
        base_probability = self.sigmoid(self.base_value)
        results = []
        feature_importances = {}

        # Calculate feature importances
        for feature in self.cat_features + self.num_features:
            feature_shap_values = self.shap_values[:, self.X_train.columns.get_loc(feature)]
            feature_importances[feature] = np.mean(np.abs(feature_shap_values))

        importance_df = pd.DataFrame(list(feature_importances.items()), columns=['Feature', 'Importance'])
        importance_df.sort_values('Importance', ascending=False, inplace=True)
        importance_df['Rank'] = range(1, len(importance_df) + 1)
        importance_ranks = importance_df.set_index('Feature')['Rank'].to_dict()

        # Process each feature
        for feature in self.cat_features + self.num_features:
            feature_values = self.X_train[feature]
            feature_shap_values = self.shap_values[:, self.X_train.columns.get_loc(feature)]
            df = pd.DataFrame({feature: feature_values, 'SHAP Value': feature_shap_values})

            if feature in self.num_features:
                df['Group'] = pd.qcut(df[feature], 10, duplicates='drop')
            else:
                df['Group'] = df[feature]

            group_avg = df.groupby('Group',observed=True)['SHAP Value'].mean().reset_index()
            group_avg['Adjusted Probability'] = self.sigmoid(self.base_value + group_avg['SHAP Value'])
            group_avg['Probability Change (%)'] = (group_avg['Adjusted Probability'] - base_probability) * 100
            group_avg['Feature'] = feature
            group_avg['Feature Importance'] = feature_importances[feature]
            group_avg['Importance Rank'] = importance_ranks[feature]
            results.append(group_avg)

        self.result_df = pd.concat(results, ignore_index=True)
        self.importance_df=importance_df
        return self.result_df

    def summarize_shap_text(self):
        
        descriptions=[]
        descriptions.append(f"""Below is the description of partial dependence(PD) of target prediction on all the features.\n
                            They help in understanding how the features affect the predictions of a model, regardless of the values of other features.\n
                        """)
        
        

        # Loop through each row in the result DataFrame
        for _, row in self.result_df.iterrows():
            feature = row['Feature']
            effect = "increases" if row['Probability Change (%)'] > 0 else "decreases"
            change = abs(row['Probability Change (%)'])
            
            # Format description for intervals (numeric features) and categorical values differently
            if isinstance(row['Group'], pd.Interval):
                description = f"When {feature} is within {row['Group']}, it {effect} the probability of class 1 by {change:.2f}%. \n"
            else:
                description = f"When {feature} is {row['Group']}, it {effect} the probability of class 1 by {change:.2f}%. \n"
            
            # Add the description to the list
            descriptions.append(description)
        

        feature_importances_summary = []

        feature_importances_summary.append(f"""Feature importance from the SHAP summary is another tool that helps us understand what are top contributors towards model prediction
and outcome. The mean absolute SHAP value provides an aggregate measure of the overall impact that each feature has on the model's predictions.""")
        
        feature_importances_summary.append(f"""Below is the feature importance summary of all feaures used in the model.\n""")

        # Create and sort feature importance summary outside of the results loop
        importance_df = self.importance_df[['Feature', 'Importance', 'Rank']].drop_duplicates()
        importance_df.sort_values('Rank', ascending=True, inplace=True)
        # print(importance_df)
        # Compile feature importance summaries
        for _, row in importance_df.iterrows():
            imp_text1 = f"The importance rank of {row['Feature']}  in the model prediction is {row['Rank']} with a mean absolute SHAP value of {row['Importance']:.4f}.\n"
            imp_text=imp_text1
            feature_importances_summary.append(imp_text)

        # Combine all descriptions and append the feature importance summaries at the end
        summary_text = " ".join(descriptions) + " " + " ".join(feature_importances_summary)
        return summary_text

    def summarize_shap_df(self):
        # Initialize an empty list to store the results
        results = []

        # Loop through each row in the result DataFrame
        for _, row in self.result_df.iterrows():
            feature = row['Feature']
            effect = "increases" if row['Probability Change (%)'] > 0 else "decreases"
            change = abs(row['Probability Change (%)'])
            feature_importance_rank = row['Importance Rank']  # use the 'Importance Rank' from the result_df
            shap_value = row['SHAP Value']  # assuming the DataFrame has a column 'SHAP Value' for feature importance

            # Initialize an empty dictionary to store the result for this row
            result = {}

            # Format description for intervals (numeric features) and categorical values differently
            if isinstance(row['Group'], pd.Interval):
                group = str(row['Group'])
            else:
                group = row['Group']

            result = {
                'feature': feature,
                'feature_group': group,
                'feature_effect': effect,
                'probability_contribution': change,
                'Feature_Importance_Rank': feature_importance_rank,
                'SHAP_Value': shap_value
            }

            # Add the result to the list
            results.append(result)

        # Convert the list of results to a DataFrame
        self.summary_df = pd.DataFrame(results)
        return self.summary_df