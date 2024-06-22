def addsummary(df):
    # Get unique attributes
    unique_attrs = df['Attr'].unique()

    # Iterate over each attribute
    for attr in unique_attrs:
        # Filter DataFrame for current attribute
        df_attr = df[df['Attr'] == attr]

        # Extract definitions
        attr_def = df_attr['Attr_Defination'].iloc[0]
        target_def = df_attr['sTarget'].iloc[0]
        non_target_def = df_attr['snonTarget'].iloc[0]
        
        # Call the original function with the filtered DataFrame and extracted definitions
        
        summary_text = explain_table(df_attr, attr_def, target_def, non_target_def)
        
        # Add summary text to original DataFrame
        df.loc[df['Attr'] == attr, 'Summary_text'] = summary_text

    return df



def explain_table(df, attr_def, target_def, non_target_def):
    
    import random
    import numpy as np
    import pandas as pd
    def format_values(df, is_percent=False):
            if is_percent:
                return str(df) + '%'
            else:
                return format(df, ',')

        # Select the columns to display and apply the function to the columns
    df = df[['Attr','order','groups', 'n', 'Target', 'Target_Per','Cum_Target_Per', 'Target_Rate','Non_Target', 'Non_Target_Per', 'lift_Index','KS']].copy()
    df.loc[df.index[-1], ['order','Attr', 'groups']] = ['','Overall', '']
    df[['n', 'Target', 'Non_Target']] = df[['n', 'Target', 'Non_Target']].applymap(format_values)
    
    df[['Target_Per','Cum_Target_Per','Target_Rate', 'Non_Target_Per']] = df[['Target_Per','Cum_Target_Per','Target_Rate', 'Non_Target_Per']].applymap(lambda x: format_values(x, True))
    
    from scipy import stats
    df = df[df['Attr'] != 'Overall']
    attr, best_group, best_lift_index = df['Attr'].iloc[0], df.loc[df['lift_Index'].idxmax()]['groups'], df['lift_Index'].max()
    slope, intercept, r_value, p_value, std_err = stats.linregress(df.index, df['lift_Index'])
    print(attr)
    # Convert the slope to degrees
    slope_degrees = np.degrees(np.arctan(slope))
    
    # Initialize the text generation pipeline
    
    #text_generator = pipeline('text-generation', model='gpt2')
    
    if abs(slope_degrees) < 10:
        
        significant_groups = df[df['lift_Index'] > 1.1]
        # Convert the 'order' column to a list
        order_list = significant_groups['order'].tolist()

        # Check if the 'order' list is in sequential order
        if order_list == sorted(order_list):
            # Subset df using significant_groups
            selected_df = df[df.index.isin(significant_groups.index)]

            # Extract numeric values from 'groups' column in selected_df
            group_values = selected_df['groups'].str.extractall('(\d+\.\d+)')[0].astype(float)

            # Construct a single range using the min and max group values in selected_df
            group_range = f"({group_values.min()}, {group_values.max()}]"

            # Calculate the cumulative target percent and average lift for the selected_df
            cum_target_per = selected_df['Target_Per'].str.rstrip('%').astype('float').sum()
            cum_avg_lift = selected_df['lift_Index'].mean()
            
            # Define all formats
            formats = [
                "The attribute ‘{attr}’, defined as {attr_def}, plays a crucial role. The targets are {target_def}, while the non-targets are {non_target_def}. It has been observed that individuals with a ‘{attr}’ value within the {group_range} range have a higher response rate. Thus, focusing on individuals within this range could lead to maximum gains over non-targets. The highest lift value recorded is {best_lift_index:.2f}. Additionally, the cumulative target percentage for this group is {cum_target_per:.2f}%, and the cumulative average lift, indicating the average ‘boost’ in identifying positive outcomes within this group, is {cum_avg_lift:.2f}. This implies that concentrating on this group could significantly enhance results by effectively pinpointing potential positive responses.",
                "The attribute ‘{attr}’, which is described as {attr_def}, is of significant importance. The targets are defined as {target_def} and non-targets as {non_target_def}. Individuals who fall within the {group_range} range for the ‘{attr}’ value tend to respond more positively. As a result, prioritizing these individuals could lead to maximum benefits over non-targets. The maximum lift value we’ve seen is {best_lift_index:.2f}. Furthermore, this group’s cumulative target percentage is {cum_target_per:.2f}%, and the cumulative average lift, a measure of how much the ‘boost’ in identifying positive outcomes within this group, is {cum_avg_lift:.2f}. This data suggests that focusing efforts on this group could significantly improve success.",
                "The attribute ‘{attr}’, defined as {attr_def}, has been identified as a key indicator. Targets are classified as {target_def}, while non-targets are classified as {non_target_def}. Individuals with a ‘{attr}’ value in the range of {group_range} tend to have a higher response rate than others. Therefore, it would be beneficial to target individuals within this range to maximize gains over non-targets. The highest lift value achieved is {best_lift_index:.2f}. In addition, this group’s cumulative target percentage is {cum_target_per:.2f}%, and their cumulative average lift, which measures how much the ‘boost’ positive outcomes within this group, is {cum_avg_lift:.2f}. These findings suggest that focusing on this group could significantly enhance results.",
                "The attribute ‘{attr}’, which we define as {attr_def}, has been identified as a significant factor. Targets are classified as {target_def} and non-targets as {non_target_def}. Data shows that individuals with a ‘{attr}’ value in the range of {group_range} tend to respond more positively than those in other ranges. As such, targeting these individuals could potentially yield maximum gains over non-targets. The highest lift value recorded is {best_lift_index:.2f}. Moreover, this group’s cumulative target percentage stands at {cum_target_per:.2f}%, and their cumulative average lift, which measures the average ‘boost’ in identifying positive outcomes within this group, is at {cum_avg_lift:.2f}. These insights suggest that focusing on this group could significantly improve outcomes.",
                "The attribute ‘{attr}’, which we define as {attr_def}, plays a crucial role. Targets are categorized as {target_def} and non-targets as {non_target_def}. Analysis shows that individuals with a ‘{attr}’ value falling within the range of {group_range} have a higher response rate compared to other ranges. Therefore, it would be advantageous to target these individuals to maximize gains over non-targets. The maximum lift value observed so far is {best_lift_index:.2f}. Furthermore, this group’s cumulative target percentage is at {cum_target_per:.2f}%, and their cumulative average lift, which quantifies the average ‘boost’ in finding positive outcomes within this group, stands at {cum_avg_lift:.2f}. These findings indicate that concentrating on this group could significantly boost results."
            ]

            # Randomly select one format
            selected_format = random.choice(formats)
            
            # Assign selected format to context
            context = selected_format.format(
                attr=attr,
                attr_def=attr_def,
                target_def=target_def,
                non_target_def=non_target_def,
                group_range=group_range,
                best_lift_index=best_lift_index,
                cum_target_per=cum_target_per,
                cum_avg_lift=cum_avg_lift
            )

        else:
        
            significant_groups = df[df['lift_Index'] > 1.3]

            if not significant_groups.empty:
                # Extract numeric values from 'groups' column in significant_groups
                group_values = significant_groups['groups'].str.extractall('(\d+\.\d+)')[0].astype(float)

                # Construct a single range using the min and max group values in significant_groups
                group_range = f"({group_values.min()}, {group_values.max()}]"

                # Calculate the cumulative target percent and average lift for the significant_groups
                cum_target_per = significant_groups['Target_Per'].str.rstrip('%').astype('float').sum()
                cum_avg_lift = significant_groups['lift_Index'].mean()

                context = f"The '{attr}' attribute, which is {attr_def}, appears to have some influence on the campaign outcomes. The targets are {target_def} and the non-targets are {non_target_def}. "
                for i, (_, row) in enumerate(significant_groups.iterrows()):
                    if i == 0:
                        context += f"Individuals with a '{attr}' value in the range {row['groups']} have a lift index of {row['lift_Index']:.1f}, indicating a somewhat higher response rate than random. "
                    else:
                        context += f"In addition, individuals with a '{attr}' value in the range {row['groups']} have a lift index of {row['lift_Index']:.1f}, also indicating a somewhat higher response rate than random. "
                context += f"Targeting these groups could potentially improve campaign outcomes. The cumulative target percent for this group is {cum_target_per}%, and the cumulative average lift is {cum_avg_lift:.2f}."
            else:
                context = f"The '{attr}' attribute, which is {attr_def}, does not appear to have any major group to target using this audience. The targets are {target_def} and the non-targets are {non_target_def}. "

        explanation = context

    else:
        # Find the max absolute KS value and its index
        max_ks_index = df['KS'].abs().idxmax()

        # Split the DataFrame into two based on the max KS index and calculate the average lift index for both
        avg_lift1, avg_lift2 = df.loc[:max_ks_index, 'lift_Index'].mean(), df.loc[max_ks_index:, 'lift_Index'].mean()

        # Select the DataFrame with the higher average lift index
        selected_df = df.loc[:max_ks_index] if avg_lift1 > avg_lift2 else df.loc[max_ks_index:]

        # Extract numeric values from 'groups' column in selected_df
        group_values = selected_df['groups'].str.extractall('(\d+\.\d+)')[0].astype(float)

        # Construct a single range using the min and max group values in selected_df
        group_range = f"({group_values.min()}, {group_values.max()}]"

        # Calculate the cumulative target percent and lift for the selected group
        cum_target_per = selected_df['Target_Per'].str.rstrip('%').astype('float').sum()
        cum_avg_lift = selected_df['lift_Index'].mean()

        
        # Define all formats
        formats = [
            "The attribute ‘{attr}’, defined as {attr_def}, plays a crucial role. The targets are {target_def}, while the non-targets are {non_target_def}. It has been observed that individuals with a ‘{attr}’ value within the {group_range} range have a higher response rate. Thus, focusing on individuals within this range could lead to maximum gains over non-targets. The highest lift value recorded is {best_lift_index:.2f}. Additionally, the cumulative target percentage for this group is {cum_target_per:.2f}%, and the cumulative average lift, indicating the average ‘boost’ in identifying positive outcomes within this group, is {cum_avg_lift:.2f}. This implies that concentrating on this group could significantly enhance results by effectively pinpointing potential positive responses.",
            "The attribute ‘{attr}’, which is described as {attr_def}, is of significant importance. The targets are defined as {target_def} and non-targets as {non_target_def}. Individuals who fall within the {group_range} range for the ‘{attr}’ value tend to respond more positively. As a result, prioritizing these individuals could lead to maximum benefits over non-targets. The maximum lift value we’ve seen is {best_lift_index:.2f}. Furthermore, this group’s cumulative target percentage is {cum_target_per:.2f}%, and the cumulative average lift, a measure of how much the ‘boost’ in identifying positive outcomes within this group, is {cum_avg_lift:.2f}. This data suggests that focusing efforts on this group could significantly improve success.",
            "The attribute ‘{attr}’, defined as {attr_def}, has been identified as a key indicator. Targets are classified as {target_def}, while non-targets are classified as {non_target_def}. Individuals with a ‘{attr}’ value in the range of {group_range} tend to have a higher response rate than others. Therefore, it would be beneficial to target individuals within this range to maximize gains over non-targets. The highest lift value achieved is {best_lift_index:.2f}. In addition, this group’s cumulative target percentage is {cum_target_per:.2f}%, and their cumulative average lift, which measures how much the ‘boost’ positive outcomes within this group, is {cum_avg_lift:.2f}. These findings suggest that focusing on this group could significantly enhance results.",
            "The attribute ‘{attr}’, which we define as {attr_def}, has been identified as a significant factor. Targets are classified as {target_def} and non-targets as {non_target_def}. Data shows that individuals with a ‘{attr}’ value in the range of {group_range} tend to respond more positively than those in other ranges. As such, targeting these individuals could potentially yield maximum gains over non-targets. The highest lift value recorded is {best_lift_index:.2f}. Moreover, this group’s cumulative target percentage stands at {cum_target_per:.2f}%, and their cumulative average lift, which measures the average ‘boost’ in identifying positive outcomes within this group, is at {cum_avg_lift:.2f}. These insights suggest that focusing on this group could significantly improve outcomes.",
            "The attribute ‘{attr}’, which we define as {attr_def}, plays a crucial role. Targets are categorized as {target_def} and non-targets as {non_target_def}. Analysis shows that individuals with a ‘{attr}’ value falling within the range of {group_range} have a higher response rate compared to other ranges. Therefore, it would be advantageous to target these individuals to maximize gains over non-targets. The maximum lift value observed so far is {best_lift_index:.2f}. Furthermore, this group’s cumulative target percentage is at {cum_target_per:.2f}%, and their cumulative average lift, which quantifies the average ‘boost’ in finding positive outcomes within this group, stands at {cum_avg_lift:.2f}. These findings indicate that concentrating on this group could significantly boost results."
        ]

        # Randomly select one format
        selected_format = random.choice(formats)

        # Assign selected format to context
        context = selected_format.format(
            attr=attr,
            attr_def=attr_def,
            target_def=target_def,
            non_target_def=non_target_def,
            group_range=group_range,
            best_lift_index=best_lift_index,
            cum_target_per=cum_target_per,
            cum_avg_lift=cum_avg_lift
        )

        explanation = context
    
    return explanation.strip()
