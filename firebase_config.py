import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
from datetime import datetime
from typing import List, Dict, Optional

class FirebaseService:
    """Firebase service for handling poll data storage and retrieval"""
    
    def __init__(self):
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase app with credentials from Streamlit secrets"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Get Firebase credentials from Streamlit secrets
                firebase_creds = st.secrets.get("firebase", {})
                
                if firebase_creds:
                    # Create credentials object from secrets
                    cred = credentials.Certificate({
                        "type": firebase_creds.get("type"),
                        "project_id": firebase_creds.get("project_id"),
                        "private_key_id": firebase_creds.get("private_key_id"),
                        "private_key": firebase_creds.get("private_key").replace('\\n', '\n'),
                        "client_email": firebase_creds.get("client_email"),
                        "client_id": firebase_creds.get("client_id"),
                        "auth_uri": firebase_creds.get("auth_uri"),
                        "token_uri": firebase_creds.get("token_uri"),
                        "auth_provider_x509_cert_url": firebase_creds.get("auth_provider_x509_cert_url"),
                        "client_x509_cert_url": firebase_creds.get("client_x509_cert_url")
                    })
                    
                    # Initialize the app
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    return True
                else:
                    st.warning("Firebase credentials not found in secrets. Using local storage.")
                    return False
            else:
                # App already initialized
                self.db = firestore.client()
                return True
                
        except Exception as e:
            st.error(f"Error initializing Firebase: {str(e)}")
            return False
    
    def is_available(self) -> bool:
        """Check if Firebase is properly initialized"""
        return self.db is not None
    
    def save_response(self, response_data: Dict) -> bool:
        """Save a survey response to Firebase"""
        try:
            if not self.is_available():
                return False
            
            # Add timestamp if not present
            if 'timestamp' not in response_data:
                response_data['timestamp'] = datetime.now().isoformat()
            
            # Use participant_id as document ID for easier querying
            doc_id = response_data.get('participant_id', datetime.now().isoformat())
            
            # Save to 'survey_responses' collection
            doc_ref = self.db.collection('survey_responses').document(doc_id)
            doc_ref.set(response_data)
            
            return True
            
        except Exception as e:
            st.error(f"Error saving response to Firebase: {str(e)}")
            return False
    
    def load_all_responses(self) -> List[Dict]:
        """Load all survey responses from Firebase"""
        try:
            if not self.is_available():
                return []
            
            docs = self.db.collection('survey_responses').stream()
            responses = []
            
            for doc in docs:
                response_data = doc.to_dict()
                responses.append(response_data)
            
            # Sort by timestamp
            responses.sort(key=lambda x: x.get('timestamp', ''))
            
            return responses
            
        except Exception as e:
            st.error(f"Error loading responses from Firebase: {str(e)}")
            return []
    
    def get_response_count(self) -> int:
        """Get total number of responses"""
        try:
            if not self.is_available():
                return 0
            
            docs = self.db.collection('survey_responses').stream()
            return len(list(docs))
            
        except Exception as e:
            st.error(f"Error getting response count: {str(e)}")
            return 0
    
    def delete_all_responses(self) -> bool:
        """Delete all responses (admin function)"""
        try:
            if not self.is_available():
                return False
            
            docs = self.db.collection('survey_responses').stream()
            for doc in docs:
                doc.reference.delete()
            
            return True
            
        except Exception as e:
            st.error(f"Error deleting responses: {str(e)}")
            return False

# Global instance
firebase_service = FirebaseService()