import os
import json

from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Load .env
load_dotenv()

service_account_json = os.getenv("SERVICE_ACCOUNT_JSON")

if not service_account_json:
    raise ValueError("SERVICE_ACCOUNT_JSON is not set in .env")

# Convert JSON string to dict
try:
    service_account_dict = json.loads(service_account_json)
except json.JSONDecodeError as e:
    raise ValueError(f"Invalid SERVICE_ACCOUNT_JSON: {e}")

# Initialize Firebase Admin
cred = credentials.Certificate(service_account_dict)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Firestore client
db = firestore.client()
