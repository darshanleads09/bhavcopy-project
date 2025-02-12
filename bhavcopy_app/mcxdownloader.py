import requests
import json
import time
import mysql.connector
from datetime import datetime
import gc  # Import garbage collector
from config import DB_CONFIG, BASE_URLS

def get_bhavcopy_data(date, instrument_name="ALL"):
    """
    Fetches MCX BhavCopy data via POST request, extracts JSON data, and inserts it into MySQL.
    """
    session = requests.Session()
    homepage_url = "https://www.mcxindia.com/market-data/bhavcopy"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": "https://www.mcxindia.com/",
        "sec-fetch-site": "same-origin",
        "sec-fetch-mode": "navigate",
        "sec-fetch-user": "?1",
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        print("🔄 Fetching homepage to get session cookies...")
        response = session.get(homepage_url, headers=headers, timeout=10)
        response.raise_for_status()
        time.sleep(2)

        cookies = session.cookies.get_dict()
        cookie_string = "; ".join([f"{key}={value}" for key, value in cookies.items()])
        print(f"✅ Cookies Obtained: {cookie_string}")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching cookies: {e}")
        return

    url = "https://www.mcxindia.com/backpage.aspx/GetDateWiseBhavCopy"
    post_headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Cookie": cookie_string,  # Pass cookies
        "Referer": "https://www.mcxindia.com/market-data/bhavcopy",
        "User-Agent": headers["User-Agent"],
    }

    payload = json.dumps({"Date": date, "InstrumentName": instrument_name})

    try:
        print(f"📡 Sending POST request for BhavCopy: Date={date}, Instrument={instrument_name}")
        response = session.post(url, headers=post_headers, data=payload, timeout=10)
        response.raise_for_status()
        response_json = response.json()

        with open("mcx_response.json", "w", encoding="utf-8") as f:
            json.dump(response_json, f, indent=4)

        print("🔍 Response JSON saved to mcx_response.json.")

        if isinstance(response_json, dict) and "d" in response_json:
            data_json = response_json["d"]  # ✅ FIX: Do NOT parse again with json.loads()

            if "Data" in data_json and isinstance(data_json["Data"], list):
                print(f"✅ {len(data_json['Data'])} records found. Inserting into database...")
                insert_into_db(data_json["Data"])
            else:
                print("⚠️ No data found in JSON response.")

        else:
            print("⚠️ Expected key 'd' not found in response.")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error during request: {e}")
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def insert_into_db(bhavcopy_data):
    """Inserts MCX BhavCopy data into MySQL using batch insert with memory optimization."""
    
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor(buffered=True)  # ✅ Use buffered cursor to optimize memory usage

        insert_query = """
        INSERT INTO bhav_mcx (
            date, symbol, expiry_date, open_price, high_price, low_price, close_price, 
            previous_close, volume, volume_in_thousands, value, open_interest, 
            date_display, instrument_name, strike_price, option_type, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        ON DUPLICATE KEY UPDATE 
            open_price = VALUES(open_price),
            high_price = VALUES(high_price),
            low_price = VALUES(low_price),
            close_price = VALUES(close_price),
            previous_close = VALUES(previous_close),
            volume = VALUES(volume),
            value = VALUES(value),
            open_interest = VALUES(open_interest),
            updated_at = NOW();
        """

        batch_size = 50  # ✅ Further reduced batch size to 50 records
        records = []

        for record in bhavcopy_data:
            try:
                records.append((
                    datetime.strptime(record["Date"], "%m/%d/%Y").date(),
                    record["Symbol"].strip(),
                    datetime.strptime(record["ExpiryDate"], "%d%b%Y").date(),
                    record["Open"], record["High"], record["Low"], record["Close"],
                    record["PreviousClose"], record["Volume"], record["VolumeInThousands"].strip(),
                    record["Value"], record["OpenInterest"], record["DateDisplay"].strip(),
                    record["InstrumentName"].strip(), record["StrikePrice"], record["OptionType"].strip()
                ))

                # ✅ Insert in batches of 50 records
                if len(records) >= batch_size:
                    cursor.executemany(insert_query, records)
                    conn.commit()
                    print(f"✅ Inserted {len(records)} records into mcx_bhavcopy.")

                    records = []  # Clear batch
                    gc.collect()  # ✅ Force garbage collection to free memory

            except mysql.connector.Error as e:
                print(f"❌ Error inserting record: {record} - {e}")

        # Insert any remaining records
        if records:
            cursor.executemany(insert_query, records)
            conn.commit()
            print(f"✅ Inserted {len(records)} remaining records into mcx_bhavcopy.")
            gc.collect()  # ✅ Free memory explicitly

    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        conn.rollback()  # Rollback the last transaction

    finally:
        cursor.close()
        conn.close()
        print("🔄 MySQL connection closed.")  # Log when connection closes


# Example Usage
if __name__ == "__main__":
    get_bhavcopy_data("20250210", "ALL")