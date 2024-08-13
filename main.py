import pandas
from zipfile import ZipFile
from urllib.request import urlopen, urlretrieve
import requests
import datetime
from dateutil.parser import parse as parsedate
from os.path import exists, getmtime
import pytz
try:
    from lifters import lifters
except ModuleNotFoundError:
    #Tell users to create the file with the playersinfo
    #Including the name of the file and its format
    print("Please create a lifters file")
    print("File name: 'lifters.py'")
    print("Format of file:")
    print("")
    print("players = [")
    print('"Lifter1_name Lifter1_surname(s)",')
    print('"Lifter2_name Lifter2_surname(s)",')
    print('"Lifter3_name Lifter3_surname(s)",')
    print("]")
    #Exit without running the actual program
    exit(1)

url_list_latest = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
file = "./openpowerlifting-latest.zip"

#Check if file already exists on disk
if exists(file):
    print("File was already downloaded into disk")

    #Get date of the latests uploaded copy
    r = requests.head(url_list_latest)
    url_time = r.headers['last-modified']
    url_date = parsedate(url_time)
    #Get date of the local copy
    file_time = datetime.datetime.fromtimestamp(getmtime(file))
    utc=pytz.UTC

    #Compare dates, if online is newer, download it
    #Local file time needs to be localized for comparison
    #print(f"URL date: {url_date} File date: {file_time}")
    if url_date > utc.localize(file_time):
        print("File date online was newer than the copy on disk, downloading again")
        urlretrieve(url_list_latest, file)
    #Otherwise, no need to redownload
    else:
        print("File on disk was already the latest, no need to redownload")
#If file not in disk, download it
else:
    print("File not downloaded, downloading it")
    urlretrieve(url_list_latest, file)

#Open zipfile
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
    data_df = pandas.read_csv(zipfile.open(csv_file), low_memory=False)
    #print(data_df)

    #Uncomment next block to skip international results
    #Remember to use lifters_spain variable instead
    #Country is not really used, rather the federation
    #country = ["Spain"]
    #federation = ["AEP", "WRPF-Spain"]
    #lifters_spain = data_df[data_df.Federation.isin(federation)]
    #print(lifters_spain)

    columns_to_print = ["Name", "Age", "Division", "BodyweightKg",
                        "Best3SquatKg", "Best3BenchKg", "Best3DeadliftKg",
                        "TotalKg", "Place", "Dots", "Wilks", "Federation",
                        #Other possibly interesting data, omitted now:
                        #"Squat1Kg", "Squat2Kg", "Squat3Kg",
                        #"Bench1Kg",  "Bench2Kg", "Bench3Kg",
                        #"Deadlift1Kg", "Deadlift2Kg", "Deadlift3Kg",
                        "Date", "MeetCountry", "MeetTown", "MeetName"]
    lifters_ids = [data_df[data_df.Name.str.contains(lifter)]
                   for lifter in lifters]
    for lifter in lifters_ids:
        if not lifter.empty:
            print(lifter[columns_to_print].sort_values(["Name", "Date"]).to_string(index=False))
