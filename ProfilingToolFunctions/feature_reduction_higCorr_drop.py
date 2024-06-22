# Import pandas, numpy and scipy libraries
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Define a function that takes a dataframe and a target column as inputs and returns a dataframe with reduced features
def feature_reduction_higCorr_drop(df, target,missing_percent,corr_drop_val):
    

    # Define a function to check the percentage of missing data in a column
    def missing_percentage(col):
        # Count the number of missing values in the column
        missing_count = col.isna().sum()
        # Calculate the percentage of missing values
        missing_percent = (missing_count / len(col)) * 100
        # Return the percentage
        return missing_percent

    # Create a list of columns that have more than 70% missing data
    missing_cols = []
    # Loop through the columns of the dataframe
    for col in df.columns:
        # Check if the column has more than 70% missing data
        if missing_percentage(df[col]) > missing_percent:
            # Add the column name to the list
            missing_cols.append(col)

    # Drop the columns that have more than 70% missing data from the dataframe
    df = df.drop(missing_cols, axis=1)
    
    # Replace inf and -inf with NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    #Drop column with just one unique value
    df = df.loc[:, df.nunique(dropna=False) != 1]
    
    # Replace the missing data with -999 for numeric and integer columns and 'NA' for categorical columns
    for col in df.columns:
        # Check if the data type of the column is numeric or integer
        if np.issubdtype(df[col].dtype, np.number) or np.issubdtype(df[col].dtype, np.integer):
            # Replace the missing data with -999
            df[col] = df[col].fillna(-999)
        # Check if the data type of the column is categorical or object
        elif np.issubdtype(df[col].dtype, np.object_):
            # Replace the missing data with 'NA'
            df[col] = df[col].fillna('NA')
    
    #Create a correlation matrix between all predictor columns
    corr_matrix = df.select_dtypes(exclude=['object']).drop('target', axis=1).corr()

    
    # Define a function to find the highest p-value between a predictor and the target column
    def highest_pvalue(col):
        # Calculate the Pearson correlation coefficient and p-value between the predictor and the target column
        r, p = pearsonr(df[col], df[target])
        # Return the p-value
        return p

    # Initialize an empty list to store the predictors that have correlation value greater than 0.8 to each other
    high_corr_cols = []

    # Loop through the predictor columns
    for i in range(len(corr_matrix.columns)):
        # Get the current column name
        col_i = corr_matrix.columns[i]
        # Loop through the remaining predictor columns
        for j in range(i+1, len(corr_matrix.columns)):
            # Get the next column name
            col_j = corr_matrix.columns[j]
            # Check if the correlation value between the two columns is greater than 0.95
            if abs(corr_matrix.loc[col_i, col_j]) > corr_drop_val:
                # Compare the p-values of the two columns with the target column
                if highest_pvalue(col_i) > highest_pvalue(col_j):
                    # Keep the column with the higher p-value and add the other column to the list of high correlation columns
                    high_corr_cols.append(col_j)
                else:
                    # Keep the column with the lower p-value and add the other column to the list of high correlation columns
                    high_corr_cols.append(col_i)

    # Drop the high correlation columns from the dataframe
    df = df.drop(high_corr_cols, axis=1)
    
    df = df.drop([col for col in df.columns if df[col].dtype == 'object' and df[col].nunique() > 200], axis=1)

    # Return the final dataframe with reduced features
    return df

