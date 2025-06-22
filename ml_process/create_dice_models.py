import os
import json
import numpy as np
import pandas as pd
from sklearn.experimental import enable_hist_gradient_boosting  # noqa
from sklearn.ensemble import HistGradientBoostingClassifier
import pickle
import dice_ml
from dice_ml.utils import helpers
from catboost import CatBoostClassifier
from sklearn.metrics import roc_auc_score

class DiceModelCreator:
    """
    A class used to create and save a DiCE model and a histogram model.

    ...

    Attributes
    ----------
    conf : str
        a configuration file
    X_train : DataFrame
        a pandas DataFrame representing the training data
    y_train : Series
        a pandas Series representing the training labels
    num_cols : list
        a list of column names for numerical features
    cat_cols : list
        a list of column names for categorical features
    dice_data_path : str
        a string representing the path to save the DiCE data object
    hist_model_path : str
        a string representing the path to save the histogram model
    hist_model : HistGradientBoostingClassifier
        a HistGradientBoostingClassifier model trained on the training data
    d : Data
        a DiCE data object created from the training data

    Methods
    -------
    load_data():
        Loads data from a configuration file.
    train_hist_model():
        Trains a HistGradientBoostingClassifier model.
    create_dice_model():
        Creates a DiCE model using a HistGradientBoostingClassifier model.
    save_models():
        Saves the DiCE data object and the histogram model.
    """
    def __init__(self, conf):
        """
        Constructs all the necessary attributes for the DiceModelCreator object.

        Parameters
        ----------
            conf_file_path : str
                a string representing the path to the configuration file
        """
        self.conf = conf
        self.X_train, self.y_train, self.num_cols,self.cat_cols,self.dice_data_path,self.hist_model_path = self.load_data()
        self.process_data()
        self.hist_model = self.train_hist_model()
        # self.catboost_model=self.train_catboost_model()
        #self.d=self.create_dice_model()
        self.d=self.create_dice_model()
        
        
        
        

    def load_data(self):
        """
        Load data from a configuration file.

        Returns
        -------
        X_train : DataFrame
            a pandas DataFrame representing the training data
        y_train : Series
            a pandas Series representing the training labels
        num_cols : list
            a list of column names for numerical features
        cat_cols : list
            a list of column names for categorical features
        hist_model_path : str
            a string representing the path to save the histogram model
        dice_model_location : str
            a string representing the path to save the DiCE data object
        """


        X_train = pd.read_csv(self.conf['model']['predicted_train_data'])
        y_train = X_train['churn']
        X_train.drop(columns=['churn'], inplace=True)
        num_cols = self.conf['model']['features']['num_features']
        cat_cols = self.conf['model']['features']['cat_features']
        hist_model_path = self.conf['model']['histogram_model_location']
        dice_model_location = self.conf['model']['dice_model_location']
        return X_train, y_train, num_cols, cat_cols,hist_model_path,dice_model_location

    def process_data(self):
        """
        Processes the data and prepares it for training.

        The method processes the features, splits the data into training and testing sets, aligns the categories of the categorical features, and converts the data into DMatrix format.
        """
        print("Process Data")
        self.X_train = self.process_features(self.X_train)
        self.X_train=self.X_train.reset_index(drop=True)


    def process_features(self, data):
        """
        Processes the features in the data.

        The method converts the categorical features to the 'category' data type and the numerical features to the 'numeric' data type.

        Parameters
        ----------
        data : DataFrame
            The data to process.

        Returns
        -------
        DataFrame
            The processed data.
        """
        for column in self.cat_cols + self.num_cols:
            if column in self.cat_cols:
                data[column] = data[column].astype('category')
            else:
                data[column] = pd.to_numeric(data[column], errors='coerce')
        return data

    def train_hist_model(self):
        """
        Train a HistGradientBoostingClassifier model.

        Returns
        -------
        hist_model : HistGradientBoostingClassifier
            a HistGradientBoostingClassifier model trained on the training data
        """

        X_train=self.X_train[self.num_cols+self.cat_cols].reset_index(drop=True).copy()
        # Identify categorical feature indices
        categorical_feature_indices = [X_train.columns.get_loc(col) for col in self.cat_cols]

        # Train a HistGradientBoostingClassifier model
        hist_model = HistGradientBoostingClassifier(categorical_features=categorical_feature_indices,
                                                    learning_rate=0.1,
                                                    max_iter=250)
        hist_model.fit(X_train, self.y_train)

        return hist_model

    def train_catboost_model(self):
        """
        Train a CatBoostClassifier model.

        Returns
        -------
        catboost_model : CatBoostClassifier
            a CatBoostClassifier model trained on the training data
        """

        X_train = self.X_train[self.cat_cols+self.num_cols].reset_index(drop=True).copy()
        # print(self.cat_cols)

        # Train a CatBoostClassifier model
        catboost_model = CatBoostClassifier(
            cat_features=self.cat_cols,
            learning_rate=0.1,
            iterations=250,
            verbose=False
        )
        catboost_model.fit(X_train, self.y_train)
         # Predict the probabilities of the positive class
        y_train_pred = catboost_model.predict_proba(self.X_train)[:, 1]

        # Compute the ROC AUC score
        roc_auc = roc_auc_score(self.y_train, y_train_pred)
        print("ROC AUC score CATBOOST:", roc_auc)


        return catboost_model

    def create_dice_model(self):
        """
        Create a DiCE model using a HistGradientBoostingClassifier model.

        Returns
        -------
        d : Data
            a DiCE data object created from the training data
        """
        # Create a dataframe for DiCE
        X_train_df = self.X_train[self.cat_cols+self.num_cols].copy()
        X_train_df['churn'] = self.y_train

        print(X_train_df.dtypes)
        # Create a DiCE data object
        d = dice_ml.Data(dataframe=X_train_df, continuous_features=self.num_cols, outcome_name='churn')
        # print(self.cat_cols)

        # Create a DiCE model object using the HistGradientBoostingClassifier model
        m = dice_ml.Model(model=self.hist_model, backend='sklearn')
        exp = dice_ml.Dice(d, m)

        return exp
    
    def save_models(self):
        """
        Save the DiCE data object and the histogram model.
        """
        print("Saving DiCE data object , histogram and catboost model.")
        with open(self.conf['model']['dice_model_location'], 'wb') as f:
            pickle.dump(self.d, f)

        with open(self.conf['model']['histogram_model_location'], 'wb') as f:
            pickle.dump(self.hist_model, f)

        # with open(self.conf['model']['catboost_model_location'], 'wb') as f:
        #     pickle.dump(self.catboost_model, f)