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
        self.available = False
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase app with credentials from Streamlit secrets"""
        try:
            # Check if Firebase is already initialized
            if firebase_admin._apps:
                st.info("🔥 Firebase already initialized")
                self.db = firestore.client()
                self.available = True
                return
            
            # Check if secrets are available
            if "firebase" not in st.secrets:
                st.error("❌ Firebase secrets not found in st.secrets")
                self.available = False
                return
            
            # Validate required fields
            required_fields = ['type', 'project_id', 'private_key', 'client_email']
            firebase_config = st.secrets["firebase"]
            
            for field in required_fields:
                if field not in firebase_config:
                    st.error(f"❌ Missing Firebase config field: {field}")
                    self.available = False
                    return
                if not firebase_config[field]:
                    st.error(f"❌ Empty Firebase config field: {field}")
                    self.available = False
                    return
            
            st.info(f"🔥 Initializing Firebase for project: {firebase_config['project_id']}")
            
            # Create credentials object from secrets
            cred = credentials.Certificate({
                "type": firebase_config.get("type"),
                "project_id": firebase_config.get("project_id"),
                "private_key_id": firebase_config.get("private_key_id"),
                "private_key": firebase_config.get("private_key").replace('\\n', '\n'),
                "client_email": firebase_config.get("client_email"),
                "client_id": firebase_config.get("client_id"),
                "auth_uri": firebase_config.get("auth_uri"),
                "token_uri": firebase_config.get("token_uri"),
                "auth_provider_x509_cert_url": firebase_config.get("auth_provider_x509_cert_url"),
                "client_x509_cert_url": firebase_config.get("client_x509_cert_url")
            })
            
            # Initialize the app
            firebase_admin.initialize_app(cred)
            self.db = firestore.client()
            self.available = True
            st.success("✅ Firebase initialized successfully!")
            
        except Exception as e:
            st.error(f"❌ Firebase initialization failed: {str(e)}")
            st.error(f"Error type: {type(e).__name__}")
            self.available = False
    
    def is_available(self) -> bool:
        """Check if Firebase is properly initialized"""
        return self.available and self.db is not None
    
    def save_response(self, response_data: Dict) -> bool:
        """Save a survey response to Firebase"""
        if not self.is_available():
            st.error("❌ Firebase not available for saving")
            return False
        
        try:
            # Add timestamp if not present
            if 'timestamp' not in response_data:
                response_data['timestamp'] = datetime.now().isoformat()
            
            # Generate document ID
            doc_id = f"{response_data.get('participant_id', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            st.info(f"📝 Saving to Firebase document: {doc_id}")
            
            # Save to 'survey_responses' collection
            doc_ref = self.db.collection('survey_responses').document(doc_id)
            doc_ref.set(response_data)
            
            st.success(f"✅ Successfully saved document: {doc_id}")
            return True
            
        except Exception as e:
            st.error(f"❌ Error saving to Firebase: {str(e)}")
            st.error(f"Error type: {type(e).__name__}")
            return False
    
    def load_all_responses(self) -> List[Dict]:
        """Load all survey responses from Firebase"""
        if not self.is_available():
            st.warning("🔥 Firebase not available for loading")
            return []
        
        try:
            st.info("📖 Loading data from Firebase...")
            docs = self.db.collection('survey_responses').stream()
            responses = []
            
            for doc in docs:
                response_data = doc.to_dict()
                responses.append(response_data)
            
            # Sort by timestamp
            responses.sort(key=lambda x: x.get('timestamp', ''))
            
            st.success(f"✅ Loaded {len(responses)} responses from Firebase")
            return responses
            
        except Exception as e:
            st.error(f"❌ Error loading from Firebase: {str(e)}")
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