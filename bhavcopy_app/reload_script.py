import pandas as pd
import zipfile
import io
import os
from datetime import datetime
from bhavcopy_app.mcxdownloader import get_bhavcopy_data
from config import DB_CONFIG, BASE_URLS
import time
import mysql.connector
import numpy as np
import requests

DATA_DIR = "D:/bhavcopy_data/"

def fetch_cookies(src):
    """Fetch cookies from NSE or BSE to establish a valid session."""
    try:
        session = requests.Session()

        if src == "NSE":
            session.get("https://www.nseindia.com", headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.110 Safari/537.36"
            })

        elif src == "BSE":
            headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.110 Safari/537.36",
            "Referer": "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "X-Requested-With": "XMLHttpRequest"
        }

            # Step 1: Visit the BSE homepage
            session.get("https://www.bseindia.com", headers=headers)

            # Step 2: Visit Market Info to establish session
            response = session.get("https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx", headers=headers)

            if response.status_code == 200:
                print("✅ BSE Cookies Fetched Successfully!")
                return session  # Return full session instead of just cookies
            else:
                print(f"⚠️ Warning: Unexpected response from BSE ({response.status_code}).")
                return None

        return session
    except requests.RequestException as e:
        print(f"❌ Failed to fetch cookies for {src}: {e}")
        return None


def get_headers(src):
    """Return the appropriate headers for the given source."""
    if src == "NSE":
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.110 Safari/537.36",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.nseindia.com/all-reports",
            "X-Requested-With": "XMLHttpRequest"
        }
    elif src == "BSE":
        return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.6834.110 Safari/537.36",
        "Referer": "https://www.bseindia.com/markets/MarketInfo/BhavCopy.aspx",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "upgrade-insecure-requests": "1",
        "Referrer-Policy": "strict-origin-when-cross-origin"
    }

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


def reload_data_for_date(date_str, sgmt="CM", src="NSE"):
    """Reload data for the specified date with detailed error handling and MySQL insertion."""
    try:
        # Format date for NSE URL
        reload_date = datetime.strptime(date_str, '%Y-%m-%d')
        date_str_formatted = reload_date.strftime("%Y%m%d")
        print(f"Starting reload for date: {date_str} (formatted: {date_str_formatted})")

        # Fetch cookies
        session = fetch_cookies(src)
        if not session:
            return {"success": False, "error": f"Failed to fetch cookies from {src}."}

        # Define headers
        headers = get_headers(src)

        # Determine the correct file URL
        url_key = f"{sgmt}_{src}"  # Example: CM_NSE, FO_NSE, CD_NSE
        if url_key not in BASE_URLS:
            print(f"Error: No matching URL for segment {sgmt} and source {src}")
            return {"success": False, "error": f"No URL defined for Sgmt={sgmt}, Src={src}"}
        
        # File download URL
        file_url = BASE_URLS[url_key].format(date=date_str_formatted)

        print(f"Selected URL: {file_url}")

        # Attempt to download the file with retry logic
        # Attempt to download the file with retry logic
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use the same session and headers from fetching cookies
                response = session.get(file_url, headers=headers, cookies=session.cookies, timeout=30)

                if response.status_code == 200:
                    print(f"✅ File downloaded successfully for {date_str_formatted}.")
                    break
                elif response.status_code == 403:
                    print(f"🚫 Forbidden (403) error for {date_str_formatted}. Retrying with updated session...")
                    cookies = fetch_cookies(src)  # Re-fetch cookies and try again
                elif response.status_code == 404:
                    return {"success": False, "error": f"❌ File for {date_str_formatted} not found on {src} server."}

            except requests.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return {"success": False, "error": f"❌ Timeout after multiple retries for {date_str_formatted}."}
                
        # Check if the response contains an error page
        if b"Access Denied" in response.content or b"403 Forbidden" in response.content:
            print(f"🚫 Error: BSE blocked access for {date_str_formatted}.")
            return {"success": False, "error": f"BSE blocked access for {date_str_formatted}."}

        # Extract the file
        output_dir = os.path.join(DATA_DIR, date_str_formatted)
        os.makedirs(output_dir, exist_ok=True)

        if src == "NSE":
            try:
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    z.extractall(output_dir)
                print(f"File extracted successfully for {date_str_formatted}.")
            except zipfile.BadZipFile:
                print(f"BadZipFile error occurred while extracting {date_str_formatted}.")
                return {"success": False, "error": "Failed to extract ZIP file. File might be corrupted."}
        elif src == "BSE":
            file_name = f"BhavCopy_{src}_{sgmt}_{date_str_formatted}.csv"
            file_path = os.path.join(output_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(response.content)
            print(f"File saved successfully for {date_str_formatted} at {file_path}")

        # Locate the specific downloaded CSV file
        if src == "NSE":
            csv_file = os.path.join(output_dir, f"BhavCopy_NSE_{sgmt}_0_0_0_{date_str_formatted}_F_0000.csv")
        elif src == "BSE":
            csv_file = os.path.join(output_dir, f"BhavCopy_{src}_{sgmt}_{date_str_formatted}.csv")

        if not os.path.exists(csv_file):
            print(f"No matching CSV file found for {date_str_formatted}.")
            return {"success": False, "error": f"No matching CSV file found for {date_str_formatted}."}
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
                            TtlTrfVal, TtlNbOfTxsExctd, SsnId, NewBrdLotQty, Rmks, Rsvd1, Rsvd2, Rsvd3, Rsvd4, 
                            created_at, updated_at
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
                        )
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
                            Rsvd4 = VALUES(Rsvd4),
                            updated_at = NOW();
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


################################################################## MCX.html START ######################################################
def reload_data_for_date_mcx(date_str):
    """Reload data for the specified date with detailed error handling and MySQL insertion."""
    try:
        # Format date for NSE URL
        reload_date = datetime.strptime(date_str, '%Y-%m-%d')
        date_str_formatted = reload_date.strftime("%Y%m%d")
        print(f"Starting reload for date: {date_str} (formatted: {date_str_formatted})")

        get_bhavcopy_data(date_str_formatted)

        return {"success": True, "message": f"Data for {date_str_formatted} successfully reloaded."}

    except Exception as e:
        print(f"Unexpected error occurred for {date_str}: {e}")
        return {"success": False, "error": str(e)}
################################################################## MCX.html END ######################################################
