"""A script that downloads voting records from the data portal of the house of commons.

TODO: Read parameters (like location) from command line
TODO: only download new files. Do not download files that are allready downloaded.
"""
from urllib.request import urlretrieve

if __name__ == '__main__':
    for i in range(1000):
        url = f"https://commonsvotes.digiminster.com/Divisions/DownloadCSV/{i}" # The url that leads to a document.

        location = f'csv_files/{i:04}.csv'      # How the document will be saved

        try:    
            urlretrieve(url, location)
            print(f"File stored as {location}")
        except Exception as e:                  # An exception will be raised if the url does not exist.
            print(e)