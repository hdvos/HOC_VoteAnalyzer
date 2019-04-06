"""A script that downloads voting records from the data portal of the house of commons.

TODO: Read parameters (like location) from command line
TODO: only download new files. Do not download files that are allready downloaded.
"""
from urllib.request import urlretrieve
import os.path
import time
from http.client import HTTPSConnection

#Retrieves the commonvotes frontpage and retrieves the download ID of the last uploaded vote.
def getLastVote():
    conn = HTTPSConnection("commonsvotes.digiminster.com")
    conn.request("GET", "/")
    html = str(conn.getresponse().read())
    html = html.split("a class=\"details-card details-card-division\"\\r\\n",10)[1].split("href=\"/Divisions/Details/")[1].split("\">")[0]
    return int(html)+1

#Returns the header of the website with the response code. If this code is 200 the url is OK, otherwise the url unreachable.
def checkURL(i):
    conn = HTTPSConnection("commonsvotes.digiminster.com")
    conn.request("HEAD", f"/Divisions/DownloadCSV/{i}")
    res = conn.getresponse()
    if res.status == 200: return 1
    else:
        print(str(res.status) + " "+res.reason)
        return 0
     
if __name__ == '__main__':
  #  start = time.time() #used to track the performance of the script
    lastVote = 1000
    lastVote = getLastVote();
    for i in range(0,lastVote):
        location = f'csv_files/{i:04}.csv'      # How the document will be saved
        if os.path.isfile(location)==0: #checks if the file already exists, if it does exist it does not retrieve the file from the url
            url = f"https://commonsvotes.digiminster.com/Divisions/DownloadCSV/{i}" # The url that leads to a document.
            if(checkURL(i)):        #Check if the url is unreachable
                urlretrieve(url, location)
                print(f"File stored as {location}")
  #  print(time.time()-start) #used to track the performance of the script


