# Data Lineage Map

## 1. Data Sources (Ingestion)
The Automated Business Analytics Pipeline ingests data from three core sources:
1. **Faker Library (Synthetic CRM & Transactions)**: Generates 5000+ transaction records mimicking internal databases.
2. **Alpha Vantage API (Financial Data)**: Provides daily stock data for requested symbols.
3. **World Bank Open Data API (Economic Indicators)**: Retrieves annual GDP growth statistics for all countries.

## 2. Staging Layer
Raw data is ingested into the **DuckDB Staging Schema (`staging`)**:
- `staging.raw_transactions`: Holds Faker transactions.
- `staging.api_financial_data`: Holds Alpha Vantage records.
- `staging.api_economic_data`: Holds World Bank indicators.
- `staging.ingestion_log`: Audit trail for every ingestion run, including timestamps, sources, and record counts.

## 3. Data Validation
Following ingestion, structural and business-rule validation checks run against the staging layer (e.g., NULL checks, range checks, referential integrity proxies). 
- **Output**: Logs check results to `staging.validation_log` to monitor data quality trends and record anomalies.

## 4. Transform & Load (ETL)
A Python ETL process (`etl/transform_load.py`) orchestrates data movement from `staging` to `datamart`. 
- Data is type-cast, filtered for validity (e.g., removing negative revenue), and deduplicated.
- Using `ON CONFLICT DO UPDATE/NOTHING`, the system UPSERTs dimensional records and fact transaction data.

## 5. Enterprise DataMart (Analytics Schema)
A structured Star Schema resides in the **DuckDB DataMart Schema (`datamart`)**:
- **Fact Table**: `datamart.fact_transactions`
- **Dimension Tables**: `datamart.dim_region`, `datamart.dim_product`, `datamart.dim_customer`, `datamart.dim_date`
- **Security Check**: An `audit_log` table tracks every ETL run, including rows affected and execution status.

## 6. Access & Visualization (Dashboard)
The **Streamlit Dashboard** queries the `datamart` schema (via standard views or direct aggregations). It surfaces validated KPI metrics, pipeline health (`validation_log` and `ingestion_log`), and interactive data visualizations. No staging data is exposed to end-users.
