-- validation/sql_checks.sql

-- 1. Check for NULL values in critical columns
SELECT
    'null_critical_columns' as check_name,
    COUNT(*) as records_checked,
    SUM(CASE WHEN transaction_id IS NULL OR date IS NULL OR revenue_usd IS NULL THEN 1 ELSE 0 END) as records_failed
FROM staging.raw_transactions;

-- 2. Validate revenue_usd is > 0 and < 1,000,000
SELECT
    'invalid_revenue_range' as check_name,
    COUNT(revenue_usd) as records_checked,
    SUM(CASE WHEN revenue_usd <= 0 OR revenue_usd >= 1000000 THEN 1 ELSE 0 END) as records_failed
FROM staging.raw_transactions;

-- 3. Flag duplicate transaction_ids
WITH dupes AS (
    SELECT transaction_id
    FROM staging.raw_transactions
    WHERE transaction_id IS NOT NULL
    GROUP BY transaction_id
    HAVING COUNT(*) > 1
)
SELECT
    'duplicate_transaction_id' as check_name,
    (SELECT COUNT(*) FROM staging.raw_transactions) as records_checked,
    (SELECT COUNT(*) FROM dupes) as records_failed;

-- 4. Verify date ranges are within expected reporting window
SELECT
    'invalid_date_range' as check_name,
    COUNT(date) as records_checked,
    SUM(CASE WHEN date > current_date OR date < current_date - INTERVAL 5 YEAR THEN 1 ELSE 0 END) as records_failed
FROM staging.raw_transactions;

-- 5. Missing Customer ID (Proxy for referential integrity in staging)
SELECT
    'missing_customer_id' as check_name,
    COUNT(*) as records_checked,
    SUM(CASE WHEN customer_id IS NULL OR TRIM(customer_id) = '' THEN 1 ELSE 0 END) as records_failed
FROM staging.raw_transactions;
