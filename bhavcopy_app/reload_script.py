import pymysql
import pandas as pd
import requests
import zipfile
import io
import os
from datetime import datetime
from config import DB_CONFIG
import time
import mysql.connector
import numpy as np

DATA_DIR = "D:/bhavcopy_data/"

def fetch_cookies():
    """Fetch cookies from NSE India to establish a valid session."""
    try:
        session = requests.Session()
        session.get("https://www.nseindia.com", headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.110 Safari/537.36"
        })
        return session.cookies
    except requests.RequestException as e:
        print(f"Failed to fetch cookies: {e}")
        return None

def clean_data(df):
    """Clean and preprocess the DataFrame."""
    try:
        # Replace NaN values with a default value (e.g., None for MySQL compatibility)
        #df = df.fillna(None)
        
        # Ensure numeric columns are properly handled
        numeric_columns = ['TtlTrfVal', 'TtlNbOfTxsExctd']
        for column in numeric_columns:
            if column in df.columns:
                df[column] = df[column].apply(lambda x: float(x) if pd.notna(x) else None)

        return df
    except Exception as e:
        print(f"Error in clean_data: {e}")
        raise


def reload_data_for_date(date_str):
    """Reload data for the specified date with detailed error handling and MySQL insertion."""
    try:
        # Format date for NSE URL
        reload_date = datetime.strptime(date_str, '%Y-%m-%d')
        date_str_formatted = reload_date.strftime("%Y%m%d")
        print(f"Starting reload for date: {date_str} (formatted: {date_str_formatted})")

        # Fetch cookies
        cookies = fetch_cookies()
        if not cookies:
            print("Error: Failed to fetch cookies from NSE.")
            return {"success": False, "error": "Failed to fetch cookies from NSE."}
        print("Cookies fetched successfully.")

        # Define headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.110 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/all-reports",
            "X-Requested-With": "XMLHttpRequest"
        }

        # File download URL
        file_url = f"https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_{date_str_formatted}_F_0000.csv.zip"

        # Attempt to download the file with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"Attempting to download file for {date_str_formatted} (Attempt {attempt + 1})...")
                response = requests.get(file_url, headers=headers, cookies=cookies, timeout=30)
                if response.status_code == 200:
                    print(f"File downloaded successfully for {date_str_formatted}.")
                    break
                elif response.status_code == 404:
                    print(f"File not found on NSE server for {date_str_formatted}.")
                    return {"success": False, "error": f"File for {date_str_formatted} not found on NSE server."}
                else:
                    print(f"Unexpected response for {date_str_formatted}: {response.status_code}")
                    return {"success": False, "error": f"Unexpected response: {response.status_code}"}
            except requests.exceptions.ReadTimeout:
                print(f"Timeout occurred for {date_str_formatted} (Attempt {attempt + 1}).")
                if attempt < max_retries - 1:
                    print(f"Retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"Failed to download file for {date_str_formatted} after multiple retries.")
                    return {"success": False, "error": f"Timeout after multiple retries for {date_str_formatted}."}
            except requests.RequestException as e:
                print(f"RequestException occurred: {e}")
                return {"success": False, "error": str(e)}

        # Extract the file
        output_dir = os.path.join(DATA_DIR, date_str_formatted)
        os.makedirs(output_dir, exist_ok=True)
        try:
            with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                z.extractall(output_dir)
            print(f"File extracted successfully for {date_str_formatted}.")
        except zipfile.BadZipFile:
            print(f"BadZipFile error occurred while extracting {date_str_formatted}.")
            return {"success": False, "error": "Failed to extract ZIP file. File might be corrupted."}

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
            print(f"No CSV file found after extraction for {date_str_formatted}.")
            return {"success": False, "error": f"No CSV file found for {date_str_formatted}."}
        print(f"CSV file located: {csv_file}")

        # Insert data into MySQL database
        df = pd.read_csv(csv_file)
        df = clean_data(df)
        print(f"Data cleaned for {date_str_formatted}. Preparing for database insertion...")
        
        with mysql.connector.connect(**DB_CONFIG) as conn:
            cursor = conn.cursor()
            for _, row in df.iterrows():
                try:
                    # Replace NaN values with None for MySQL compatibility
                    row = row.replace({np.nan: None})
                    cursor.execute("""
                        INSERT INTO BhavCopy (
                            TradDt, BizDt, Sgmt, Src, FinInstrmTp, FinInstrmId, ISIN,
                            TckrSymb, SctySrs, XpryDt, FininstrmActlXpryDt, StrkPric, OptnTp,
                            FinInstrmNm, OpnPric, HghPric, LwPric, ClsPric, LastPric, PrvsClsgPric,
                            UndrlygPric, SttlmPric, OpnIntrst, ChngInOpnIntrst, TtlTradgVol,
                            TtlTrfVal, TtlNbOfTxsExctd, SsnId, NewBrdLotQty, Rmks, Rsvd1, Rsvd2, Rsvd3, Rsvd4
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE 
                            TradDt = VALUES(TradDt),
                            BizDt = VALUES(BizDt),
                            Sgmt = VALUES(Sgmt),
                            Src = VALUES(Src),
                            FinInstrmTp = VALUES(FinInstrmTp),
                            ISIN = VALUES(ISIN),
                            TckrSymb = VALUES(TckrSymb),
                            SctySrs = VALUES(SctySrs),
                            XpryDt = VALUES(XpryDt),
                            FininstrmActlXpryDt = VALUES(FininstrmActlXpryDt),
                            StrkPric = VALUES(StrkPric),
                            OptnTp = VALUES(OptnTp),
                            FinInstrmNm = VALUES(FinInstrmNm),
                            OpnPric = VALUES(OpnPric),
                            HghPric = VALUES(HghPric),
                            LwPric = VALUES(LwPric),
                            ClsPric = VALUES(ClsPric),
                            LastPric = VALUES(LastPric),
                            PrvsClsgPric = VALUES(PrvsClsgPric),
                            UndrlygPric = VALUES(UndrlygPric),
                            SttlmPric = VALUES(SttlmPric),
                            OpnIntrst = VALUES(OpnIntrst),
                            ChngInOpnIntrst = VALUES(ChngInOpnIntrst),
                            TtlTradgVol = VALUES(TtlTradgVol),
                            TtlTrfVal = VALUES(TtlTrfVal),
                            TtlNbOfTxsExctd = VALUES(TtlNbOfTxsExctd),
                            SsnId = VALUES(SsnId),
                            NewBrdLotQty = VALUES(NewBrdLotQty),
                            Rmks = VALUES(Rmks),
                            Rsvd1 = VALUES(Rsvd1),
                            Rsvd2 = VALUES(Rsvd2),
                            Rsvd3 = VALUES(Rsvd3),
                            Rsvd4 = VALUES(Rsvd4)
                    """, tuple(row))
                except mysql.connector.Error as e:
                    print(f"Error inserting/updating row: {row} - {e}")
            conn.commit()


        print(f"Data for {date_str_formatted} successfully inserted into the database.")
        return {"success": True, "message": f"Data for {date_str_formatted} successfully reloaded."}

    except Exception as e:
        print(f"Unexpected error occurred for {date_str}: {e}")
        return {"success": False, "error": str(e)}

# Test the function
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python reload_script.py <YYYY-MM-DD>")
        sys.exit(1)

    date_input = sys.argv[1]
    result = reload_data_for_date(date_input)
    if result["success"]:
        print(result["message"])
    else:
        print(f"Error: {result['error']}")
