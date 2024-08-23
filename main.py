import pandas
from zipfile import ZipFile
from urllib.request import urlopen, urlretrieve
import requests
import datetime
from dateutil.parser import parse as parsedate
from os.path import exists, getmtime
import pytz
from unidecode import unidecode
from time import time

def missing_lifters():
    """
    Tell users to create the file with the lifters info
    Including the name of the file and its format
    """
    print("Please create a lifters file in the same path")
    print("File name: 'lifters.py'")
    print("Format of file:")
    print("")
    print("lifters = [")
    print('"Lifter1_name Lifter1_surname(s)",')
    print('"Lifter2_name Lifter2_surname(s)",')
    print('"Lifter3_name Lifter3_surname(s)",')
    print("]")
    #Exit without running the actual program
    exit(1)

try:
    from lifters import lifters
except ModuleNotFoundError:
    missing_lifters()

def get_file_remote_date(url):
    """Return date of the latest uploaded copy"""
    r = requests.head(url)
    url_time = r.headers['last-modified']
    return parsedate(url_time)

def get_data_df_from_zip(file):
    """Return a pandas df from the csv in the downloaded zip file"""
    with ZipFile(file) as zipfile:
        #Get a list with all csv files in that zip
        extensions = (".csv")
        csv_files = [file for file in zipfile.namelist() if file.endswith(extensions)]
        #We just keep the first one, there should be only one csv
        csv_file = csv_files[0]
        #Get the date, it's a tuple
        date = zipfile.getinfo(csv_file).date_time
        #Time is not needed, just the date. Make it human readable
        human_date = str(date[2]) + "/" + str(date[1]) + "/" + str(date[0])
        #Some formatting, print the date of the list for users to see it
        print(f"Data from openpowerlifting.org dated on {human_date}:")
        #Read the whole csv into a pandas dataframe
        return pandas.read_csv(zipfile.open(csv_file), low_memory=False)

def get_lifters_data(data_df, lifters):
    """Look up the lifters in 'lifters' list into all the results from data_df """
    return [data_df[data_df.Name.str.contains(lifter)]
            if not data_df[data_df.Name.str.contains(lifter)].empty
            else data_df[data_df.Name.str.contains(unidecode(lifter))]
            for lifter in lifters]

def print_lifters_results(lifters_results, columns):
    """Print all results for the search omitting empty values"""
    for lifter in lifters_results:
        if not lifter.empty:
            print(lifter[columns].sort_values(["Name", "Date"]).to_string(index=False))

#Some needed values, url with the zip and localfile name
url_list_latest = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
file = "./openpowerlifting-latest.zip"

#Check if file already exists on disk
if exists(file):
    print("File was already downloaded into disk")

    #Get date of the local copy
    file_time = datetime.datetime.fromtimestamp(getmtime(file))

    #Get date of the remote copy
    url_date = get_file_remote_date(url_list_latest)

    #Compare dates, if online is newer, download it
    #Local file time needs to be localized for comparison, pytz.UTC is needed
    if url_date > pytz.UTC.localize(file_time):
        print("File date online was newer than the copy on disk, downloading again")
        urlretrieve(url_list_latest, file)
    #Otherwise, no need to redownload
    else:
        print("File on disk was already the latest, no need to redownload")
#If file not in disk, download it
else:
    print("File not downloaded, downloading it")
    urlretrieve(url_list_latest, file)

#Get a pandas DF from the zipfile
time_before_loading_df = time()
data_df = get_data_df_from_zip(file)
time_load_df = float('{:.2f}'.format(time() - time_before_loading_df))
print(f"All results from database loaded into memory in {time_load_df} second(s)")

#Uncomment next block to skip international results
#Remember to use lifters_spain variable instead
#Country is not really used, rather the federation
#country = ["Spain"]
#federation = ["AEP", "WRPF-Spain"]
#lifters_spain = data_df[data_df.Federation.isin(federation)]
#print(lifters_spain)

time_before_search = time()
lifters_results = get_lifters_data(data_df, lifters)
time_search = float('{:.2f}'.format(time() - time_before_search))

columns_to_print = ["Name", "Age", "Division", "BodyweightKg",
                    "Best3SquatKg", "Best3BenchKg", "Best3DeadliftKg",
                    "TotalKg", "Place", "Dots", "Wilks", "Federation",
                    #Other possibly interesting data, omitted now:
                    #"Squat1Kg", "Squat2Kg", "Squat3Kg",
                    #"Bench1Kg",  "Bench2Kg", "Bench3Kg",
                    #"Deadlift1Kg", "Deadlift2Kg", "Deadlift3Kg",
                    "Date", "MeetCountry", "MeetTown", "MeetName"]
print_lifters_results(lifters_results, columns_to_print)
print(f"All lifters requested searched in database in {time_search} (additional) second(s)")
