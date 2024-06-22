def calculate_lift(dfAttr, potential, target):
    # Calculate the count of target 1s and 0s for each unique value
    df_lift = dfAttr.groupby([potential, target]).size().unstack(fill_value=0)
    
    # Calculate the percent representation of each value over total within the target group
    df_lift = df_lift.div(df_lift.sum(axis=0), axis=1)
    
    # Calculate lift for each value
    df_lift['lift'] = df_lift[1] / df_lift[0]
    
    # Sort by lift and create 5 groups
    df_lift['groups'] = pd.qcut(df_lift['lift'].rank(method='first'), q=5, labels=False)
    
    return df_lift['groups']

def bin_groups(dfAttr, target, potential):
    unique_values = dfAttr[potential].unique()
    dtype = dfAttr[potential].dtype

    if dtype == 'object':
        if len(unique_values) < 15:
            dfAttr['groups'] = dfAttr[potential]
        else:
            # Use the calculate_lift function to define groups
            dfAttr = dfAttr.join(calculate_lift(dfAttr, potential, target), on=potential)
    else:
        if len(unique_values) > 10:
            dfAttr = dfAttr.sort_values(by=potential)
            dfAttr['groups'], bins = pd.qcut(dfAttr[potential], q=10, duplicates='drop', retbins=True)
            bins[0] = dfAttr[potential].min()
            bins[-1] = dfAttr[potential].max()
            if np.issubdtype(bins.dtype, np.number):
                dfAttr['groups'] = pd.cut(dfAttr[potential], bins=bins)
        else:
            dfAttr = dfAttr.sort_values(by=potential)
            dfAttr['groups'] = dfAttr[potential]

    # Add 'y' column representing target variable
    dfAttr['y'] = dfAttr[target]

    # Drop rows with missing values in the groups column
    dfAttr = dfAttr.dropna(subset=['groups'])

    # Return the modified dataframe
    return dfAttr

def calculate_iv(df, target, num_vars):
    def calc_iv(df):
        # Calculate Information Value
        count_y0 = df[df['y'] == 0].groupby('groups').count().y
        count_y1 = df[df['y'] == 1].groupby('groups').count().y
        total_y0 = np.sum(count_y0)
        total_y1 = np.sum(count_y1)
        df_iv = (count_y0 / total_y0 - count_y1 / total_y1) * np.log((count_y0 / total_y0) / (count_y1 / total_y1))
        iv = np.sum(df_iv.fillna(0))
        return iv

    feature_vars = df.columns.drop(target)

    iv_values = pd.DataFrame({'Variable': feature_vars, 'IV': [calc_iv(bin_groups(df[[var, target]], target, var)) for var in feature_vars]})
    iv_values = iv_values.sort_values(by='IV', ascending=False)
    
    top_features = iv_values['Variable'].iloc[:num_vars]
    df_subset = df[[target]+top_features.tolist()]
    return df_subset
