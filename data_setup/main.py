import os
import shutil
import requests

# Create the target directory if it doesn't exist
DATA_DIR = os.path.join("data_setup", "data")
os.makedirs(DATA_DIR, exist_ok=True)

# File paths
db_url = "https://storage.googleapis.com/benchmarks-artifacts/travel-db/travel2.sqlite"
local_file = os.path.join(DATA_DIR, "travel2.sqlite")
backup_file = os.path.join(DATA_DIR, "travel2.backup.sqlite")

# Download the database if it doesn't already exist
if not os.path.exists(local_file):
    response = requests.get(db_url)
    response.raise_for_status()

    with open(local_file, "wb") as f:
        f.write(response.content)

    # Create a backup copy
    shutil.copy(local_file, backup_file)

    print(f"Database downloaded to: {local_file}")
    print(f"Backup created at: {backup_file}")
else:
    print(f"Database already exists at: {local_file}")
