# 🚀 Automated Business Analytics Pipeline

## 📖 Project Overview
The **Automated Business Analytics Pipeline** is a comprehensive, full-stack data engineering and analytics solution designed to process real-time and synthetic business data. The system automatically ingests data, enforces strict validation schemas to ensure data quality, models the cleaned data into a high-performance Star Schema DataMart, and visualizes critical KPIs through an interactive, responsive Streamlit dashboard. 

This project demonstrates the end-to-end lifecycle of data—from raw ingestion to actionable business intelligence—eliminating manual data entry, enforcing data governance, and surfacing revenue growth opportunities.

---

## 🏗️ Architecture & Modules

The pipeline is organized into five distinct modules, each handling a critical phase of the data lifecycle:

### 1. Automated Data Ingestion Pipeline (`ingestion/`)
- **Real-Time API Integration**: Connects to the **Alpha Vantage API** for daily financial stock data and the **World Bank Open Data API** for global economic indicators (GDP growth).
- **Synthetic Data Generation**: Utilizes the Python `faker` library to generate over 5,000 highly realistic monthly CRM and transaction records. Fields include `transaction_id`, timestamp, customer proxies, SKU data, regional assignments, and financial metrics.
- **Staging Area**: All raw data is written to a centralized DuckDB `staging` schema.
- **Audit Logging**: Every ingestion run is logged in the `staging.ingestion_log` table, tracking execution timestamps, data sources, and record counts.

### 2. Automated SQL Validation Scripts (`validation/`)
- **Data Quality Rules**: Executes a suite of SQL-based validation scripts against the staging data to catch anomalies before they reach the data warehouse.
- **Checks Performed**:
  - Missing or `NULL` values in critical columns.
  - Business logic bounds (e.g., Revenue must be > $0 and < $1,000,000).
  - Referential integrity proxies (e.g., ensuring Customer IDs exist).
  - Identification of duplicate `transaction_id`s.
  - Date range bounding.
- **Validation Logging**: Results, including failure rates and records checked, are captured in `staging.validation_log` for monitoring pipeline health over time.

### 3. Centralized DataMart Design & ETL (`datamart/` & `etl/`)
- **Star Schema Modeling**: Data is transformed and loaded into a highly optimized Star Schema residing in the DuckDB `datamart` schema.
  - **Fact Table**: `fact_transactions` (holds measurable, quantitative data).
  - **Dimension Tables**: `dim_date`, `dim_customer`, `dim_product`, `dim_region` (describe the business entities).
- **Idempotent ETL**: A Python-based ETL orchestration script reads valid records from staging, type-casts fields, and performs `UPSERT` operations (`ON CONFLICT DO UPDATE/NOTHING`) to gracefully handle existing records and deduplication.

### 4. Secured Data Processing Workflows (`docs/`)
- **Parameterized Queries**: All database insertions use safe, parameterized SQL queries to prevent SQL injection vulnerabilities.
- **Audit Trails**: The `datamart.audit_log` table tracks every ETL run, noting the user, pipeline step, rows affected, and completion status.
- **Lineage**: Full data lineage is documented in `docs/data_lineage.md`, providing a transparent view of the data's journey from API/Faker to the Dashboard.

### 5. Interactive Analytics Dashboard (`dashboard/`)
- **UI/UX**: Flowing data is visualized via a premium, responsive **Streamlit** dashboard enhanced with Plotly charts.
- **Executive KPIs**: High-level metrics showing Total Monthly Revenue (with MoM% change), Data Quality Scores, and anomaly detection flags.
- **Interactive Visualizations**: 
  - Revenue trends over time across different regions.
  - Top 10 product performance metrics.
  - Sales rep performance scatter plots.
  - Lead-to-close funnels based on acquisition channels.
- **Dynamic Filtering**: Users can slice the data instantly by Date Range, Region, Product Category, and Channel.

---

## 🛠️ Technology Stack
| Layer | Technology |
|---|---|
| **Language** | Python 3.x |
| **Ingestion** | `requests`, `pandas`, `faker`, `schedule` |
| **Database Engine** | DuckDB (High-performance analytical SQLite alternative) |
| **Data Validation** | Standard SQL |
| **Dashboarding** | Streamlit, Plotly (`plotly.express`, `plotly.graph_objects`) |
| **Environment Mgt** | `python-dotenv`, `venv` |

---

## 📈 Success Metrics Achieved
- **Volume**: Automated the ingestion of ≥ 5,000 monthly transaction records.
- **Performance**: Dashboard load times consistently < 3 seconds leveraging DuckDB's in-memory analytical processing.
- **Efficiency**: Full end-to-end pipeline runtime (Ingest → Validate → ETL) completes in seconds.
- **Coverage**: 100% of critical fields pass through structural SQL validation logging.

---

## 🚀 Getting Started

Follow these instructions to run the pipeline on your local machine.

### 1. Prerequisites
Ensure you have Python 3.9+ installed on your system.

### 2. Environment Setup
Clone the repository, navigate to the project root, and set up a virtual environment:

```bash
# Create and activate virtual environment (macOS/Linux)
python3 -m venv venv
source venv/bin/activate

# Install required dependencies
pip install -r requirements.txt
```

### 3. Configuration
The system uses environment variables for secure credential management.
Create or edit the `.env` file in the root directory:
```env
# Get a free key at: https://www.alphavantage.co/support/#api-key
ALPHA_VANTAGE_API_KEY="demo"
ENVIRONMENT="development"
```

### 4. Execution
You can run the entire pipeline end-to-end utilizing the provided orchestrator, or run each module independently.

**Run End-to-End Orchestrator (Recommended):**
```bash
python main.py
```

**Run Modules Independently:**
```bash
# 1. Ingest Data -> Staging
python ingestion/pipeline.py

# 2. Validate Staging Data
python validation/validator.py

# 3. Transform & Load -> DataMart
python etl/transform_load.py
```

### 5. Launch the Dashboard
Once the data has been loaded into the DataMart, spin up the Streamlit application to view the insights:

```bash
streamlit run dashboard/app.py
```
*The dashboard will automatically open in your default web browser at `http://localhost:8501`.*
