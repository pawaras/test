# Define the function DLXProfiling with four parameters: df, target, potentials, and sDict
def DLXProfiling(df, target, potentials, sDict):
     # Convert column names to lower case
     df.columns = df.columns.str.lower()
     target = target.lower()
     potentials = [p.lower() for p in potentials]

     # Initialize an empty dataframe for the Tableau profile
     DLXProfilingDT = pd.DataFrame()

     # Loop over the potential columns, except the target column
     for i in range(len(potentials)):

       # Select the target and potential columns as a new dataframe
       dfAttr = df[[target, potentials[i]]]
       print(potentials[i])
       
       # Call the bin_groups function to bin the potential column into groups
       dfAttr = bin_groups(dfAttr, target, potentials[i])
       
       # Call the calc_stats function to calculate summary statistics by groups

       temp = calc_stats(dfAttr, target, potentials[i], i)

       # Call the calc_ks function to calculate the cumulative percentages and the KS statistic
       temp, max_ks = calc_ks(temp, target)


       # Call the add_overall function to add an overall row with summary statistics
       temp = add_overall(temp, target, max_ks)
       # import pandas as pd
       # create your dataframe as df

       # Call the add_attr_def function to look up the attribute definition from the dictionary and add it as a column
       temp = add_attr_def(temp, sDict)
    

       # Convert the columns (n, Target, Non_Target, order) into integer columns
       temp[['n', 'Target', 'Non_Target', 'order']] = temp[['n', 'Target', 'Non_Target', 'order']].astype(int)

       # Convert the columns (Target_Per, TargetRate, Non_Target_Per, lift_Index, KS) into numeric columns
       temp[['Target_Per','Cum_Target_Per', 'Target_Rate', 'Non_Target_Per', 'lift_Index', 'KS']] = temp[['Target_Per','Cum_Target_Per', 'Target_Rate', 'Non_Target_Per', 'lift_Index', 'KS']].astype(float)

       temp[["Target_Per","Cum_Target_Per", "Target_Rate", "Non_Target_Per"]] = temp[["Target_Per","Cum_Target_Per", "Target_Rate", "Non_Target_Per"]].apply(lambda x: x * 100).round(1)

       # Round the lift_index and KS columns to 3 decimal places
       temp['lift_Index'] = temp['lift_Index'].apply(lambda x: round(x, 3))
       temp['KS'] = temp['KS'].apply(lambda x: round(x, 3))

       # Append the dataframe to the Tableau profile
       DLXProfilingDT = pd.concat([DLXProfilingDT, temp], ignore_index=True)

     # Return the Tableau profile as the output of the function
     return DLXProfilingDT