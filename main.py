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
import csv


class LiftersQuery():

    def __init__(self, csv_lifters_file="lifters.csv",
                 columnsToPrint=[]):
        """
        Class constructor
        First parameter: CSV file name (with a default)
        Second parameter: Which columns to print (empty default will print
        everything)
        """
        self.csv_lifters_file = csv_lifters_file
        self.columnsToPrint=columnsToPrint
        self.liftersQuery = self.getLifters()
        self.db_file = self.getOrRefreshFile()
        #Get a pandas DF from the zipfile
        time_before_loading_df = time()
        self.data_df = self.getDataDfFromZip(self.db_file)
        self.timeLoadDf = float('{:.2f}'.format(time() - time_before_loading_df))
        print(f"All results from database loaded into memory in {self.timeLoadDf} second(s)")

        time_before_search = time()
        self.liftersResults = self.getLiftersData(self.data_df, self.liftersQuery)
        self.timeSearch = float('{:.2f}'.format(time() - time_before_search))

        print(f"All lifters requested searched in database in {self.timeSearch} (additional) second(s)")

    def getLifters(self):
        """
        Returns a list of lifters, either from the csv file, or from the
        lifters.py file. Returns an error and exists if it can't find either
        """
        if exists(self.csv_lifters_file):
            with open(self.csv_lifters_file, newline="") as csvfile:
                reader = csv.reader(csvfile, delimiter=",", quotechar='"')
                lifters = [" ".join(row).strip() for row in reader]
        else:
            try:
                from lifters import lifters
            except ModuleNotFoundError:
                self.missing_lifters()

        return lifters

    def getOrRefreshFile(self):
        """
        Check whether the file exists locally.
        If it does, check the date in the online file.
        Only download if it did not exist or if it was newer online
        Returns the filename, which is actually hardcoded
        """
        #Some needed values, url with the zip and localfile name
        #url_list_latest = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
        url_list_latest = "https://openpowerlifting.gitlab.io/opl-csv/files/openipf-latest.zip"
        #file = "./openpowerlifting-latest.zip"
        file = "./openipf-latest.zip"
        #Check if file already exists on disk
        if exists(file):
            print("File was already downloaded into disk")
            #Get date of the local copy
            file_time = datetime.datetime.fromtimestamp(getmtime(file))
            #Get date of the remote copy
            url_date = self.getFileRemoteDate(url_list_latest)
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
        return file

    def missingLifters(self):
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
        #Tell users that the can also use a csv file
        print("")
        print("A CSV file can also be provided:")
        print("It needs to be saved as 'lifters.csv'")
        print("Each lifter to be listed in a row of the CSV")
        print("Name before surname(s) for each lifter")
        print("The full name may be contained in a single cell (single-column CSV)")
        print("Or names and surnames separated in columns. Use comma as separator")
        print("If the CSV file exists, the lifters.py file is ignored")
        #Exit without running the actual program
        exit(1)

    def getFileRemoteDate(self, url):
        """Return date of the latest uploaded copy"""
        r = requests.head(url)
        url_time = r.headers['last-modified']
        return parsedate(url_time)

    def getDataDfFromZip(self, file):
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

    def getLiftersData(self, data_df, lifters):
        """Look up the lifters in 'lifters' list into all the results from data_df """
        return [data_df[data_df.Name.str.contains(lifter)]
                if not data_df[data_df.Name.str.contains(lifter)].empty
                else data_df[data_df.Name.str.contains(unidecode(lifter))]
                for lifter in lifters]

    def printLiftersResults(self):
        """Print all results for the search omitting empty values"""
        if not self.columnsToPrint:
            self.columnsToPrint = list(self.liftersResults[0].columns.values)
        for lifter in self.liftersResults:
            if not lifter.empty:
                print(lifter[self.columnsToPrint].sort_values(["Name",
                                                               "Date"]).to_string(index=False))

    def exportLiftersData(self, filename="query.csv", columns=[]):
        """
        Exports info as a CSV file. Will ignore the columns settings and export
        everything nevertheless, unless the specific columns are passed as a
        list
        """
        with open(filename, "w") as file:
            if not columns:
                columns = list(self.liftersResults[0].columns.values)
            #Write headers first:
            write = csv.writer(file)
            write.writerow(columns)
        #Write actual results
        for lifter in self.liftersResults:
            if not lifter.empty:
                lifter[columns].sort_values(["Name","Date"]).to_csv(filename,
                                                                    mode="a",
                                                                    encoding="utf-8",
                                                                    index=False,
                                                                    header=False)
        print(f"Lifters data exported into '{filename}' file")

columns_to_print = ["Name", "Age", "Division", "BodyweightKg",
                    "Best3SquatKg", "Best3BenchKg", "Best3DeadliftKg",
                    "TotalKg", "Place", "Goodlift", "Federation",
                    #Other possibly interesting data, omitted now:
                    #"Squat1Kg", "Squat2Kg", "Squat3Kg",
                    #"Bench1Kg",  "Bench2Kg", "Bench3Kg",
                    #"Deadlift1Kg", "Deadlift2Kg", "Deadlift3Kg",
                    "Date", "MeetCountry", "MeetTown", "MeetName"]

lifters_query = LiftersQuery(columnsToPrint=columns_to_print)

lifters_query.printLiftersResults()
lifters_query.exportLiftersData()
