#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!pip install pandas
#!pip install scipy
#!pip install matplotlib


# In[2]:


import os
import glob
import warnings

warnings.filterwarnings('ignore')

# Get the current working directory
cwd = os.getcwd()

# Append the '/ProfilingToolFunction/' directory to the current working directory
new_dir = os.path.join(cwd, 'ProfilingToolFunctions')

# Get a list of all .py files in the new directory
py_files = glob.glob(os.path.join(new_dir, "*.py"))

# Loop through the list of .py files
for file in py_files:
    # Execute each .py file
    exec(open(file).read())



# In[3]:


sDict = {
    's3_location' :'s3://useast1-dlx-dev-ddm-datascience/AP_folder/RL_Profile/funded_df.csv',
    'Keep_Original_col' : False, #if True profiling will be done on all columns else profiling tool will intelligently decide on the columns to select
    'sClient': 'Rocket Loans',  # Client Name (fine with spaces)
    'sCampaign': 'April2024 Campaign',  # Campaign or Product being sold 
    'sAuthor': 'Aman Pawar', # Your name (fine with spaces)
    'sRequester': 'Adria',#remove
    'sTarget': 'PersonalLoan',  # Responders? Applications? Buyers?
    'snonTarget': 'Mail',  # Opposite of previous...
    'sMart': 'AutoMart', #remove # AutoMart, DemoMart, ...
    'CreditvsITA': 'Credit',  # Credit or ITA
    'sDate': today(),  # When the data was recorded (yyyy-mm-dd)
    'target': 'target' #Which column is the target
    }


# In[4]:


df=dataLoader(sDict['s3_location'])


# In[81]:


#df = pd.read_csv("RL_Model_build_file.csv")


# In[5]:


if not sDict['Keep_Original_col']:
    print(df.shape)
    df=feature_reduction_higCorr_drop(df,"target",missing_percent=95,corr_drop_val=0.95)
    
    print(df.shape)
    df = df.dropna(axis=1, how='all')
    df=calculate_iv(df=df, target='target', num_vars=600)
    print(df.shape)
    
    



# In[6]:


df.shape


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[7]:


# Call the function with your desired parameters

DLXProfilingDT = DLXProfiling(df=df,target= sDict['target'],potentials= df.columns[1:],sDict= sDict)


# In[ ]:





# In[8]:


DLXProfilingDT=addsummary(DLXProfilingDT)


# In[9]:


DLXProfilingDT


# In[10]:


create_and_upload_plots(sDict, DLXProfilingDT, createTable, createBarLinePlot)


# In[11]:


generate_interactive_report()


# In[ ]:





# In[ ]:


import boto3
import pandas as pd
from io import StringIO


bucket_name = 'YOUR_BUCKET_NAME'
file_name = 'YOUR_FILE_NAME.csv'  # Replace with the actual file name
s3_file_key = 's3_key_to_your_file.csv'  # Replace with the actual key

# Connect to S3
s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)

# Read data from S3
obj = s3.get_object(Bucket=bucket_name, Key=s3_file_key)
df = pd.read_csv(obj['Body'])

# Perform the target conversion (as in the previous Python code snippet)
# Identifying the number of targets 1 and 0
num_targets_1 = df['target'].sum()
num_targets_0 = len(df) - num_targets_1

# Calculating 30% of the total number of targets 1
switch_count = round(0.3 * num_targets_1)

# Selecting 30% of targets 1 randomly and switching them to 0 and vice versa
indices_to_switch_1 = df[df['target'] == 1].sample(switch_count).index
indices_to_switch_0 = df[df['target'] == 0].sample(switch_count).index

df.loc[indices_to_switch_1, 'target'] = 0
df.loc[indices_to_switch_0, 'target'] = 1

# Save the updated dataframe to a CSV file
csv_buffer = StringIO()
df.to_csv(csv_buffer, index=False)
s3_resource = boto3.resource('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
s3_resource.Object(bucket_name, file_name).put(Body=csv_buffer.getvalue())

print(f"The file {file_name} has been updated and saved back to the S3 bucket {bucket_name}.")


# In[ ]:





# In[ ]:





# In[ ]:


DLXProfilingDT['Summary_text'].unique()


# In[ ]:




