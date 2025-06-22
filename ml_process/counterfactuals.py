import os
import json
import numpy as np
import pandas as pd
from sklearn.experimental import enable_hist_gradient_boosting  # noqa
from sklearn.ensemble import HistGradientBoostingClassifier
import pickle
import xgboost as xgb
import yaml
import dice_ml
from dice_ml.utils import helpers
from sklearn.metrics import pairwise_distances


class DiceModelExplainer:
    # Class variables to store the models
    hist_model = None
    dice_model = None
    xgb_model = None
    explainer = None
    train_categories=None

    @classmethod
    def load_models(cls, conf_file_path):
        """
        Load the histogram model, the DiCE model, and the XGBoost model from files.
        """
        with open(conf_file_path, 'r') as f:
            cls.conf = yaml.load(f, Loader=yaml.FullLoader)


        # if cls.hist_model is None:
        #     with open(cls.conf['model']['histogram_model_location'], 'rb') as f:
        #         cls.hist_model = pickle.load(f)

        if cls.explainer is None:
            with open(cls.conf['model']['dice_model_location'], 'rb') as f:
                cls.explainer = pickle.load(f)

        if cls.xgb_model is None:
            with open(cls.conf['model']['model_location'], 'rb') as f:
                cls.xgb_model = pickle.load(f)
        # print("yo")
        # if cls.explainer is None:
        #     # Create a DiCE model object using the HistGradientBoostingClassifier model
        #     m = dice_ml.Model(model=cls.hist_model, backend='sklearn')
        #     cls.explainer = dice_ml.Dice(cls.dice_model, m)

        if cls.train_categories is None:
            with open(cls.conf['model']['train_category_levels'], 'r') as f:
                cls.train_categories = json.load(f)

        cls.cat_cols = cls.conf['model']['features']['cat_features']
        cls.num_cols = cls.conf['model']['features']['num_features']

    def __init__(self, df):
        """
        Constructs all the necessary attributes for the ModelLoader object.

        Parameters
        ----------
            df : DataFrame
                a pandas DataFrame representing the input data
        """
        self.query_instance = df.copy()
        self.df = df.copy()
        for col in self.__class__.cat_cols:
            self.df.loc[:, col] = (self.df.loc[:, col]
                            .astype(str)
                            .replace('nan', 'unknown')  # replace 'nan' strings with 'unknown'
                            .str.lower()
                            .str.strip()
                            .replace('', 'unknown')  # replace blank strings with 'unknown'
                            .fillna('unknown')  # fill NaN values with 'unknown'
                            .astype('category'))


        for col in self.__class__.num_cols:
            self.df.loc[:, col] = pd.to_numeric(self.df.loc[:, col], errors='coerce').fillna(0)

    def align_categories(self,X_prod):
        for col in self.__class__.cat_cols:
            # Set the categories of the production data to be the same as the ones used during training
            X_prod[col] = X_prod[col].astype('category').cat.set_categories(self.__class__.train_categories[col])
        return X_prod

    def catboost_process(self,data):
        for column in  self.__class__.cat_cols +  self.__class__.num_cols:
            if column in self.__class__.cat_cols:
                data[column] = data[column].astype('category')
            else:
                data[column] = pd.to_numeric(data[column], errors='coerce')
        return data

    def generate_dice_explanation(self, features_to_vary):
        """
        Generate DiCE explanations for a single given test instance.

        Parameters:
        test_data (DataFrame): The test data.
        features_to_vary (list): The features to vary in the counterfactuals.
        xgb_model (XGBClassifier): The trained XGBoost model.
        explainer (DiCE): The DiCE explainer.
        total_CFs (int, optional): The total number of counterfactuals to generate. Defaults to 3.
        desired_class (int, optional): The desired class for the counterfactuals. Defaults to 0.
        top_N (int, optional): The top N counterfactuals to return. Defaults to 3.
        diversity_weight (float, optional): The weight for diversity in the counterfactuals. Defaults to 1.

        Returns:
        tuple: A tuple containing the actual instance, all counterfactuals, and the top N counterfactuals.
        """
        total_CFs = self.__class__.conf['dice']['total_cfs']
        top_N = self.__class__.conf['dice']['top_n']
        diversity_weight = self.__class__.conf['dice']['diversity_weight']
        desired_class = self.__class__.conf['dice']['desired_class']
        #desired_class = 0
        print("0")
        try:


            query_instance=self.query_instance[self.__class__.cat_cols+self.__class__.num_cols].copy()
            range_features=  self.__class__.conf['dice']['permitted_range']          
            

            #query_instance=self.catboost_process(query_instance)
            dice_exp = self.__class__.explainer.generate_counterfactuals(query_instance, total_CFs=total_CFs,
                                 desired_class=desired_class, features_to_vary=features_to_vary,
                                diversity_weight=diversity_weight,
                                permitted_range=range_features,
                                random_seed=42,verbose=False)

            # x1 = query_instance.copy()
            x1 = self.align_categories(self.df.copy())
            x1=x1[self.__class__.xgb_model.feature_names]
            x1['churn_probability'] = self.__class__.xgb_model.predict(xgb.DMatrix(x1, enable_categorical=True))
            x1['type'] = 'actual'


            x2 = dice_exp.cf_examples_list[0].final_cfs_df
            x2=self.catboost_process(x2)
            x2=self.align_categories(x2)
            x2=x2[self.__class__.xgb_model.feature_names]
            x2['churn_probability'] = self.__class__.xgb_model.predict(xgb.DMatrix(x2, enable_categorical=True))
            x2['type'] = 'counterfactual'

            ##NOTE - Can add filter_similar_cfs to filter out similar counterfactuals
            # x3=x2.sort_values(by='churn_probability',ascending=True)
            #x3=x3[x3['churn_probability']<x1['churn_probability'].head(top_N).values[0]]
            x3=x2[x2['churn_probability']<x1['churn_probability'].values[0]].copy()
            x3=x3.sort_values(by='churn_probability',ascending=True).head(top_N)

            return x1,x2,x3
        except Exception as e:
            print(f"Could not generate counterfactual for instance {self.df.index[0]}: {e}")

    def identify_changes_with_impact(self,actual, counter_factual):
        """
        Identify the changes in the counterfactuals that have an impact on the prediction.

        Parameters:
        actual (DataFrame): The actual instance.
        counter_factual (DataFrame): The counterfactual instances.

        Returns:
        str: A JSON string representing the changes and their impact.
        """
        # Initialize an empty list to store the changes
        changes = []

        # Get the actual instance
        actual_instance = actual.iloc[0]

        # Iterate over the rows of counter_factual
        for i in range(len(counter_factual)):
            # Get the counterfactual instance
            counterfactual = counter_factual.iloc[i]

            # Initialize an empty dictionary to store the changes for this row
            row_changes = {"recommendation_rank": i + 1}

            # Iterate over the features
            for feature in actual.columns:
                # If the feature value has changed and the feature is not 'type'
                if feature!='churn_prob':
                    if actual_instance[feature] != counterfactual[feature] and feature != 'type':
                        # Add the change to the dictionary
                        row_changes[feature] = f'{actual_instance[feature]} -> {counterfactual[feature]}'

            # Add the impact on churn probability
            initial_prob = float(actual_instance['churn_probability'])
            new_prob = float(counterfactual['churn_probability'])
            reduction = (initial_prob - new_prob)
            row_changes['impact'] = f"Churn probability decreased by {reduction * 100:.2f}%"

            # Add the changes for this row to the list
            changes.append(row_changes)

        # Convert the list to a JSON object
        changes_json = json.dumps(changes, indent=4)

        return changes_json


    def generate_range(self,value, lower=0.8, upper=1.0):
        """
        Generate a range of values between 80% and 100% of the input value.

        Parameters:
        value (float): The input value.

        Returns:
        list: A list containing the lower and upper bounds of the range.
        """
        if value == 0:
            return [-5, 5]
        else:
            lower_bound = value * lower
            upper_bound = value * upper
        return [lower_bound, upper_bound]
    
    def filter_similar_cfs(self,cf_df, similarity_threshold=0.05):
        # Select only numeric columns
        numeric_cols = ['currentequipmentdays','monthlyrevenue',
        'directorassistedcalls', 'overageminutes', 'roamingcalls', 'droppedblockedcalls',
        'customercarecalls', 'threewaycalls','callforwardingcalls', 'callwaitingcalls','activesubs', 'handsets', 'handsetmodels', 
        'retentioncalls','referralsmadebysubscriber','revenue_per_minute','avg_call_duration',
        'customer_support_interaction','handsetprice','roamingcalls']
        
        # Sort DataFrame by 'prediction' in ascending order
        cf_df = cf_df.sort_values(by=['churn_probability'], ascending=True)
        
        # Calculate pairwise distances between counterfactuals
        distances = pairwise_distances(cf_df[numeric_cols], metric='euclidean')
        
        # Initialize list of unique indices with the index of the first row
        unique_indices = [0]
        
        for i in range(1, len(cf_df)):
            is_unique = True
            for j in unique_indices:
                if distances[i, j] < similarity_threshold:
                    is_unique = False
                    # If a similar row is found, remove the row with the higher 'prediction' value
                    if cf_df.iloc[i]['churn_probability'] > cf_df.iloc[j]['churn_probability']:
                        unique_indices.remove(j)
                    break
            if is_unique:
                unique_indices.append(i)
        
        return cf_df.iloc[unique_indices]
    
