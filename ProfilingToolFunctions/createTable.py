import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
import textwrap

def createTable(x):
    # Define a custom function to add commas to numeric values and percentage signs
    def format_values(x, is_percent=False):
        if is_percent:
            return str(x) + '%'
        else:
            return format(x, ',')

    # Select the columns to display and apply the function to the columns
    df = x[['Attr','order','groups', 'n', 'Target', 'Target_Per','Cum_Target_Per', 'Target_Rate','Non_Target', 'Non_Target_Per', 'lift_Index']].copy()
    df.loc[df.index[-1], ['order','Attr', 'groups']] = ['','Overall', '']
    df[['n', 'Target', 'Non_Target']] = df[['n', 'Target', 'Non_Target']].applymap(format_values)
    
    df[['Target_Per','Cum_Target_Per','Target_Rate', 'Non_Target_Per']] = df[['Target_Per','Cum_Target_Per','Target_Rate', 'Non_Target_Per']].applymap(lambda x: format_values(x, True))
    
    # Create a figure and an axes object
    fig, ax = plt.subplots(figsize=(8,9))
    plt.subplots_adjust(left=0.1, right=.9, bottom=0.5, top=0.8)  # Increase bottom

    # Hide the axes and the frame
    ax.axis('off')
    ax.set_frame_on(False)

    # Create the table and adjust the font size
    table = ax.table(cellText=df.values, colLabels=df.columns, loc='center')

    # Adjust the column widths
    table.auto_set_column_width(col=list(range(len(df.columns))))

    # Make the first and last row of the table bold
    for (row,col), cell in table.get_celld().items():
        if row == len(df):
            cell.set_fontsize(14)
            cell.set_text_props(weight='bold')

        cell.set_facecolor('#f5f5f5')

        # Set the edgecolor to a lighter shade
        cell.set_edgecolor('#d9d9d9')

        # Apply color shading to lift_Index column based on its value
        if col == df.columns.get_loc('lift_Index') and row != 0 and row != len(df):
            lift_index_value = float(cell.get_text().get_text())
            if lift_index_value > 1:
                colors = plt.cm.BuPu(np.linspace(0, 0.5, len(df['lift_Index'])))
                cell.set_facecolor(colors[np.digitize(lift_index_value, np.linspace(df['lift_Index'].min(), df['lift_Index'].max(), len(colors))) - 1])

    
    summary_text = x['Summary_text'].iloc[0]
    
    # Wrap the text
    wrapper = textwrap.TextWrapper(width=100)  # Adjust width as needed
    wrapped_text = wrapper.fill(text=summary_text)

    
    plt.annotate(wrapped_text, (0,0), xycoords='axes fraction', textcoords='offset points', va='top', ha='left',fontsize=8, fontweight=50,color='#696969')


    
    return fig

