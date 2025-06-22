import os



# # Get the current working directory
# current_dir = os.getcwd()
# # Assuming the root directory is one level up from the current directory
# root_dir = os.path.dirname(current_dir)
# # Change the working directory to the root directory
# os.chdir(root_dir)
# print("Current working directory:", os.getcwd())


from process_data import DataProcessor
import yaml
import json
import numpy as np
import pandas as pd

##Load config file named conf.yml
with open('conf.yml') as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)




# Create an instance of the DataProcessor class
data_processor = DataProcessor(
    data_path=conf['data']['raw_data_path'],
    cat_cols=conf['data']['features']['cat_features'],
    num_cols=conf['data']['features']['num_features'],
    target=conf['data']['features']['target'],
    target_majority_class=conf['data']['features']['target_majority_class']
)

# Process the data
df = data_processor.process_data()
print(f"Processed data shape: {df.shape}")
print(f"Processed data save to: {conf['data']['processed_data_path']}")
df.to_csv(conf['data']['processed_data_path'], index=False)