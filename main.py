import os

def run_all():
    print("1. Executing Ingestion...")
    os.system("python ingestion/pipeline.py")
    
    print("2. Executing Validation...")
    os.system("python validation/validator.py")
    
    print("3. Executing ETL...")
    os.system("python etl/transform_load.py")
    
    print("Pipeline Complete!")

if __name__ == "__main__":
    run_all()
