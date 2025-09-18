import streamlit as st
import gspread
from google.oauth2.service_account import Credentials

st.title("Create Google Sheets for Survey")

try:
    if "gcp_service_account" in st.secrets:
        st.write("✅ Found GCP service account in secrets")
        
        # Create credentials
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
        )
        st.write("✅ Created credentials successfully")
        
        # Connect to Google Sheets
        gc = gspread.authorize(credentials)
        st.write("✅ Authorized with Google Sheets")
        
        if st.button("Create New Spreadsheet for Survey"):
            try:
                # Create a new spreadsheet
                spreadsheet = gc.create("LnS Poll Survey Responses")
                st.success(f"✅ Created new spreadsheet: {spreadsheet.title}")
                st.write(f"📊 Spreadsheet ID: `{spreadsheet.id}`")
                st.write(f"🔗 Spreadsheet URL: https://docs.google.com/spreadsheets/d/{spreadsheet.id}")
                
                # Set up the header row
                worksheet = spreadsheet.sheet1
                worksheet.update('A1:Z1', [[
                    'Timestamp', 'Age', 'Gender', 'Education', 'News_Consumption', 'Primary_Source',
                    'Trust_Traditional', 'Trust_Social', 'Trust_Podcasts', 'Audio_A_Trustworthy',
                    'Audio_A_Professional', 'Audio_A_Engaging', 'Audio_A_Clear', 'Audio_A_Credible',
                    'Audio_B_Trustworthy', 'Audio_B_Professional', 'Audio_B_Engaging', 'Audio_B_Clear',
                    'Audio_B_Credible', 'Audio_C_Trustworthy', 'Audio_C_Professional', 'Audio_C_Engaging',
                    'Audio_C_Clear', 'Audio_C_Credible', 'Most_Trustworthy_Audio', 'Factors_Influence',
                    'Additional_Comments'
                ]])
                st.success("✅ Set up header row in spreadsheet")
                
                st.markdown("### Next Steps:")
                st.markdown("1. **Copy the Spreadsheet ID above**")
                st.markdown("2. **Update your secrets.toml file** with this new spreadsheet ID")
                st.markdown("3. **The spreadsheet is automatically shared** with your service account")
                
                st.code(f'''
# Update this in your .streamlit/secrets.toml file:
[google_sheets]
spreadsheet_id = "{spreadsheet.id}"
                ''')
                
            except Exception as e:
                st.error(f"❌ Failed to create spreadsheet: {str(e)}")
                
        st.markdown("---")
        st.markdown("### Alternative: Use Existing Spreadsheet")
        st.markdown("If you have an existing Google Sheets spreadsheet:")
        st.markdown("1. Open your spreadsheet in Google Sheets")
        st.markdown("2. Share it with: `lns-32@lns-survey.iam.gserviceaccount.com`")
        st.markdown("3. Give it **Editor** permissions")
        st.markdown("4. Copy the spreadsheet ID from the URL")
        st.markdown("5. Update your secrets.toml file")
        
    else:
        st.error("❌ No GCP service account found in secrets")
        
except Exception as e:
    st.error(f"❌ Setup failed: {str(e)}")
    st.write("Error details:", e)