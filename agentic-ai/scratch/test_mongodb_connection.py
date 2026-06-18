import sys
from pathlib import Path

# Add project root to path so we can import config
project_root = str(Path(__file__).resolve().parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from config.settings import get_settings

def test_connection():
    settings = get_settings()
    uri = settings.MONGODB_URI
    
    print(f"Connecting to: {uri}")
    client = MongoClient(uri, serverSelectionTimeoutMS=5000)
    
    try:
        # The ismaster command is cheap and does not require auth.
        client.admin.command('ping')
        print("MongoDB connection successful!")
    except ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    test_connection()
