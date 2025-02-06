# DB_CONFIG = {
#     'host': '216.48.185.197',
#     'user': 'darsan',
#     'password': 'Aloh@1234',
#     'database': 'bhavcopynew',
#     'port': 3306
# }


DB_CONFIG = {
    'host': '127.0.0.1',  # or 'localhost'
    'user': 'root',  # Replace with your local database username (e.g., 'root')
    'password': 'Newday@123',  # Replace with your local database password
    'database': 'bhavcopynew',  # Replace with the name of the database you want to connect to
    'port': 3306  # Default MySQL port (if you're using a non-standard port, update accordingly)
}

# Base URLs for different segments
BASE_URLS = {
    "CM_NSE": "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date}_F_0000.csv.zip",
    "FO_NSE": "https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_{date}_F_0000.csv.zip",
    "CD_NSE": "https://nsearchives.nseindia.com/archives/cd/bhav/BhavCopy_NSE_CD_0_0_0_{date}_F_0000.csv.zip",

    "CM_BSE":"https://www.bseindia.com/download/BhavCopy/Equity/BhavCopy_BSE_CM_0_0_0_{date}_F_0000.CSV",
    "FO_BSE":"https://www.bseindia.com/download/Bhavcopy/Derivative/BhavCopy_BSE_FO_0_0_0_{date}_F_0000.CSV",
    "CD_BSE":"https://www.bseindia.com/bsedata/CIML_bhavcopy/BhavCopy_BSE_CD_0_0_0_{date}_F_0000.CSV"
}

