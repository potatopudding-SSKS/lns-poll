import streamlit as st

st.title("Secrets Test")

# Check if secrets are available
if hasattr(st, 'secrets'):
    st.write("✅ st.secrets is available")
    
    # Check for gcp_service_account
    if "gcp_service_account" in st.secrets:
        st.write("✅ gcp_service_account found in secrets")
        
        # Get the values
        project_id = st.secrets["gcp_service_account"].get("project_id", "")
        private_key = st.secrets["gcp_service_account"].get("private_key", "")
        
        st.write(f"Project ID: {project_id}")
        st.write(f"Private key starts with: {private_key[:50]}...")
        
        # Check the condition
        if project_id and project_id != "your-project-id" and "BEGIN PRIVATE KEY" in private_key and "..." not in private_key:
            st.success("✅ Should show: Cloud Storage: Active")
        else:
            st.warning("⚠️ Should show: Configured with Placeholders")
            st.write(f"- project_id exists: {bool(project_id)}")
            st.write(f"- project_id != 'your-project-id': {project_id != 'your-project-id'}")
            st.write(f"- 'BEGIN PRIVATE KEY' in private_key: {'BEGIN PRIVATE KEY' in private_key}")
            st.write(f"- '...' not in private_key: {'...' not in private_key}")
    else:
        st.error("❌ gcp_service_account NOT found in secrets")
        st.write("Available secrets keys:", list(st.secrets.keys()) if st.secrets else "None")
else:
    st.error("❌ st.secrets not available")