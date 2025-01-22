import sqlite3
import pandas as pd
import requests
import zipfile
import io
import os
import sys
from datetime import datetime

DATA_DIR = "D:/bhavcopy_data/"
DB_PATH = "C:\\Users\\Darshan\\Downloads\\sqlite-tools-win-x64-3480000\\bhavcopy_data.db"

def reload_data_for_date(date_str):
    """Reload data for the specified date."""
    try:
        # Convert date string to datetime
        reload_date = datetime.strptime(date_str, '%Y-%m-%d')
        date_str = reload_date.strftime("%Y%m%d")

        # Step 1: Download the file
        file_url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_str}_F_0000.csv.zip"
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(file_url, headers=headers, timeout=30)

        if response.status_code != 200:
            print(f"Failed to download file for {date_str}. Status Code: {response.status_code}")
            return False

        # Step 2: Extract the file
        output_dir = os.path.join(DATA_DIR, date_str)
        os.makedirs(output_dir, exist_ok=True)

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            z.extractall(output_dir)

        # Locate the CSV file
        csv_file = None
        for root, _, files in os.walk(output_dir):
            for file in files:
                if file.endswith(".csv"):
                    csv_file = os.path.join(root, file)
                    break
            if csv_file:
                break

        if not csv_file:
            print(f"No CSV file found for {date_str}.")
            return False

        # Step 3: Insert data into SQLite database
        df = pd.read_csv(csv_file)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            for _, row in df.iterrows():
                cursor.execute("""
                    INSERT INTO BhavCopy (
                        TradDt, BizDt, Sgmt, Src, FinInstrmTp, FinInstrmId, ISIN,
                        TckrSymb, SctySrs, XpryDt, TtlTradgVol, TtlTrfVal, TtlNbOfTxsExctd,
                        SsnId, NewBrdLotQty, Rmks, Rsvd1, Rsvd2, Rsvd3, Rsvd4
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row['TradDt'], row['BizDt'], row['Sgmt'], row['Src'], row['FinInstrmTp'], row['FinInstrmId'], row['ISIN'],
                    row['TckrSymb'], row.get('SctySrs', None), row.get('XpryDt', None), row['TtlTradgVol'], row['TtlTrfVal'],
                    row['TtlNbOfTxsExctd'], row['SsnId'], row['NewBrdLotQty'], row.get('Rmks', None),
                    row.get('Rsvd1', None), row.get('Rsvd2', None), row.get('Rsvd3', None), row.get('Rsvd4', None)
                ))
            conn.commit()

        print(f"Data for {date_str} successfully inserted into the database.")
        return True

    except Exception as e:
        print(f"Error reloading data for {date_str}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reload_script.py <YYYY-MM-DD>")
        sys.exit(1)

    date_input = sys.argv[1]
    reload_data_for_date(date_input)
