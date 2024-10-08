import os
import json
import csv
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Debugging: Print environment variables
print(f"SUPABASE_URL: {os.environ.get('SUPABASE_URL')}")
print(f"SUPABASE_API_KEY: {os.environ.get('SUPABASE_API_KEY')}")

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_API_KEY")

# Check if the variables are None
if not url or not key:
    raise ValueError("SUPABASE_URL and SUPABASE_API_KEY must be set")

supabase: Client = create_client(url, key)

def update_snapshot():
    # Fetch all table names in the public schema
    response = supabase.rpc('get_public_tables').execute()
    
    if hasattr(response, 'error') and response.error is not None:
        raise Exception(f"Error fetching tables: {response.error}")
    
    tables = response.data

    print(f"Tables fetched: {tables}")  # Debug print

    # Ensure the directory exists
    os.makedirs('public_data/snapshots/latest', exist_ok=True)

    for table in tables:
        print(f"Processing table: {table}")  # Debug print
        # Fetch data from Supabase
        response = supabase.table(table).select("*").execute()
        
        if hasattr(response, 'error') and response.error is not None:
            print(f"Error fetching data from table {table}: {response.error}")  # Debug print
            continue

        data = response.data

        # Write the updated data to a CSV file
        with open(f'public_data/snapshots/latest/{table}.csv', 'w', newline='') as f:
            if data:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)

    # Update metadata
    metadata = {
        'last_updated': datetime.now().isoformat(),
        'table_record_counts': {}
    }
    for table in tables:
        try:
            count = len(supabase.table(table).select("*").execute().data)
            metadata['table_record_counts'][table] = count
        except Exception as e:
            print(f"Error getting record count for table {table}: {str(e)}")
            metadata['table_record_counts'][table] = "Error"

    with open('public_data/snapshots/latest/json/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=2)

if __name__ == "__main__":
    update_snapshot()