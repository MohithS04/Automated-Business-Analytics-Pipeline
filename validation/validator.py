import duckdb
from datetime import datetime

DB_PATH = 'datamart/analytics.duckdb'

def setup_validation_tables():
    conn = duckdb.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS staging.validation_log (
        run_id VARCHAR,
        check_name VARCHAR,
        records_checked INTEGER,
        records_failed INTEGER,
        failure_rate DOUBLE,
        run_at TIMESTAMP
    );
    """)
    conn.close()

def run_validations():
    setup_validation_tables()
    conn = duckdb.connect(DB_PATH)
    
    with open('validation/sql_checks.sql', 'r') as f:
        sql_script = f.read()
    
    queries = [q.strip() for q in sql_script.split(';') if q.strip()]
    
    run_id = f"RUN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    print(f"--- Starting Data Validation ({run_id}) ---")
    for query in queries:
        try:
            result = conn.execute(query).fetchone()
            if result:
                check_name, records_checked, records_failed = result
                # Handle None values
                records_checked = records_checked or 0
                records_failed = records_failed or 0
                
                failure_rate = (records_failed / records_checked) * 100 if records_checked > 0 else 0
                
                print(f"[{check_name}] Checked: {records_checked}, Failed: {records_failed} ({failure_rate:.2f}%)")
                
                conn.execute("""
                    INSERT INTO staging.validation_log 
                    VALUES (?, ?, ?, ?, ?, ?)
                """, [run_id, check_name, records_checked, records_failed, failure_rate, datetime.now()])
        except Exception as e:
            print(f"Error running check: {e}\nQuery: {query}")
            
    conn.close()
    print("--- Validation Complete ---\n")

if __name__ == "__main__":
    run_validations()
