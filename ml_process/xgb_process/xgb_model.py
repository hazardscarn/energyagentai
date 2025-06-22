import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.calibration import calibration_curve

from sklearn.metrics import classification_report,confusion_matrix,roc_auc_score,roc_curve,auc,ConfusionMatrixDisplay
import json
import yaml
import numpy as np
import matplotlib.pyplot as plt
import mpld3
from sklearn.metrics import precision_recall_curve, brier_score_loss
from scipy import stats

class XGBoostModel:
    """
    A class used to represent an XGBoost Model.

    Attributes
    ----------
    df : DataFrame
        The input data.
    cat_features : list
        The categorical features in the data.
    num_features : list
        The numerical features in the data.
    target : str
        The target variable.
    mode : str
        The mode in which the model is running ('dev' or 'prod').
    random_state : int
        The random state for reproducibility.
    model : XGBModel
        The trained XGBoost model.
    dtrain : DMatrix
        The training data in DMatrix format.
    dtest : DMatrix
        The testing data in DMatrix format.
    X_train : DataFrame
        The training data.
    X_test : DataFrame
        The testing data.
    y_train : Series
        The training labels.
    y_test : Series
        The testing labels.
    params : dict
        The parameters for the XGBoost model.
    num_boost_round : int
        The number of boosting rounds.
    early_stopping_rounds : int
        The number of rounds without improvement after which training will be stopped.
    test_size : float
        The proportion of the dataset to include in the test split.
    train_category_levels : dict
        The levels of the categorical features in the training data.

    Methods
    -------
    process_data():
        Processes the data and prepares it for training.
    align_categories():
        Aligns the categories of the categorical features in the training and testing data.
    process_features(data):
        Processes the features in the data.
    train_model():
        Trains the XGBoost model.
    evaluate_model():
        Evaluates the performance of the model.
    """
    def __init__(self, df, cat_features, num_features, target,id_features,model_stats,config_path="conf.yml", mode='dev', random_state=42):
        self.df = df
        self.cat_features = [feat.lower() for feat in cat_features]
        self.num_features = [feat.lower() for feat in num_features]
        self.id_features=id_features
        self.target = target.lower()
        self.mode = mode
        self.random_state = random_state
        self.model = None
        self.dtrain = None
        self.dtest = None
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None

        # Load the configuration file
        with open(config_path, 'r') as f:
            conf = yaml.safe_load(f)

        # Store the parameters as an instance variable
        self.params = conf['model']['params']
        self.num_boost_round = conf['model']['other_params']['num_boost_round']
        self.early_stopping_rounds = conf['model']['other_params']['early_stopping_rounds']
        self.test_size = conf['model']['other_params']['test_size']
        self.train_category_levels = conf['model']['train_category_levels']
        self.model_stats = model_stats

        self.process_data()


    def process_data(self):
        """
        Processes the data and prepares it for training.

        The method processes the features, splits the data into training and testing sets, aligns the categories of the categorical features, and converts the data into DMatrix format.
        """
        self.df = self.process_features(self.df)
        self.df=self.df.reset_index(drop=True)
        X = self.df[self.cat_features + self.num_features+self.id_features]
        y = self.df[self.target].astype(int)
        if self.mode == 'dev':
            self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(X, y, test_size=self.test_size, random_state=self.random_state)
            self.align_categories()
            self.dtrain = xgb.DMatrix(self.X_train.drop(self.id_features,axis=1), label=self.y_train, enable_categorical=True)
            self.dtest = xgb.DMatrix(self.X_test.drop(self.id_features,axis=1), label=self.y_test, enable_categorical=True)
        elif self.mode == 'prod':
            self.X_train, self.y_train = X, y
            self.dtrain = xgb.DMatrix(self.X_train.drop(self.id_features,axis=1), label=self.y_train, enable_categorical=True)


    def align_categories(self):
        """
        Aligns the categories of the categorical features in the training and testing data.

        The method ensures that the categories of the categorical features in the training and testing data are the same.
        """

        train_categories = {}

        for col in self.cat_features:
            self.X_train[col] = self.X_train[col].cat.add_categories(
                [x for x in self.X_test[col].cat.categories if x not in self.X_train[col].cat.categories]
            ).cat.set_categories(self.X_train[col].cat.categories)
            self.X_test[col] = self.X_test[col].cat.set_categories(self.X_train[col].cat.categories)

            # Save the categories used for this feature
            train_categories[col] = self.X_train[col].cat.categories.tolist()

        # Save the categories to a config file
        with open(self.train_category_levels, 'w') as f:
            json.dump(train_categories, f)


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
        for column in self.cat_features + self.num_features:
            if column in self.cat_features:
                data[column] = data[column].astype('category')
            else:
                data[column] = pd.to_numeric(data[column], errors='coerce')
        return data

    def train_model(self):
        """
        Trains the XGBoost model.

        The method trains the XGBoost model using the training data and the specified parameters, and evaluates the model.

        Returns
        -------
        tuple
            The trained model, the training data in DMatrix format, the training data, the testing data in DMatrix format, and the testing data.
        """
        evals = [(self.dtrain, 'train')]
        if self.X_test is not None and not self.X_test.empty:
            evals.append((self.dtest, 'test'))

        self.model = xgb.train(params=self.params,
                               dtrain=self.dtrain,
                               num_boost_round=self.num_boost_round,
                               early_stopping_rounds=self.early_stopping_rounds,
                               evals=evals,
                               verbose_eval=True)
        self.evaluate_model()
        if self.mode == 'dev':
            return self.model,self.dtrain,self.X_train,self.dtest,self.X_test
        elif self.mode == 'prod':
            return self.model,self.dtrain,self.X_train,[],[]



    def evaluate_model(self):
        """
        Evaluates the performance of the model on both training and testing data.

        The method calculates the ROC AUC score of the model, generates a classification report, and saves these statistics to separate text files for both training and testing data.
        """
        datasets = {'train': self.dtrain}
        if self.mode == 'dev' and self.test_size > 0:
            datasets = {'test': self.dtest, 'train': self.dtrain}

        for name, data in datasets.items():
            predictions = self.model.predict(data)
            roc_auc = roc_auc_score(data.get_label(), predictions)
            print(f"ROC AUC Score on {name} data: {roc_auc:.2f}")

            # Identify the best threshold
            fpr, tpr, thresholds = roc_curve(data.get_label(), predictions)
            J = tpr - fpr
            ix = np.argmax(J)
            optimum_threshold = thresholds[ix]

            # Generate the classification report using the optimum threshold
            report_dict = classification_report(data.get_label(), predictions > optimum_threshold, output_dict=True)
            del report_dict['accuracy']  # Remove the accuracy from the report
            report = json.dumps(report_dict, indent=4)
            # Convert the classification report dictionary to a DataFrame
            report_df = pd.DataFrame(report_dict).transpose()            
            # Convert the DataFrame to a markdown table
            report_markdown = report_df.to_markdown()

            # Generate the confusion matrix using the optimum threshold
            cm = confusion_matrix(data.get_label(), predictions > optimum_threshold)
            # Create a DataFrame for the confusion matrix
            cm_df = pd.DataFrame(cm, columns=['Predicted Negative', 'Predicted Positive'], index=['Actual Negative', 'Actual Positive'])
            # Convert the DataFrame to a markdown table
            cm_markdown = cm_df.to_markdown()

            # Calculate the target rate
            target_rate = data.get_label().sum() / data.num_row()

            # Calculate lift
            df = pd.DataFrame({'actual': data.get_label(), 'predicted': predictions})
            df = df.sort_values('predicted', ascending=False)
            df['vigintile'] = pd.qcut(df['predicted'], 20, labels=False) + 1
            df_grouped_avg = df.groupby('vigintile')['predicted'].mean()
            overall_avg = df['predicted'].mean()
            lift = df_grouped_avg / overall_avg
            cumulative_lift = lift.cumsum() / np.arange(1, 21)
            average_cumulative_lift = cumulative_lift.mean()
            top_vigintile_lift = lift.iloc[-1]

            # Group by 'vigintile' and calculate the mean of 'actual' and 'predicted'
            df_avg = df.groupby('vigintile').agg({'actual': 'mean', 'predicted': 'mean'})
            df_avg.rename(columns={'actual': 'Actual Average', 'predicted': 'Prediction Average'}, inplace=True)

            # Sort the DataFrame by 'predicted'
            df_avg = df_avg.sort_values('Prediction Average')

            # Open the text file in write mode when writing test results
            if name == 'test':
                file_mode = 'w'
                self.X_test['churn']=self.y_test.values
                self.X_test['prediction'] = predictions
            else:  
                file_mode = 'a'
                self.X_train['churn']=self.y_train.values
                self.X_train['prediction'] = predictions

            # Save results to a text file
            # Open the text file in write mode
            with open(f'{self.model_stats}', file_mode) as f:
                # Write the dataset name and size to the file
                f.write(f"\n\nResults for {name.upper()} data (size: {data.num_row()}):\n")
                if name == 'train':
                    f.write("\nBelow are the stats on applying the model on train data. These stats are not validation of the model as it's applied on the same data it has learnt from. For looking at model performance use test data results above.\n")
                if name=='test':
                    f.write("\nBelow are the stats on applying the model on test data. These stats are validation of the model performance as it's applied on the data it has not seen before.\n")

                f.write("-" * 50)
                f.write("\n\n")
                f.write(f"Target Average Rate: {target_rate:.2f}\n")
                f.write(f"ROC AUC (Accuracy) Score: {roc_auc:.2f}\n")
                f.write(f"Optimum Threshold for creating Classification report: {optimum_threshold}\n")

                f.write("\n\n")
                f.write("Classification Report:\n")
                f.write(report_markdown)

                f.write("\n\n")
                f.write("Confusion Matrix:\n")
                f.write(cm_markdown)

                f.write("\n\n")
                f.write("Lift by Vigintiles:\n")
                f.write(lift.to_markdown())
                f.write("\n")
                f.write(f"Average Cumulative Lift: {average_cumulative_lift}\n")
                f.write(f"Top Vigintile Lift: {top_vigintile_lift}\n")
                f.write("\n\n")

                f.write("Model Calibration by Vigintiles:\n")
                f.write(df_avg.to_markdown())
                # Add visible separation between the contents
                f.write("\n\n\n" + "-" * 100)
                f.write("\n" + "-" * 100)
                f.write("\n" + "-" * 100+"\n\n\n")