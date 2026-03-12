import duckdb
from datetime import datetime

DB_PATH = 'datamart/analytics.duckdb'

def setup_datamart(conn):
    with open('datamart/schema.sql', 'r') as f:
        schema_sql = f.read()
    conn.execute(schema_sql)

def transform_and_load():
    conn = duckdb.connect(DB_PATH)
    setup_datamart(conn)
    print(f"--- Starting ETL to DataMart at {datetime.now()} ---")
    
    # Extract only valid records from staging (where date and revenue are valid)
    valid_transactions_query = """
    SELECT * FROM staging.raw_transactions
    WHERE transaction_id IS NOT NULL 
      AND date IS NOT NULL 
      AND revenue_usd > 0
      AND revenue_usd < 1000000
    """
    
    # 1. UPSERT dim_region
    conn.execute(f"""
    INSERT INTO datamart.dim_region (region_name, country, territory)
    SELECT region, 'Unknown', 'Unknown' 
    FROM ({valid_transactions_query}) q
    WHERE region IS NOT NULL
    GROUP BY region
    ON CONFLICT (region_name) DO NOTHING;
    """)
    
    # 2. UPSERT dim_product
    conn.execute(f"""
    INSERT INTO datamart.dim_product (product_sku, category, subcategory, unit_cost)
    SELECT product_sku, 'General', 'General', 10.0
    FROM ({valid_transactions_query}) q
    WHERE product_sku IS NOT NULL
    GROUP BY product_sku
    ON CONFLICT (product_sku) DO NOTHING;
    """)
    
    # 3. UPSERT dim_customer
    conn.execute(f"""
    INSERT INTO datamart.dim_customer (customer_id, segment, region, acquisition_channel)
    SELECT customer_id, 'Standard', MAX(region), MAX(channel)
    FROM ({valid_transactions_query}) q
    WHERE customer_id IS NOT NULL
    GROUP BY customer_id
    ON CONFLICT (customer_id) DO NOTHING;
    """)
    
    # 4. UPSERT dim_date
    conn.execute(f"""
    INSERT INTO datamart.dim_date (date_key, date, month, quarter, year, day_of_week)
    SELECT DISTINCT 
        CAST(strftime((CAST(date AS DATE)), '%Y%m%d') AS INTEGER) as date_key,
        CAST(date AS DATE) as date,
        month(date) as month,
        quarter(date) as quarter,
        year(date) as year,
        dayofweek(date) as day_of_week
    FROM ({valid_transactions_query}) q
    WHERE date IS NOT NULL
    ON CONFLICT (date_key) DO NOTHING;
    """)
    
    # 5. UPSERT fact_transactions
    conn.execute(f"""
    INSERT INTO datamart.fact_transactions 
    (transaction_id, date_key, customer_key, product_key, region_key, revenue_usd, units_sold, channel, rep_id)
    SELECT 
        q.transaction_id,
        CAST(strftime((CAST(q.date AS DATE)), '%Y%m%d') AS INTEGER) as date_key,
        c.customer_key,
        p.product_key,
        r.region_key,
        q.revenue_usd,
        q.units_sold,
        q.channel,
        q.rep_id
    FROM ({valid_transactions_query}) q
    LEFT JOIN datamart.dim_customer c ON q.customer_id = c.customer_id
    LEFT JOIN datamart.dim_product p ON q.product_sku = p.product_sku
    LEFT JOIN datamart.dim_region r ON q.region = r.region_name
    ON CONFLICT (transaction_id) DO UPDATE SET
        revenue_usd = EXCLUDED.revenue_usd,
        units_sold = EXCLUDED.units_sold;
    """)
    
    count = conn.execute("SELECT count(*) FROM datamart.fact_transactions").fetchone()[0]
    print(f"ETL Complete. Fact table now has {count} records.")
    
    conn.execute("CREATE TABLE IF NOT EXISTS datamart.audit_log (run_id VARCHAR, pipeline_step VARCHAR, user_name VARCHAR, rows_affected INTEGER, status VARCHAR, timestamp TIMESTAMP)")
    run_id = f"ETL-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    conn.execute("INSERT INTO datamart.audit_log VALUES (?, ?, ?, ?, ?, ?)",
                 [run_id, 'Transform & Load', 'etl_user', count, 'Success', datetime.now()])
    
    conn.close()

if __name__ == "__main__":
    transform_and_load()
