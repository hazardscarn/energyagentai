import os


import pandas as pd
from xgb_process import shap_summary,xgb_model
import yaml
import xgboost as xgb
import json
import numpy as np
import pickle
from create_dice_models import DiceModelCreator



##Load config file named conf.yml
with open('conf_telchurn.yml') as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)

#Load processed data
df=pd.read_csv(conf['data']['processed_data_path'])
cat_cols=conf['model']['features']['cat_features']
num_cols=conf['model']['features']['num_features']
target=conf['model']['features']['target']
id_features=conf['model']['features']['id_features']


# Initialize and use the model
model_instance = xgb_model.XGBoostModel(df=df, cat_features=cat_cols, num_features=num_cols, target=target,id_features=id_features, mode='dev')
_,dtrain,X_train,dtest,X_test=model_instance.train_model()
X_train=X_train.reset_index(drop=True)
X_test=X_test.reset_index(drop=True)

# print("Saving model")
# # Save the model to a pickle file
# with open(conf['model']['model_location'], 'wb') as f:
#     pickle.dump(model, f)


# print("Save train and test data with predictions")
# X_train.to_csv(conf['model']['predicted_train_data'], index=False)
# X_test.to_csv(conf['model']['predicted_test_data'], index=False)
with open(conf['model']['model_location'], 'rb') as f:
            xgb_model = pickle.load(f)

analyzer=shap_summary.ShapAnalyzer(model=xgb_model,
                                X_train=X_train,
                                dtrain=dtrain,
                                cat_features=cat_cols,
                                num_features=num_cols)

##Save the local SHAP explanation for X_test and X_train
print("Getting Local SHAP explanation saved")
explainer=analyzer.get_explainer()
base_value = explainer.expected_value
print(f"Base Value (Expected Value): {base_value}")
with open(conf['model']['shap_base_value'], "w") as file:
    file.write(f"{base_value}\n")