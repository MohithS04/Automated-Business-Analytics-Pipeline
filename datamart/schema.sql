CREATE SCHEMA IF NOT EXISTS datamart;

-- Dimension: Region
CREATE SEQUENCE IF NOT EXISTS datamart.seq_dim_region;
CREATE TABLE IF NOT EXISTS datamart.dim_region (
    region_key INTEGER DEFAULT nextval('datamart.seq_dim_region'),
    region_name VARCHAR UNIQUE,
    country VARCHAR,
    territory VARCHAR,
    PRIMARY KEY (region_key)
);

-- Dimension: Product
CREATE SEQUENCE IF NOT EXISTS datamart.seq_dim_product;
CREATE TABLE IF NOT EXISTS datamart.dim_product (
    product_key INTEGER DEFAULT nextval('datamart.seq_dim_product'),
    product_sku VARCHAR UNIQUE,
    category VARCHAR,
    subcategory VARCHAR,
    unit_cost DOUBLE,
    PRIMARY KEY (product_key)
);

-- Dimension: Customer
CREATE SEQUENCE IF NOT EXISTS datamart.seq_dim_customer;
CREATE TABLE IF NOT EXISTS datamart.dim_customer (
    customer_key INTEGER DEFAULT nextval('datamart.seq_dim_customer'),
    customer_id VARCHAR UNIQUE,
    segment VARCHAR,
    region VARCHAR,
    acquisition_channel VARCHAR,
    PRIMARY KEY (customer_key)
);

-- Dimension: Date
CREATE TABLE IF NOT EXISTS datamart.dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE,
    month INTEGER,
    quarter INTEGER,
    year INTEGER,
    day_of_week INTEGER
);

-- Fact: Transactions
CREATE TABLE IF NOT EXISTS datamart.fact_transactions (
    transaction_id VARCHAR PRIMARY KEY,
    date_key INTEGER,
    customer_key INTEGER,
    product_key INTEGER,
    region_key INTEGER,
    revenue_usd DOUBLE,
    units_sold INTEGER,
    channel VARCHAR,
    rep_id VARCHAR
);

-- Reporting Views
CREATE OR REPLACE VIEW datamart.monthly_revenue_by_region AS
SELECT 
    d.year,
    d.month,
    r.region_name,
    SUM(f.revenue_usd) as total_revenue,
    SUM(f.units_sold) as total_units
FROM datamart.fact_transactions f
JOIN datamart.dim_date d ON f.date_key = d.date_key
JOIN datamart.dim_region r ON f.region_key = r.region_key
GROUP BY 1, 2, 3;

CREATE OR REPLACE VIEW datamart.top_products_by_quarter AS
SELECT 
    d.year,
    d.quarter,
    p.product_sku,
    p.category,
    SUM(f.revenue_usd) as total_revenue
FROM datamart.fact_transactions f
JOIN datamart.dim_date d ON f.date_key = d.date_key
JOIN datamart.dim_product p ON f.product_key = p.product_key
GROUP BY 1, 2, 3, 4;

CREATE OR REPLACE VIEW datamart.customer_lifetime_value_summary AS
SELECT 
    c.customer_id,
    c.segment,
    MIN(d.date) as first_purchase_date,
    MAX(d.date) as latest_purchase_date,
    COUNT(DISTINCT f.transaction_id) as total_orders,
    SUM(f.revenue_usd) as lifetime_revenue
FROM datamart.fact_transactions f
JOIN datamart.dim_customer c ON f.customer_key = c.customer_key
JOIN datamart.dim_date d ON f.date_key = d.date_key
GROUP BY 1, 2;

CREATE OR REPLACE VIEW datamart.rep_performance_scorecard AS
SELECT 
    f.rep_id,
    r.region_name,
    COUNT(f.transaction_id) as deals_closed,
    SUM(f.revenue_usd) as total_revenue,
    SUM(f.units_sold) as total_units
FROM datamart.fact_transactions f
JOIN datamart.dim_region r ON f.region_key = r.region_key
GROUP BY 1, 2;
