import matplotlib.pyplot as plt
import numpy as np

def createBarLinePlot(df):
    # Select the columns to display
    columns = ['order','Attr','groups', 'n', 'Target', 'Target_Per', 'Target_Rate','Non_Target', 'Non_Target_Per', 'lift_Index']
    df_new = df[columns]

    # Create a new DataFrame 'df_new' that excludes the last row of 'df'
    df_new = df_new.iloc[:-1]

    fig = plt.figure(figsize=(6.5,2.8))  # Assign the figure to 'fig'
    
    # Define the width of the bars
    bar_width = 0.4

    # Create an array with the positions of each bar along the x-axis
    r1 = np.arange(len(df_new['order']))
    r2 = [x + bar_width for x in r1]

    # Create bar plot for 'Target_Per' in position r1
    target_bar = plt.bar(r1, df_new['Target_Per'], color ='#EA992C', width = bar_width)

    # Create bar plot for 'Non_Target_Per' in position r2
    non_target_bar = plt.bar(r2, df_new['Non_Target_Per'], color ='#4685B6', width = bar_width)

    plt.xlabel('Order/Ntile')
    plt.ylabel('Percentage')

    # Adding xticks: this will show bar number on x-axis instead of array index.
    plt.xticks([r + bar_width/2 for r in range(len(df_new['order']))], df_new['order'])

    # Create a second y-axis for the 'Lift_Index' line plot
    ax2 = plt.gca().twinx()
    lift_line, = ax2.plot(r1 + bar_width/2, df_new['lift_Index'], color='red')
    ax2.set_ylabel('Lift Index')

    # Manually set the limits of both y-axes
    plt.ylim(0, max(df_new['Target_Per'].max(), df_new['Non_Target_Per'].max())*1.2)
    ax2.set_ylim(0, df_new['lift_Index'].max()*1.2)

    # Add a legend that includes entries from both y-axes and place it outside of the plot on the right-hand side
    plt.legend([target_bar, non_target_bar, lift_line], ['Target Per', 'Non-Targets Per', 'Lift_Index'], bbox_to_anchor=(1.15, 1), loc='upper left', prop={'size': 8}, frameon=False)
    
    #plt.show()
    
    return fig  # Return the figure object
