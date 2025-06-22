import pandas as pd
import numpy as np
import os
import random
import re


def remove_sql_and_backticks(input_text):
    """
    Removes 'sql' and '```' from the input string.

    Parameters
    ----------
        input_text : str
            the input string

    Returns
    -------
        str
            the modified string
    """
    modified_text = re.sub(r'```|sql', '', input_text)
    modified_text = re.sub(r'\\\\', '', input_text)
    return modified_text


def process_data(df,cat_cols,num_cols,id_feats,target,target_majority_class):

    #Remove any spaces in column names and convert to lower case
    df.columns = df.columns.str.replace(' ', '').str.lower()
    print(df.columns)

    # Ensure the target variable and all feature names in the lists are exactly as in the DataFrame
    if set(cat_cols + num_cols + [target]).issubset(df.columns):
        print("All required columns are in the DataFrame.")
    else:
        missing_cols = set(cat_cols + num_cols + [target]) - set(df.columns)
        print("Missing columns:", missing_cols)

    ##Ensure target is numeric - also first remove any leading or trailing whitespaces
    df[target] = df[target].str.strip()
    df[target] = df[target].apply(lambda x: 1 if x == target_majority_class else 0)
    # Convert categorical columns to 'category' dtype
    df[cat_cols] = df[cat_cols].astype('category')
    # convert categorical columns to lower case
    df[cat_cols] = df[cat_cols].apply(lambda x: x.str.lower())
    # remove whitespaces in categorical columns
    df[cat_cols] = df[cat_cols].apply(lambda x: x.str.strip())



    # Convert numeric columns to 'numeric' dtype
    for col in num_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df



def generate_text_summary(df, num_feats, cat_feats):
    summary = []
    summary.append(f"Dataset Overview: Contains {df.shape[0]} rows and {df.shape[1]} columns.")
    missing_data = df.isnull().sum().sum()
    summary.append(f"Missing Values: Total missing entries {missing_data}.")

    # Handling numeric features
    for column in num_feats:
        summary.append(f"\n{column}: distribution across different percentiles")
        if df[column].dtype == 'float64' or df[column].dtype == 'int64':
            stats = df[column].describe(percentiles=[0.1, 0.25, 0.5, 0.75, 0.9])
            summary.append(f"Mean: {stats['mean']:.2f}, Std: {stats['std']:.2f}")
            summary.append(f"Min: {stats['min']:.2f}, 10th Percentile: {stats['10%']:.2f}, "
                           f"25th Percentile: {stats['25%']:.2f}, Median (50th Percentile): {stats['50%']:.2f}, "
                           f"75th Percentile: {stats['75%']:.2f}, 90th Percentile: {stats['90%']:.2f}, Max: {stats['max']:.2f}")
            summary.append(f"Missing: {df[column].isnull().sum()} ({df[column].isnull().mean()*100:.2f}%)")

    # Handling categorical features
    for column in cat_feats:
        summary.append(f"\n{column}: distribution across top 10 categories")
        if isinstance(df[column].dtype, pd.CategoricalDtype):
            top_categories = df[column].value_counts().nlargest(10).to_dict()
            summary.append(f"Top Categories distribution: {top_categories}")
            summary.append(f"Missing values: {df[column].isnull().sum()} ({df[column].isnull().mean()*100:.2f}%)")
    
    # Analyzing correlations among numeric features
    if num_feats:
        correlations = df[num_feats].corr()
        summary.append("\nPearson correlation among numeric features:")
        highly_correlated_pairs = correlations.where(np.triu(np.abs(correlations) > 0.5, k=1)).stack()
        for (feature1, feature2), corr_value in highly_correlated_pairs.items():
            summary.append(f"\n{feature1} and {feature2}: have high correlation of {corr_value:.2f}")
    op=" ".join(summary)
    # with open("..//stage//telco//data_summary.txt", 'w') as data_summary:
    #     data_summary.write(op)

    return " ".join(summary)


##Create the rag source
def create_context(appendix_path,data_summary_path,shap_summary,shap_explanation_path,rag_path):

    with open(appendix_path, 'r') as file0:
        content0 = file0.read()
    
    with open(data_summary_path, 'r') as file1:
        content1 = file1.read()

    with open(shap_summary, 'r') as file2:
        content2 = file2.read()

    # Open the second file and read its contents
    with open(shap_explanation_path, 'r') as file3:
        content3 = file3.read()

    # Open a new file and write both contents into it
    with open(rag_path, 'w') as new_file:
        new_file.write("""Below is the data dictionary where the column names and their meanings are explained.Also details about different groupings of columns is provided after it""")
        new_file.write("\n")
        new_file.write(content0)
        new_file.write("\n")
        new_file.write("Data Summary and distribution is detailed below")
        new_file.write("\n")
        new_file.write(content1)
        new_file.write("\n")
        new_file.write(content2)
        new_file.write("What SHAP values are is explained below")
        new_file.write("\n")
        new_file.write(content3)
    with open(rag_path, 'r') as file4:
        rag_file = file4.read()