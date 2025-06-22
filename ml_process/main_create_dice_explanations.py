import os
import yaml
import pandas as pd
from counterfactuals import DiceModelExplainer
from tqdm import tqdm
import json

# Load config file named conf.yml
with open('conf.yml') as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)


def clean_json_string(json_str):
    # Remove newlines and extra spaces
    json_str = json_str.replace('\n', '')
    # Ensure it is valid JSON
    if json_str.startswith('[') and json_str.endswith(']'):
        return json.loads(json_str)

# Get Diceexplainer Object
DiceModelExplainer.load_models(conf_file_path='conf.yml')

# Load Test Data
test_df = pd.read_csv(conf['model']['predicted_test_data'])

# Dice explanation is needed for those with high churn probability only
dice_pop = test_df[test_df['prediction'] > 0.4].sort_values(by='prediction', ascending=False).reset_index(drop=True)
print(f"Shape of dice_pop: {dice_pop.shape}")

results_list = []

# Use tqdm for progress bar and iterrows for efficient looping
for i, row in tqdm(dice_pop.iterrows(), total=dice_pop.shape[0]):
    try:
        # Convert row to DataFrame
        test_data_instance = pd.DataFrame([row])
        explainer = DiceModelExplainer(test_data_instance)

        # replace this with the features you want to vary
        x1, x2, x3 = explainer.generate_dice_explanation(features_to_vary=conf['llm_subsets']['action_features'])
        changes = explainer.identify_changes_with_impact(actual=x1, counter_factual=x3)

        # Append a dictionary to the results list
        results_list.append({'customerid': row['customerid'], 'changes': changes})

        if i % 25 == 0:
            print(f"CF for index {i} completed")

    except Exception as e:
        print(f"An error occurred at index {i}: {e}")

# Convert the results list to a DataFrame
results = pd.DataFrame(results_list)
results['changes'] = results['changes'].apply(clean_json_string)
results.to_csv(conf['dice']['cf_recommendations'], index=False)