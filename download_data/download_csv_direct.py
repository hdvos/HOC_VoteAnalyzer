from urllib.request import urlretrieve


for i in range(1000):
    url = f"https://commonsvotes.digiminster.com/Divisions/DownloadCSV/{i}"

    location = f'download_data/csv_files/{i:04}.csv'

    try:
        urlretrieve(url, location)
    except Exception as e:
        print(e)