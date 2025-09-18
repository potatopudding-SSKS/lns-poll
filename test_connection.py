import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Google Sheets Connection Test")

try:
    # Test if we can connect to Google Sheets
    if "gcp_service_account" in st.secrets:
        st.write("✅ Found GCP service account in secrets")
        
        # Try to create credentials
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        st.write("✅ Created credentials successfully")
        
        # Try to connect to Google Sheets
        gc = gspread.authorize(credentials)
        st.write("✅ Authorized with Google Sheets")
        
        # Try to open the spreadsheet
        if "google_sheets" in st.secrets and "spreadsheet_id" in st.secrets["google_sheets"]:
            spreadsheet_id = st.secrets["google_sheets"]["spreadsheet_id"]
            st.write(f"📊 Trying to open spreadsheet: {spreadsheet_id}")
            
            try:
                spreadsheet = gc.open_by_key(spreadsheet_id)
                st.success(f"✅ Successfully opened spreadsheet: {spreadsheet.title}")
                
                # List worksheets
                worksheets = spreadsheet.worksheets()
                st.write(f"📋 Found {len(worksheets)} worksheets:")
                for ws in worksheets:
                    st.write(f"  - {ws.title}")
                
            except Exception as e:
                st.error(f"❌ Failed to open spreadsheet: {str(e)}")
                st.write("This could mean:")
                st.write("1. The spreadsheet ID is incorrect")
                st.write("2. The service account doesn't have access to the spreadsheet")
                st.write("3. The spreadsheet doesn't exist")
        else:
            st.warning("⚠️ No spreadsheet_id found in secrets")
            
    else:
        st.error("❌ No GCP service account found in secrets")
        
except Exception as e:
    st.error(f"❌ Connection test failed: {str(e)}")
    st.write("Error details:", e)