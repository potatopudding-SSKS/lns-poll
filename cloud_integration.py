# Modified streamlit_app.py for Google Sheets integration
# Replace the existing save_response function with this cloud-enabled version

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import glob
import pickle
from streamlit_sortables import sort_items

# NEW: Add these imports for Google Sheets
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    st.warning("Google Sheets integration not available. Install: pip install gspread google-auth")

def save_response_cloud(response_data):
    """
    Save response to cloud storage (Google Sheets) with local fallback
    """
    response_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Try Google Sheets first
    if GOOGLE_SHEETS_AVAILABLE and "gcp_service_account" in st.secrets:
        if save_to_google_sheets(response_data):
            st.success("✅ Response saved to cloud storage")
            return True
    
    # Fallback to local storage
    save_to_local_storage(response_data)
    st.info("💾 Response saved locally (for cloud deployment, configure Google Sheets)")
    return True

def save_to_google_sheets(response_data):
    """Save response to Google Sheets"""
    try:
        # Setup Google Sheets connection
        scope = ['https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive']
        
        creds_dict = st.secrets["gcp_service_account"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Open spreadsheet
        spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
        sheet = client.open_by_key(spreadsheet_id).sheet1
        
        # Prepare row data - flatten nested structures
        row_data = []
        
        # Basic info
        row_data.extend([
            response_data.get('timestamp', ''),
            response_data.get('participant_id', ''),
            response_data.get('age', ''),
            response_data.get('mother_tongue', '')
        ])
        
        # Audio ratings
        audio_keys = [k for k in response_data.keys() if 'naturalness_' in k or 'trustworthiness_' in k]
        for key in sorted(audio_keys):
            row_data.append(response_data.get(key, ''))
        
        # Rankings
        ranking_keys = [k for k in response_data.keys() if 'ranking_' in k]
        for key in sorted(ranking_keys):
            row_data.append(response_data.get(key, ''))
        
        # Follow-up responses
        followup_keys = [k for k in response_data.keys() if 'followup_' in k]
        for key in sorted(followup_keys):
            row_data.append(response_data.get(key, ''))
        
        # Append to sheet
        sheet.append_row(row_data)
        return True
        
    except Exception as e:
        st.error(f"Google Sheets error: {e}")
        return False

def save_to_local_storage(response_data):
    """Fallback local storage"""
    DATA_FILE = "survey_responses.pkl"
    
    try:
        # Load existing responses
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                responses = pickle.load(f)
        else:
            responses = []
        
        # Add new response
        responses.append(response_data)
        
        # Save back to file
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(responses, f)
            
    except Exception as e:
        st.error(f"Local storage error: {e}")

def load_responses_cloud():
    """Load responses from cloud storage with local fallback"""
    
    # Try Google Sheets first
    if GOOGLE_SHEETS_AVAILABLE and "gcp_service_account" in st.secrets:
        cloud_responses = load_from_google_sheets()
        if cloud_responses:
            return cloud_responses
    
    # Fallback to local storage
    return load_from_local_storage()

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

def load_from_local_storage():
    """Load from local pickle file"""
    DATA_FILE = "survey_responses.pkl"
    
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                return pickle.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading local data: {e}")
        return []

# =================================================================
# SETUP INSTRUCTIONS FOR GOOGLE SHEETS
# =================================================================

def show_setup_instructions():
    """Display setup instructions for Google Sheets integration"""
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("Cloud Storage Setup")
    
    if not GOOGLE_SHEETS_AVAILABLE:
        st.sidebar.error("Google Sheets not available")
        st.sidebar.code("pip install gspread google-auth")
        return
    
    if "gcp_service_account" not in st.secrets:
        st.sidebar.warning("Google Sheets not configured")
        
        with st.sidebar.expander("Setup Instructions"):
            st.markdown("""
            **Steps to enable cloud storage:**
            
            1. **Create Google Sheets:**
               - Create a new Google Sheets document
               - Copy the spreadsheet ID from the URL
            
            2. **Get Service Account:**
               - Go to Google Cloud Console
               - Create a service account
               - Download the JSON key file
            
            3. **Configure Streamlit Secrets:**
               Add to `.streamlit/secrets.toml`:
               ```toml
               [gcp_service_account]
               type = "service_account"
               project_id = "your-project"
               private_key_id = "key-id"
               private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
               client_email = "your-service@project.iam.gserviceaccount.com"
               client_id = "123456789"
               auth_uri = "https://accounts.google.com/o/oauth2/auth"
               token_uri = "https://oauth2.googleapis.com/token"
               
               [google_sheets]
               spreadsheet_id = "your-spreadsheet-id"
               ```
            
            4. **Share the Sheet:**
               - Share your Google Sheet with the service account email
               - Give it Editor permissions
            """)
    else:
        st.sidebar.success("✅ Cloud storage configured")
        st.sidebar.info(f"Spreadsheet: {st.secrets['google_sheets']['spreadsheet_id'][:10]}...")

# =================================================================
# REQUIREMENTS UPDATE
# =================================================================

def get_cloud_requirements():
    """Additional requirements for cloud storage"""
    
    cloud_requirements = """
# Add these to requirements.txt for Google Sheets integration:
gspread==5.11.3
google-auth==2.23.3
google-auth-oauthlib==1.1.0
google-auth-httplib2==0.1.1

# Alternative cloud storage options:
# supabase==1.2.0  # For Supabase
# pymongo==4.5.0   # For MongoDB
# boto3==1.29.7    # For AWS
"""
    
    return cloud_requirements

if __name__ == "__main__":
    print("Cloud Storage Integration for Survey App")
    print("=" * 50)
    print(get_cloud_requirements())