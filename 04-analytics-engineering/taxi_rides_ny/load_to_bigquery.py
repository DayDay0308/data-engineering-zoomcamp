import requests
import gzip
import io
import time
from google.cloud import bigquery
from google.oauth2 import service_account

KEY_FILE = r"C:\Users\dramo\Downloads\zoomcamp-project-493610-711ab3e52b77.json"
PROJECT_ID = "zoomcamp-project-493610"
DATASET = "nytaxi"
BASE_URL = "https://github.com/DataTalksClub/nyc-tlc-data/releases/download"

credentials = service_account.Credentials.from_service_account_file(KEY_FILE)
client = bigquery.Client(credentials=credentials, project=PROJECT_ID)

YELLOW_SCHEMA = [
    bigquery.SchemaField("VendorID", "STRING"),
    bigquery.SchemaField("tpep_pickup_datetime", "TIMESTAMP"),
    bigquery.SchemaField("tpep_dropoff_datetime", "TIMESTAMP"),
    bigquery.SchemaField("passenger_count", "FLOAT"),
    bigquery.SchemaField("trip_distance", "FLOAT"),
    bigquery.SchemaField("RatecodeID", "FLOAT"),
    bigquery.SchemaField("store_and_fwd_flag", "STRING"),
    bigquery.SchemaField("PULocationID", "STRING"),
    bigquery.SchemaField("DOLocationID", "STRING"),
    bigquery.SchemaField("payment_type", "FLOAT"),
    bigquery.SchemaField("fare_amount", "FLOAT"),
    bigquery.SchemaField("extra", "FLOAT"),
    bigquery.SchemaField("mta_tax", "FLOAT"),
    bigquery.SchemaField("tip_amount", "FLOAT"),
    bigquery.SchemaField("tolls_amount", "FLOAT"),
    bigquery.SchemaField("improvement_surcharge", "FLOAT"),
    bigquery.SchemaField("total_amount", "FLOAT"),
    bigquery.SchemaField("congestion_surcharge", "FLOAT"),
]

def download_with_retry(url, retries=5):
    for attempt in range(retries):
        try:
            response = requests.get(url, stream=True, timeout=120)
            response.raise_for_status()
            return response
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                print("Retrying in 10 seconds...")
                time.sleep(10)
    return None

def load_file(taxi_type, year, month):
    filename = f"{taxi_type}_tripdata_{year}-{month:02d}.csv.gz"
    url = f"{BASE_URL}/{taxi_type}/{filename}"
    table_id = f"{PROJECT_ID}.{DATASET}.{taxi_type}_tripdata"

    print(f"Downloading {filename}...")
    response = download_with_retry(url)
    if response is None:
        print(f"Skipping {filename} after multiple failures")
        return

    data = io.BytesIO(response.content)

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        autodetect=False,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND,
        skip_leading_rows=1,
        schema=YELLOW_SCHEMA,
    )

    try:
        with gzip.open(data, 'rb') as f:
            job = client.load_table_from_file(f, table_id, job_config=job_config)
            job.result()
        print(f"✅ Loaded {filename}")
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")

# Only load the 2 missing files
load_file("yellow", 2019, 5)
load_file("yellow", 2019, 6)

print("Done!")