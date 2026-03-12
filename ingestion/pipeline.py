import os
import time
import requests
import pandas as pd
import duckdb
import schedule
from faker import Faker
from dotenv import load_dotenv
from datetime import datetime, timedelta
import random

load_dotenv()

DB_PATH = 'datamart/analytics.duckdb'

def setup_db():
    # Only setting up staging here. Datamart schema will be handled separately.
    conn = duckdb.connect(DB_PATH)
    conn.execute("CREATE SCHEMA IF NOT EXISTS staging;")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS staging.raw_transactions (
        transaction_id VARCHAR,
        date TIMESTAMP,
        customer_id VARCHAR,
        product_sku VARCHAR,
        region VARCHAR,
        revenue_usd DOUBLE,
        units_sold INTEGER,
        channel VARCHAR,
        rep_id VARCHAR
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS staging.api_financial_data (
        symbol VARCHAR,
        date TIMESTAMP,
        open DOUBLE,
        high DOUBLE,
        low DOUBLE,
        close DOUBLE,
        volume BIGINT
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS staging.api_economic_data (
        country_code VARCHAR,
        date TIMESTAMP,
        gdp_growth DOUBLE
    );
    """)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS staging.ingestion_log (
        run_timestamp TIMESTAMP,
        source VARCHAR,
        records_loaded INTEGER,
        status VARCHAR
    );
    """)
    conn.close()

def log_ingestion(conn, source, count, status):
    print(f"[{datetime.now()}] Ingestion: {source} | Count: {count} | Status: {status}")
    conn.execute("INSERT INTO staging.ingestion_log VALUES (?, ?, ?, ?)", 
                 [datetime.now(), source, count, status])

def generate_transactions(num_records=5000):
    fake = Faker()
    regions = ['North America', 'EMEA', 'APAC', 'LATAM']
    channels = ['Direct', 'Partner', 'Online', 'Retail']
    
    data = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    for _ in range(num_records):
        data.append({
            'transaction_id': fake.uuid4(),
            'date': fake.date_time_between(start_date=start_date, end_date=end_date),
            'customer_id': f"CUST-{fake.random_int(min=1000, max=9999)}",
            'product_sku': f"SKU-{fake.random_int(min=100, max=999)}",
            'region': random.choice(regions),
            'revenue_usd': round(random.uniform(10.0, 5000.0), 2),
            'units_sold': fake.random_int(min=1, max=100),
            'channel': random.choice(channels),
            'rep_id': f"REP-{fake.random_int(min=10, max=99)}"
        })
    df = pd.DataFrame(data)
    
    # Introduce some bad data to trigger validations later (25% anomaly rate as requested)
    bad_rows_idx = df.sample(frac=0.25).index
    for idx in bad_rows_idx:
        issue_type = random.choice(['null_revenue', 'negative_revenue', 'huge_revenue', 'null_date', 'null_tx_id'])
        if issue_type == 'null_revenue':
            df.at[idx, 'revenue_usd'] = None
        elif issue_type == 'negative_revenue':
            df.at[idx, 'revenue_usd'] = -150.0
        elif issue_type == 'huge_revenue':
            df.at[idx, 'revenue_usd'] = 2000000.0
        elif issue_type == 'null_date':
            df.at[idx, 'date'] = None
        elif issue_type == 'null_tx_id':
            df.at[idx, 'transaction_id'] = None

    conn = duckdb.connect(DB_PATH)
    try:
        # Clear out previous raw data for the day
        conn.execute("DELETE FROM staging.raw_transactions")
        conn.execute("INSERT INTO staging.raw_transactions SELECT * FROM df")
        log_ingestion(conn, 'Faker Transactions', len(df), 'Success')
    except Exception as e:
        log_ingestion(conn, 'Faker Transactions', 0, f'Failed: {str(e)}')
    finally:
        if len(df) < num_records:
            print(f"ALERT: Expected {num_records} records but generated {len(df)}.")
        conn.close()

def fetch_alpha_vantage():
    api_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
    symbol = 'IBM'
    url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={api_key}'
    
    try:
        response = requests.get(url)
        data = response.json()
        if 'Time Series (Daily)' in data:
            ts = data['Time Series (Daily)']
            records = []
            for date_str, metrics in ts.items():
                records.append({
                    'symbol': symbol,
                    'date': pd.to_datetime(date_str),
                    'open': float(metrics['1. open']),
                    'high': float(metrics['2. high']),
                    'low': float(metrics['3. low']),
                    'close': float(metrics['4. close']),
                    'volume': int(metrics['5. volume'])
                })
            df = pd.DataFrame(records)
            
            conn = duckdb.connect(DB_PATH)
            conn.execute(f"DELETE FROM staging.api_financial_data WHERE symbol='{symbol}'")
            conn.execute("INSERT INTO staging.api_financial_data SELECT * FROM df")
            log_ingestion(conn, 'Alpha Vantage', len(df), 'Success')
            conn.close()
        else:
            print(f"Alpha Vantage API error or rate limit: {data}")
            # Optional: Add mock data if rate-limited
    except Exception as e:
        print(f"Alpha Vantage fetch failed: {e}")

def fetch_world_bank():
    # GDP growth (annual %) indicator: NY.GDP.MKTP.KD.ZG
    url = 'https://api.worldbank.org/v2/country/all/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page=100'
    try:
        response = requests.get(url)
        data = response.json()
        if len(data) > 1:
            records = []
            for item in data[1]:
                if item['value'] is not None:
                    records.append({
                        'country_code': item['countryiso3code'],
                        'date': pd.to_datetime(item['date'], format='%Y'),
                        'gdp_growth': float(item['value'])
                    })
            df = pd.DataFrame(records)
            conn = duckdb.connect(DB_PATH)
            conn.execute("DELETE FROM staging.api_economic_data")
            conn.execute("INSERT INTO staging.api_economic_data SELECT * FROM df")
            log_ingestion(conn, 'World Bank', len(df), 'Success')
            conn.close()
        else:
            print("World Bank API unexpectedly empty.")
    except Exception as e:
        print(f"World Bank fetch failed: {e}")

def run_pipeline():
    print(f"--- Starting Ingestion Pipeline at {datetime.now()} ---")
    setup_db()
    generate_transactions(5000)
    fetch_alpha_vantage()
    fetch_world_bank()
    print("--- Pipeline Run Complete ---\n")

if __name__ == "__main__":
    run_pipeline()
