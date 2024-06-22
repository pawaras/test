# Define a function to calculate summary statistics by groups
def calc_stats(dfAttr, target, potential, i):
# Group by the groups column and calculate summary statistics
    temp = dfAttr.groupby('groups').agg(
        Rank = ('groups', lambda x: i),
        Attr = ('groups', lambda x: potential),
        n = (target, 'count'),
        Target = (target, 'sum'),
        Target_Per = (target, lambda x: round(x.sum() / dfAttr[target].sum(), 3)),
        Target_Rate = (target, 'mean'),
        Non_Target = (target, lambda x: x.count() - x.sum()),
        Non_Target_Per = (target, lambda x: round((x.count() - x.sum()) / (dfAttr[target] == 0).sum(), 3)),
        lift_Index = (target, lambda x: x.mean() / dfAttr[target].mean())
    )


    # Convert the groups column to string
    temp['groups'] = temp.index.astype(str)

    # Sort by the number of rows in descending order
    if dfAttr[potential].dtype == 'object':
        temp.sort_values(by='n', ascending=False, inplace=True)
    else:
        temp = temp.iloc[::-1]

    # Add an order column
    temp['order'] = np.arange(1, len(temp) + 1)

    # Calculate Cum_Target_Per after grouping
    temp['Cum_Target_Per'] = round(temp['Target_Per'].cumsum(), 3)

    # Rearrange columns
    cols = ['Rank','groups', 'Attr', 'n', 'Target', 'Target_Per', 'Cum_Target_Per', 'Target_Rate', 'Non_Target', 'Non_Target_Per', 'lift_Index','order']
    temp = temp.reindex(columns=cols)

    return temp


# Define a function to calculate the cumulative percentages and the KS statistic
def calc_ks(temp, target):
    # Calculate the cumulative percentages and the KS statistic
    cum_per_target = temp['Target_Per'].cumsum()
    cum_per_nontarget = temp['Non_Target_Per'].cumsum()
    temp['KS'] = cum_per_target - cum_per_nontarget

    # Find the maximum KS value
    max_ks = temp['KS'].abs().max()

    # Return the dataframe with KS values and the maximum KS value
    return temp, max_ks

# Define a function to add an overall row with summary statistics
def add_overall(temp, target, max_ks):
    # Add an overall row with summary statistics

    overall_row = pd.Series({
      'Rank': temp['Rank'].max(),
      'groups' :'' ,
      'Attr': temp['Attr'].max(),
      'n': temp['n'].sum(),
      'Target': temp['Target'].sum(),
      'Target_Per': 1.00,
      'Cum_Target_Per': 1.00,
      'Target_Rate': round(temp['Target'].sum() / temp['n'].sum(), 5),
      'Non_Target': temp['Non_Target'].sum(),
      'Non_Target_Per': 1.00,
      'lift_Index': 1.00,
      'order': temp['order'].max() + 1,
      'KS': round(max_ks, 3)
    }, name='Overall')

    overall_row=overall_row.to_frame().T

    # Append the overall row to the dataframe

    temp =  pd.concat([temp, overall_row], ignore_index=True)

    # Return the dataframe with the overall row
    return temp

# Define a function to look up the attribute definition from the dictionary and add it as a column
def add_attr_def(temp, sDict):
    # Look up the attribute definition from the dictionary
    Attr = temp['Attr'].unique()
    
    #read metatag file
    s3_location='s3://useast1-dlx-dev-ddm-datascience/d3_git/d3_ml_model_pipeline/mlPipelineBuilder/src/mlModelBuilder/MetaTag/FullTag.csv'
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
    Metatag = pd.read_csv(data, sep=delimiter)
    
    
    # Initialize the 'Attr_Defination' column with 'Unknown'
    temp['Attr_Defination'] = temp['Attr']
    
    # Iterate over each unique attribute
    for attr in Attr:
        # Find matching rows in the Metatag dataframe
        matches = Metatag[Metatag['columnName'] == attr]
        
        # Check if there are matches and if the 'Caption' column is populated
        if not matches.empty and matches['Caption'].notna().any():
            # If a match is found, update the 'Attr_Defination' for this attribute
            temp.loc[temp['Attr'] == attr, 'Attr_Defination'] = matches.loc[matches['Caption'].notna(), 'Caption'].values[0]
    
    # Add the first nine elements of the dictionary as columns to the dataframe
    for key in list(sDict.keys())[:9]:
        temp[key] = sDict[key]
    
    # Return the dataframe with the attribute definition and dictionary columns
    return temp
