# Streamlit Cloud Deployment Guide

This guide explains how to deploy both the survey application and admin portal to Streamlit Cloud.

## Prerequisites

1. GitHub repository with your survey code
2. Streamlit Cloud account (https://streamlit.io/cloud)
3. Audio files uploaded to your repository

## Important: Data Storage Considerations

**Local Development vs Cloud Deployment:**
- Local development uses `survey_responses.pkl` file storage
- For cloud deployment, consider using a cloud database for data persistence
- Multiple Streamlit Cloud instances cannot share local file storage

**Recommended Cloud Storage Options:**
1. **Google Sheets API** (simple, built-in Streamlit support)
2. **Supabase** (PostgreSQL database with simple API)
3. **MongoDB Atlas** (document database)
4. **AWS S3 + DynamoDB** (enterprise solution)

## Deployment Steps

### Option 1: Single Repository, Two Apps

1. **Deploy Main Survey:**
   - Connect your repository to Streamlit Cloud
   - Set main file path: `streamlit_app.py`
   - App URL will be: `https://your-app-name.streamlit.app`

2. **Deploy Admin Portal:**
   - Create a second Streamlit Cloud app from the same repository
   - Set main file path: `admin.py`
   - Admin URL will be: `https://your-admin-app-name.streamlit.app`

### Option 2: Separate Repositories

1. **Survey Repository:**
   - Contains: `streamlit_app.py`, `requirements.txt`, `audio/` folder
   - Deploy as main survey app

2. **Admin Repository:**
   - Contains: `admin.py`, `requirements.txt`
   - Deploy as separate admin app

## Security Configuration

### Update Admin Password

Before deploying, update the admin password in `admin.py`:

```python
# Option 1: Hardcoded (not recommended for production)
if password == "your_secure_password_here":

# Option 2: Using Streamlit Secrets (recommended)
if password == st.secrets["ADMIN_PASSWORD"]:
```

### Using Streamlit Secrets

1. In your Streamlit Cloud app settings, go to "Secrets"
2. Add your configuration:

```toml
[passwords]
ADMIN_PASSWORD = "your_secure_password"

[database]
CONNECTION_STRING = "your_database_connection_string"
```

3. Update your code to use secrets:

```python
import streamlit as st

# Access secrets
admin_password = st.secrets["passwords"]["ADMIN_PASSWORD"]
db_connection = st.secrets["database"]["CONNECTION_STRING"]
```

## Cloud Database Integration Example

### Using Google Sheets (Simple Option)

1. Install additional dependencies in `requirements.txt`:
```
gspread
google-auth
```

2. Replace file storage with Google Sheets:

```python
import gspread
from google.oauth2.service_account import Credentials

def save_to_sheets(response_data):
    # Configure Google Sheets API
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    # Use Streamlit secrets for credentials
    creds_dict = st.secrets["gcp_service_account"]
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    
    client = gspread.authorize(creds)
    sheet = client.open("Survey Responses").sheet1
    
    # Append response data
    sheet.append_row([
        response_data['timestamp'],
        response_data['age'],
        response_data['mother_tongue'],
        # ... other fields
    ])
```

## Audio File Management

### For Cloud Deployment:

1. **Small Audio Files (<25MB total):**
   - Include in your Git repository under `audio/` folder
   - Commit and push to trigger redeployment

2. **Large Audio Files:**
   - Use Git LFS (Large File Storage)
   - Or host audio files externally (AWS S3, Google Cloud Storage)
   - Update `get_audio_files()` function to fetch from cloud storage

### External Audio Storage Example:

```python
def get_audio_files():
    """Fetch audio files from cloud storage"""
    # Example using direct URLs
    audio_files = {
        "clip_1": {
            "file": "https://your-storage.com/audio/news_clip_1.mp3",
            "title": "News Clip 1",
            "questions": [...]
        }
    }
    return audio_files
```

## Deployment Checklist

- [ ] Repository connected to Streamlit Cloud
- [ ] Requirements.txt updated with all dependencies
- [ ] Audio files accessible (local or cloud storage)
- [ ] Admin password updated for production
- [ ] Secrets configured (if using cloud database)
- [ ] Both survey and admin apps deployed
- [ ] Data storage solution implemented
- [ ] URLs documented and shared with stakeholders

## URLs After Deployment

**Survey Application:**
- URL: `https://your-survey-app.streamlit.app`
- Share this URL with research participants

**Admin Portal:**
- URL: `https://your-admin-app.streamlit.app`
- Keep this URL private, share only with authorized personnel

## Monitoring and Maintenance

1. **Monitor App Usage:**
   - Check Streamlit Cloud analytics
   - Monitor response collection rates

2. **Data Backup:**
   - Regular exports of response data
   - Backup cloud database if used

3. **Updates:**
   - Push updates to GitHub repository
   - Streamlit Cloud auto-deploys on new commits

## Troubleshooting

### Common Issues:

1. **Import Errors:**
   - Ensure all dependencies in `requirements.txt`
   - Check Python version compatibility

2. **Audio Files Not Loading:**
   - Verify file paths and permissions
   - Check file size limits (GitHub: 100MB, Git LFS: larger files)

3. **Data Not Persisting:**
   - Local file storage doesn't work across cloud instances
   - Implement cloud database solution

4. **Admin Portal Access:**
   - Verify password configuration
   - Check Streamlit secrets setup

### Getting Help:

- Streamlit Documentation: https://docs.streamlit.io/
- Streamlit Community Forum: https://discuss.streamlit.io/
- GitHub Issues: Create issues in your repository