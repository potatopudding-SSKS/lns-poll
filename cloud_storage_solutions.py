# Cloud Storage Solutions for Survey Data
# Choose ONE of these solutions for web deployment

# =================================================================
# SOLUTION 1: Google Sheets (Recommended for simplicity)
# =================================================================

import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def setup_google_sheets():
    """
    Setup Google Sheets for data storage
    
    Steps to implement:
    1. Create a Google Sheets document
    2. Get Google Cloud service account credentials
    3. Share the sheet with the service account email
    4. Add credentials to Streamlit secrets
    """
    
    # This goes in your Streamlit secrets (.streamlit/secrets.toml)
    secrets_example = """
    [gcp_service_account]
    type = "service_account"
    project_id = "your-project-id"
    private_key_id = "key-id"
    private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
    client_email = "your-service-account@your-project.iam.gserviceaccount.com"
    client_id = "client-id"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    
    [google_sheets]
    spreadsheet_id = "your-spreadsheet-id"
    """
    
    return secrets_example

def save_to_google_sheets(response_data):
    """Save response to Google Sheets"""
    try:
        # Setup credentials from Streamlit secrets
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        
        # Connect to Google Sheets
        client = gspread.authorize(creds)
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        # Convert response to row format
        row = [
            response_data.get('timestamp', ''),
            response_data.get('age', ''),
            response_data.get('mother_tongue', ''),
            response_data.get('naturalness_1', ''),
            response_data.get('trustworthiness_1', ''),
            # Add all other fields...
        ]
        
        # Append to sheet
        sheet.append_row(row)
        return True
        
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False

def load_from_google_sheets():
    """Load responses from Google Sheets"""
    try:
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        
        client = gspread.authorize(creds)
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        # Get all records
        records = sheet.get_all_records()
        return records
        
    except Exception as e:
        st.error(f"Error loading from Google Sheets: {e}")
        return []

# =================================================================
# SOLUTION 2: Supabase (PostgreSQL Database)
# =================================================================

def setup_supabase():
    """
    Setup Supabase for data storage
    
    Steps:
    1. Create account at https://supabase.com
    2. Create new project
    3. Create table for survey responses
    4. Get API URL and keys
    """
    
    # SQL to create table in Supabase
    sql_schema = """
    CREATE TABLE survey_responses (
        id SERIAL PRIMARY KEY,
        timestamp TEXT,
        age INTEGER,
        mother_tongue TEXT,
        naturalness_1 INTEGER,
        trustworthiness_1 INTEGER,
        clip_1_ranking_rate_of_speech INTEGER,
        clip_1_ranking_tone INTEGER,
        clip_1_ranking_inflection INTEGER,
        clip_1_ranking_intonation INTEGER,
        clip_1_ranking_stress INTEGER,
        -- Add follow-up questions as JSON or separate columns
        followup_responses JSON,
        created_at TIMESTAMP DEFAULT NOW()
    );
    """
    
    # Streamlit secrets for Supabase
    secrets_example = """
    [supabase]
    url = "https://your-project.supabase.co"
    key = "your-anon-key"
    """
    
    return sql_schema, secrets_example

def save_to_supabase(response_data):
    """Save response to Supabase"""
    try:
        from supabase import create_client, Client
        
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        supabase: Client = create_client(url, key)
        
        # Insert data
        result = supabase.table('survey_responses').insert(response_data).execute()
        return True
        
    except Exception as e:
        st.error(f"Error saving to Supabase: {e}")
        return False

# =================================================================
# SOLUTION 3: MongoDB Atlas (Document Database)
# =================================================================

def setup_mongodb():
    """Setup MongoDB Atlas for data storage"""
    
    secrets_example = """
    [mongodb]
    connection_string = "mongodb+srv://username:password@cluster.mongodb.net/database"
    database_name = "survey_db"
    collection_name = "responses"
    """
    
    return secrets_example

def save_to_mongodb(response_data):
    """Save response to MongoDB"""
    try:
        from pymongo import MongoClient
        
        connection_string = st.secrets["mongodb"]["connection_string"]
        client = MongoClient(connection_string)
        
        db = client[st.secrets["mongodb"]["database_name"]]
        collection = db[st.secrets["mongodb"]["collection_name"]]
        
        # Insert document
        result = collection.insert_one(response_data)
        return True
        
    except Exception as e:
        st.error(f"Error saving to MongoDB: {e}")
        return False

# =================================================================
# SOLUTION 4: AWS S3 + DynamoDB (Enterprise)
# =================================================================

def setup_aws():
    """Setup AWS for data storage"""
    
    secrets_example = """
    [aws]
    access_key_id = "your-access-key"
    secret_access_key = "your-secret-key"
    region = "us-east-1"
    dynamodb_table = "survey-responses"
    """
    
    return secrets_example

def save_to_dynamodb(response_data):
    """Save response to AWS DynamoDB"""
    try:
        import boto3
        
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=st.secrets["aws"]["access_key_id"],
            aws_secret_access_key=st.secrets["aws"]["secret_access_key"],
            region_name=st.secrets["aws"]["region"]
        )
        
        table = dynamodb.Table(st.secrets["aws"]["dynamodb_table"])
        
        # Put item
        response = table.put_item(Item=response_data)
        return True
        
    except Exception as e:
        st.error(f"Error saving to DynamoDB: {e}")
        return False

# =================================================================
# HYBRID SOLUTION: Local + Cloud Fallback
# =================================================================

def save_response_hybrid(response_data):
    """
    Hybrid approach: Try cloud first, fallback to local
    """
    
    # Try cloud storage first
    cloud_success = False
    
    if "gcp_service_account" in st.secrets:
        cloud_success = save_to_google_sheets(response_data)
    elif "supabase" in st.secrets:
        cloud_success = save_to_supabase(response_data)
    elif "mongodb" in st.secrets:
        cloud_success = save_to_mongodb(response_data)
    elif "aws" in st.secrets:
        cloud_success = save_to_dynamodb(response_data)
    
    # Fallback to local storage
    if not cloud_success:
        st.warning("Cloud storage failed, saving locally (data may not persist)")
        save_to_local_pickle(response_data)
    else:
        st.success("Response saved to cloud storage")

def save_to_local_pickle(response_data):
    """Original local storage method"""
    import pickle
    
    DATA_FILE = "survey_responses.pkl"
    
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                responses = pickle.load(f)
        else:
            responses = []
        
        responses.append(response_data)
        
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(responses, f)
            
    except Exception as e:
        st.error(f"Error saving locally: {e}")

# =================================================================
# RECOMMENDATION
# =================================================================

def get_recommendation():
    """
    Recommendation for different use cases
    """
    
    recommendations = {
        "Quick Prototype": "Google Sheets - Easy setup, no coding required",
        "Small Research Project": "Supabase - Free tier, easy to use, SQL queries",
        "Medium Research Project": "MongoDB Atlas - Flexible document storage",
        "Large Enterprise": "AWS DynamoDB - Scalable, enterprise-grade",
        "Academic Institution": "Google Sheets or Supabase - Often free/discounted"
    }
    
    return recommendations

if __name__ == "__main__":
    print("Cloud Storage Solutions for Survey Data")
    print("=" * 50)
    
    recommendations = get_recommendation()
    for use_case, solution in recommendations.items():
        print(f"{use_case}: {solution}")