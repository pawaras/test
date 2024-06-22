import matplotlib.pyplot as plt
import boto3
import tempfile
import os

def create_and_upload_plots(sDict, DLXProfilingDT, createTable, createBarLinePlot):
    s3 = boto3.client('s3')

    # Extract the last subdirectory from the S3 location
    s3_location = sDict['s3_location']
    bucket_name = s3_location.split('/')[2]  # Extract the bucket name from the S3 location

    # Get unique values of 'Attr'
    unique_attrs = DLXProfilingDT['Attr'].unique()

    # Get a list of all objects in the 'plots' directory
    objects = s3.list_objects(Bucket=bucket_name, Prefix=os.path.join(*s3_location.split('/')[3:-1], 'plots'))

    # Delete all objects in the 'plots' directory
    if 'Contents' in objects:
        s3.delete_objects(
            Bucket=bucket_name,
            Delete={
                'Objects': [{'Key': obj['Key']} for obj in objects['Contents']]
            }
        )
    # Loop through each unique 'Attr'
    for attr in unique_attrs:
        # Subset DLXProfilingDT for the current 'Attr'
        DLXProfilingDT_temp = DLXProfilingDT[DLXProfilingDT['Attr'] == attr]

        # Create a temporary directory
        with tempfile.TemporaryDirectory() as tempdir:
            # The temporary directory path is stored in the 'tempdir' variable

            # Get unique value of 'Rank'
            rank = str(DLXProfilingDT_temp['Rank'].unique()[0])

            # Create the table plot and save it as a PNG file
            fig1 = createTable(DLXProfilingDT_temp)
            table_png_path = os.path.join(tempdir, f'table_plot_{rank}__{attr}.png')
            fig1.savefig(table_png_path, bbox_inches='tight',dpi=150)

            # Create the bar line plot and save it as a PNG file
            fig2 = createBarLinePlot(DLXProfilingDT_temp)
            bar_line_png_path = os.path.join(tempdir, f'bar_line_plot_{rank}__{attr}.png')
            fig2.savefig(bar_line_png_path, bbox_inches='tight',dpi=150)

            #print(f'Saved plots to {table_png_path} and {bar_line_png_path}')

            # Upload the PNG files to S3
            s3 = boto3.client('s3')
            with open(table_png_path, 'rb') as data:
                s3.upload_fileobj(data, bucket_name, os.path.join(*s3_location.split('/')[3:-1], 'plots', f'{rank}__{attr}__table_plot.png'))
            with open(bar_line_png_path, 'rb') as data:
                s3.upload_fileobj(data, bucket_name, os.path.join(*s3_location.split('/')[3:-1], 'plots', f'{rank}__{attr}__bar_line_plot.png'))
             
    print(f'Uploaded plots to {os.path.join("s3:/", bucket_name, *s3_location.split("/")[3:-1], "plots")}')
