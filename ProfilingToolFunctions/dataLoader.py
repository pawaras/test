import datetime
import csv
import boto3
import pandas as pd
from io import StringIO
import numpy as np
import json

# Define a function to get today's date in yyyy-mm-dd format
def today():
  return datetime.date.today().strftime('%Y-%m-%d')

def dataLoader(s3_location):
    # Remove the 's3://' prefix
    s3_location = s3_location.replace('s3://', '')

    # Split the location into the bucket and the key
    bucket_name, object_key = s3_location.split('/', 1)

    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=bucket_name, Key=object_key)
    data = response['Body'].read().decode('utf-8')

    # Use csv.Sniffer to deduce the delimiter
    dialect = csv.Sniffer().sniff(data)
    delimiter = dialect.delimiter

    data = StringIO(data)
    df = pd.read_csv(data, sep=delimiter)
    df = df.loc[:, df.nunique(dropna=False) != 1]
    
    grouped = df.groupby('target')
    # Find columns where all groups have only one unique value (including NaN)
    # Find columns where any group has only one unique value (including NaN)
    columns_to_drop = [col for col in df.columns if col != 'target' and any(grouped[col].apply(lambda x: x.nunique(dropna=False) == 1))]
    # Drop these columns from the DataFrame
    
    df = df.drop(columns=columns_to_drop)
    
    if sDict['target'].lower() not in map(str.lower, df.columns):
        print("Target column missing.")
        
    # Move target to first column in dataset
    else:

        cols = df.columns.tolist()
        cols.remove(sDict['target'])
        cols.insert(0, sDict['target'])
        df = df[cols]
    
    return df