import boto3
import os
import base64
import re
s3 = boto3.client('s3')

def get_png_files(s3_location):
    # Extract the last subdirectory from the S3 location
    bucket_name = s3_location.split('/')[2] 

    # Specify your S3 location
    s3_location_plots = os.path.join("s3:/", bucket_name, *s3_location.split("/")[3:-1], "plots")

    prefix = '/'.join(s3_location_plots.split('/')[2:])

    
    # Get the list of files in the bucket with the specified prefix
    files = s3.list_objects(Bucket=bucket_name, Prefix=prefix)['Contents']

    # Filter out the PNG files and sort them by rank
    png_files = sorted([file['Key'] for file in files if file['Key'].endswith('.png')]) 
    png_files = sorted(png_files, key=lambda x: int(re.findall(r'\d+', x)[0]))

    return png_files

def get_logo_base64(bucket_name):
    # Download the logo image from S3
    s3.download_file(bucket_name, 'profilingtool/deluxe_logo_tagline2020_4c.jpg', 'logo.jpg')

    # Open the logo image file in binary mode
    with open('logo.jpg', 'rb') as f:
        # Read the file and encode it into base64 format
        logo_base64 = base64.b64encode(f.read()).decode('utf-8')

    return logo_base64


def generate_html(png_files, logo_base64,bucket_name):
    # Start the HTML document with a dropdown menu and CSS to scale down the webpage
    html_str = f"""
    <div style="text-align:center">
        <img src="data:image/jpg;base64,{logo_base64}" alt="Logo" style="width:20%">
    </div>
    <!DOCTYPE html>
    <html>
    <head>
    <style>
    body {{
      transform: scale(0.90);  /* Scale down the webpage by 5% */
      transform-origin: 0 0;  /* Set the origin point for the scaling to the top left corner of the webpage */
    }}
    .center-div {{
      display: flex;
      justify-content: center;
    }}
    </style>
    </head>
    <body>

    <div class="center-div">
    <h2>Ranked Attribute</h2>

    <select id="mySelect" onchange="myFunction()">
    """

    # Add an option to the dropdown menu for each header
    for i in range(0, len(png_files), 2):
        # Extract header from the PNG file name
        header = png_files[i].split('__')[1]
        html_str += f'<option value="{header}">{header}</option>'

    html_str += """
    </select>
    </div>
    """

    # Add a div for each image pair and hide them by default
    for i in range(0, len(png_files), 2):
        # Download the bar plot and table plot for each rank
        s3.download_file(bucket_name, png_files[i], 'bar_plot.png')
        s3.download_file(bucket_name, png_files[i+1], 'table_plot.png')

        # Open the images with PIL and convert them into base64
        with open('bar_plot.png', 'rb') as f:
            bar_plot_base64 = base64.b64encode(f.read()).decode('utf-8')
        with open('table_plot.png', 'rb') as f:
            table_plot_base64 = base64.b64encode(f.read()).decode('utf-8')

        # Extract header from the PNG file name
        header = png_files[i].split('__')[1]

        # Add a div for each image pair and hide it by default
        html_str += f'<div id="{header}" style="display:none">'
        html_str += f'<center><h2 style="color:#008080;">{header}</h2>'
        html_str += f'<img src="data:image/png;base64,{bar_plot_base64}"><br>'
        html_str += f'<img src="data:image/png;base64,{table_plot_base64}"><br><br><br></center>'
        html_str += '</div>'

    # Add JavaScript code to show and hide divs based on the selected option
    html_str += """
<script>
function myFunction() {
  var x = document.getElementById("mySelect").value;
  
  // Hide all divs
"""
    
    for i in range(0, len(png_files), 2):
        # Extract header from the PNG file name
        header = png_files[i].split('__')[1]
        html_str += f'document.getElementById("{header}").style.display = "none";\n'

    html_str += """
      // Show the selected div
      document.getElementById(x).style.display = "block";
    }
    </script>

    </body>
    </html>
    """

    return html_str

def upload_to_aws(local_file, bucket, s3_file):
        s3 = boto3.client('s3')

        try:
            s3.upload_file(local_file, bucket, s3_file)
            print("Upload Successful")
            return True
        except FileNotFoundError:
            print("The file was not found")
            return False
        except NoCredentialsError:
            print("Credentials not available")
            return False

def generate_interactive_report():
    s3_location = sDict['s3_location']
    
    png_files = get_png_files(s3_location)
    
    bucket_name = s3_location.split('/')[2]
    
    logo_base64 = get_logo_base64(bucket_name)
    
    html_str = generate_html(png_files, logo_base64,bucket_name)

    with open('Interactive_report.html', 'w') as f:
        f.write(html_str)

    # Get the bucket and path from sDict['s3_location']
    bucket, path = sDict['s3_location'].split('/')[2], '/'.join(sDict['s3_location'].split('/')[3:])

    # Remove the old filename from the path and add the new folder and filename
    new_path = '/'.join(path.split('/')[:-1]) + '/Final_report/Interactive_report.html'

    uploaded = upload_to_aws('Interactive_report.html', bucket, new_path)
    
    if uploaded:
        print("HTML Doc Generated")


