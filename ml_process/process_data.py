import os
from utils import process_data
from xgb_process import shap_summary,xgb_model
import yaml
import json
import numpy as np
import pandas as pd
import pickle


class DataProcessor:
    def __init__(self, data_path, cat_cols, num_cols, target, target_majority_class):
        """
        Initialize the DataProcessor class.

        Parameters:
        data_path (str): Path to the data file.
        cat_cols (list): List of categorical feature names.
        num_cols (list): List of numerical feature names.
        target (str): Name of the target variable.
        target_majority_class (str): Majority class of the target variable.
        """
        self.data_path = data_path
        self.cat_cols = cat_cols
        self.num_cols = num_cols
        self.target = target
        self.target_majority_class = target_majority_class

    def load_data(self):
        """
        Load the data from the data file and clean the column names.
        """
        print(f"Loading data from :{self.data_path}")
        self.df = pd.read_csv(self.data_path)
        self.df.columns = self.df.columns.str.replace(' ', '').str.lower()

    def add_engineered_features(self):
        """
        Add engineered features to the data.
        """
        print("Adding engineered features.")


    def check_columns(self):
        """
        Check if all required columns are in the DataFrame.
        """
        if set(self.cat_cols + self.num_cols + [self.target]).issubset(self.df.columns):
            print("All required columns are in the DataFrame.")
        else:
            missing_cols = set(self.cat_cols + self.num_cols + [self.target]) - set(self.df.columns)
            print("Missing columns:", missing_cols)

    def clean_data(self):
        """
        Clean the data by processing the target and feature columns.
        """
        print("Cleaning the data.")
        #self.df[self.target] = self.df[self.target].str.strip()
        print(self.df[self.target].value_counts())
        #self.df[self.target] = self.df[self.target].apply(lambda x: 1 if x == self.target_majority_class else 0)
        for col in self.cat_cols:
            self.df[col] = (self.df[col]
                            .astype(str)
                            .replace('nan', 'unknown')  # replace 'nan' strings with 'unknown'
                            .str.lower()
                            .str.strip()
                            .replace('', 'unknown')  # replace blank strings with 'unknown'
                            .fillna('unknown')  # fill NaN values with 'unknown'
                            .astype('category'))

        for col in self.num_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)

    def process_data(self):
        """
        Process the data by loading it, adding engineered features, checking the columns, and cleaning it.

        Returns:
        DataFrame: The processed data.
        """
        self.load_data()
        self.add_engineered_features()
        self.check_columns()
        self.clean_data()
        return self.df