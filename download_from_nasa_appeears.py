# Import packages 
import requests as r
import getpass, pprint, time, os, cgi, json, sys
import geopandas as gpd
import pandas as pd

AOIFILE=sys.argv[1]

# Set input directory, change working directory
inDir = os.getcwd()                                    # IMPORTANT: Update to reflect directory on your OS
os.chdir(inDir)                                        # Change to working directory

# Read the Area of Interest (AOI) -- geojson or shapefile
aoi = gpd.read_file(AOIFILE) # Read in GeoJSON or Shapefile as dataframe using geopandas
aoi = aoi.drop(columns=['loaddate']).explode(index_parts=True)
aoi = json.loads(aoi.to_json())
# Parsethe AOIFILE to create task_name, add today's date
task_name=AOIFILE.split('/')[-1].split('.')[0]+"_"+pd.to_datetime("today").strftime("%Y%m%d")

# Set up Auth for NASA APPEEARS
api = 'https://appeears.earthdatacloud.nasa.gov/api/'
# Promopt for NASA Earth Data Username and Password
# Login with NASA Earthdata Account
user = getpass.getpass(prompt = 'Enter NASA Earthdata Login Username: ')      # Input NASA Earthdata Login Username
password = getpass.getpass(prompt = 'Enter NASA Earthdata Login Password: ')  # Input NASA Earthdata Login Password

token_response = r.post('{}login'.format(api), auth=(user, password)).json()  # Insert API URL, call login service, provide credentials & return json
token = token_response['token']                                               # Save login token to a variable
head = {'Authorization': 'Bearer {}'.format(token)}                           # Create a header to store token information, needed to submit a request
del user, password                                                            # Remove user and password information

# Create list of products of interest
# MYD16A2.061  ET -- MODIS Aqua
# MOD16A2.061  ET -- MODIS Terra
# MCD15A2H.061 LAI -- combined MODIS
# MYD15A2H.061 LAI -- MODIS Aqua
# MOD15A2H.061 LAI -- MODIS Terra
# MYD17A2.061  GPP -- MODIS Aqua
# MOD17A2.061  GPP -- MODIS Terra
prod_list_all = ['MYD16A2.061', 'MOD16A2.061', 'MCD15A2H.061', 'MYD15A2H.061', 'MOD15A2H.061', 'MYD17A2H.061', 'MOD17A2H.061']
prod_list = ['MYD16A2.061', 'MCD15A2H.061', 'MYD17A2H.061']


# Get list of layers for this product
# ET - MODIS Aqua
layers = [(prod_list[0],'ET_500m')]  

## Add LAI vars to the list of layers we want to request
# LAI - MODIS Combined
layers.append((prod_list[1],'Lai_500m'))

## Add GPP vars to the list of layers we want to request
# GPP - MODIS Aqua
layers.append((prod_list[2],'Gpp_500m'))

# Create a list of dictionaries
prodLayer = []
for l in layers:
    prodLayer.append({
            "layer": l[1],
            "product": l[0]
          })

# Submit an Area Request

# Compile a JSON
task_type = ['area']        # Type of task, area or point
#proj = projs['geographic']['Name']  # Set output projection
#outFormat = ['netcdf4']  # Set output file format type
startDate = '01-01-2000'            # Start of the date range for which to extract data: MM-DD-YYYY
endDate = '12-31-2022'              # End of the date range for which to extract data: MM-DD-YYYY
recurring = False                   # Specify True for a recurring date range
#yearRange = [2000,2016]            # if recurring = True, set yearRange, change start/end date to MM-DD

# create JSON
task = {
    'task_type': task_type[0],
    'task_name': task_name,
    'params': {
         'dates': [
         {
             'startDate': startDate,
             'endDate': endDate,
             'recurring': False,
             'yearRange': [1950, 2050],
         }],
         'layers': prodLayer,
         'output': {
                 'format': {
                         'type': 'netcdf4'},
                         'projection': 'geographic'},
         'geo': aoi,
    }
}

# Submit a Task Request
task_response = r.post('{}task'.format(api), json=task, headers=head).json()  # Post json to the API task service, return response as json

# take the task id returned from the task_response that was generated when submitting your request, and use the AρρEEARS API status service to check the status of your request.
task_id = task_response['task_id']                                               # Set task id from request submission

# call the task service for your request every 60 seconds to check the status of your request.
# Ping API until request is complete, then continue to download 
starttime = time.time()
while r.get('{}task/{}'.format(api, task_id), headers=head).json()['status'] != 'done':
    print(r.get('{}task/{}'.format(api, task_id), headers=head).json()['status'])
    time.sleep(60.0 - ((time.time() - starttime) % 60.0))

# Download a Request
destDir = os.path.join(inDir, task_name)                # Set up output directory using input directory and task name
if not os.path.exists(destDir):os.makedirs(destDir)     # Create the output directory

# Get list of files in Request Output 
bundle = r.get('{}bundle/{}'.format(api,task_id), headers=head).json()  # Call API and return bundle contents for the task_id as json

# Download Files in the Request
# use the contents of the bundle to select the file name and id and store as a dictionary.
files = {}                                                       # Create empty dictionary
for f in bundle['files']: files[f['file_id']] = f['file_name']   # Fill dictionary with file_id as keys and file_name as values

# Use the files dictionary and a for loop to automate downloading all of the output files into the output directory.
for f in files:
    dl = r.get('{}bundle/{}/{}'.format(api, task_id, f), headers=head, stream=True, allow_redirects = 'True')                                # Get a stream to the bundle file
    if files[f].endswith('.tif'):
        filename = files[f].split('/')[1]
    else:
        filename = files[f] 
    filepath = os.path.join(destDir, filename)                                                       # Create output file path
    with open(filepath, 'wb') as f:                                                                  # Write file to dest dir
        for data in dl.iter_content(chunk_size=8192): f.write(data) 
print('Downloaded files can be found at: {}'.format(destDir))


