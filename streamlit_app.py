import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import glob
import pickle
import random
from streamlit_sortables import sort_items

# Configuration variables
N_RANDOM_CLIPS = 10  # Number of random clips to show all participants
M_LANGUAGE_CLIPS = 5  # Number of language-specific clips to show

# Initialize Firebase service with caching
@st.cache_resource
def get_firebase_service():
    """Initialize Firebase service with caching"""
    try:
        from firebase_config import FirebaseService
        return FirebaseService()
    except Exception as e:
        return None

# Get Firebase service
firebase_service = get_firebase_service()

# Cloud storage imports (with fallback for local development)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    CLOUD_STORAGE_AVAILABLE = True
except ImportError:
    CLOUD_STORAGE_AVAILABLE = False

# Set page configuration
st.set_page_config(
    page_title="Distinguishing between AI and Human Newscasters",
    page_icon="L",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data persistence file
DATA_FILE = "survey_responses.pkl"

def load_responses():
    """Load responses with Firebase support and fallbacks"""
    # Try Firebase first
    if firebase_service and firebase_service.is_available():
        try:
            responses = firebase_service.load_all_responses()
            if responses:
                return responses
        except Exception as e:
            pass  # Silently fail and try fallbacks
    
    # Fallback to Google Sheets if configured
    if CLOUD_STORAGE_AVAILABLE and "gcp_service_account" in st.secrets:
        project_id = st.secrets["gcp_service_account"].get("project_id", "")
        private_key = st.secrets["gcp_service_account"].get("private_key", "")
        client_email = st.secrets["gcp_service_account"].get("client_email", "")
        
        # Check if we have real credentials (not placeholders)
        is_real_credentials = (
            project_id and 
            project_id not in ["your-project-id", "placeholder-project"] and
            private_key and 
            "BEGIN PRIVATE KEY" in private_key and 
            "..." not in private_key and
            len(private_key) > 100 and
            client_email and 
            "@" in client_email and
            ".iam.gserviceaccount.com" in client_email
        )
        
        if is_real_credentials:
            try:
                return load_from_google_sheets()
            except Exception as e:
                pass  # Silently fall back to local storage
    
    # Final fallback to local storage
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                return pickle.load(f)
        return []
    except Exception as e:
        return []

def load_from_google_sheets():
    """Load responses from Google Sheets"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(st.secrets["google_sheets"]["spreadsheet_id"]).sheet1
    records = sheet.get_all_records()
    
    # Convert back to original format
    responses = []
    for record in records:
        try:
            # Try to parse complete JSON response first
            if 'complete_response' in record and record['complete_response']:
                response = json.loads(record['complete_response'])
            else:
                # Fallback to individual fields
                response = {
                    'timestamp': record.get('timestamp', ''),
                    'participant_id': record.get('participant_id', ''),
                    'age': record.get('age', ''),
                    'mother_tongue': record.get('mother_tongue', ''),
                    'naturalness_1': record.get('naturalness_1', ''),
                    'trustworthiness_1': record.get('trustworthiness_1', ''),
                }
            responses.append(response)
        except Exception as e:
            continue  # Skip malformed records
    
    return responses

def save_responses(responses):
    """Save responses to persistent storage with Firebase support"""
    # Try Firebase first
    if firebase_service.is_available():
        try:
            # Save the latest response (assuming responses is a list and we want the last one)
            if responses:
                latest_response = responses[-1] if isinstance(responses, list) else responses
                success = firebase_service.save_response(latest_response)
                if success:
                    return
        except Exception as e:
            st.warning(f"Firebase save failed, falling back to local storage: {str(e)}")
    
    # Fallback to local storage
    try:
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(responses, f)
    except Exception as e:
        pass  # Silently ignore save errors

def save_single_response(response_data):
    """Save a single response to Firebase or fallback storage"""
    # Try Firebase first
    if firebase_service.is_available():
        try:
            success = firebase_service.save_response(response_data)
            if success:
                return True
        except Exception as e:
            st.warning(f"Firebase save failed: {str(e)}")
    
    # Fallback to adding to session state and local storage
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    
    st.session_state.responses.append(response_data)
    save_responses(st.session_state.responses)
    return True

# Initialize session state for storing responses
if 'responses' not in st.session_state:
    st.session_state.responses = load_responses()

if 'survey_step' not in st.session_state:
    st.session_state.survey_step = 'participant_info'

if 'current_clip' not in st.session_state:
    st.session_state.current_clip = 0

if 'current_responses' not in st.session_state:
    st.session_state.current_responses = {}

if 'ranking_complete' not in st.session_state:
    st.session_state.ranking_complete = {}

if 'participant_audio_clips' not in st.session_state:
    st.session_state.participant_audio_clips = {}

# Clean CSS for better styling
st.markdown("""
<style>
    /* Increase overall font size */
    .main .block-container {
        font-size: 1.2rem;
    }
    
    /* Larger headers */
    .main-header {
        font-size: 3rem;
        color: #64B5F6;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Larger subheaders */
    h2, h3 {
        font-size: 1.5rem !important;
    }
    
    /* Larger radio button text */
    .stRadio > div {
        font-size: 1.1rem !important;
    }
    
    /* Larger slider text and styling */
    .stSlider > div {
        font-size: 1.1rem !important;
    }
    
    .stSlider > div > div > div {
        font-size: 1.1rem !important;
    }
    
    /* Larger form labels */
    .stSelectbox > label, .stSlider > label, .stRadio > label, .stTextInput > label {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
    }
    
    /* Larger markdown text */
    .stMarkdown p {
        font-size: 1.1rem !important;
    }
    
    .audio-section {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #64B5F6;
        margin: 1rem 0;
        font-size: 1.1rem;
    }
    
    .follow-up-section {
        background-color: #0F172A;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #F59E0B;
        margin: 1rem 0;
        font-size: 1.1rem;
    }
    
    .section-divider {
        border-top: 2px solid #444;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Linguistic features for ranking with explanations
LINGUISTIC_FEATURES = [
    "Rate of speech",
    "Tone", 
    "Inflection",
    "Intonation",
    "Stress"
]

# Explanations for linguistic features
FEATURE_EXPLANATIONS = {
    "Rate of speech": "How fast or slow the speaker talks",
    "Tone": "The attitude or feeling in the speaker's voice (friendly, serious, confident, etc.)",
    "Inflection": "How the voice goes up and down within words",
    "Intonation": "The overall melody and flow of the speech",
    "Stress": "Which words or parts the speaker emphasizes to make them stand out"
}

# Follow-up questions based on most influential feature
FOLLOW_UP_QUESTIONS = {
    "Rate of speech": [
        {
            "id": "pace_assessment",
            "text": "Did you find the rate of speech to be natural?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Too slow", "Just right", "Too fast"]
        },
        {
            "id": "urgency_perception", 
            "text": "Did the speed make the news sound urgent?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Very calm", "Normal", "Very urgent"]
        }
    ],
    "Tone": [
        {
            "id": "tone_formality",
            "text": "How formal did the speaker sound?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Very casual", "Normal", "Very formal"]
        },
        {
            "id": "tone_confidence",
            "text": "How confident did the speaker sound?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Not confident", "Normal", "Very confident"]
        }
    ],
    "Inflection": [
        {
            "id": "inflection_naturalness",
            "text": "Did the voice changes sound natural?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Very fake", "Normal", "Very natural"]
        },
        {
            "id": "inflection_understanding",
            "text": "Does the inflection affect your ability to understand the speech?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Made it harder", "No difference", "Made it easier"]
        }
    ],
    "Intonation": [
        {
            "id": "intonation_variety",
            "text": "How much did the melodic pattern of the voice change?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Very flat", "Normal", "Very varied"]
        },
        {
            "id": "emotional_impact",
            "text": "How did the melodic pattern affect the way you felt?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Negative feeling", "No feeling", "Positive feeling"]
        }
    ],
    "Stress": [
        {
            "id": "stress_appropriateness",
            "text": "Were the right words emphasized?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Wrong words", "Okay", "Right words"]
        },
        {
            "id": "stress_comprehension",
            "text": "Did the emphasized words help you understand?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Made it harder", "No difference", "Made it easier"]
        }
    ]
}

def get_all_audio_files():
    """Get all audio files from audio folder and subfolders organized by location"""
    audio_folder = "audio"
    if not os.path.exists(audio_folder):
        return {"general": [], "language_specific": {}}
    
    audio_extensions = [".mp3", ".wav", ".m4a", ".ogg"]
    general_files = []
    language_specific = {}
    
    # Get general audio files (root level)
    for file in os.listdir(audio_folder):
        file_path = os.path.join(audio_folder, file)
        if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in audio_extensions):
            general_files.append(file_path)
    
    # Get language-specific audio files (subfolders)
    for item in os.listdir(audio_folder):
        item_path = os.path.join(audio_folder, item)
        if os.path.isdir(item_path):
            language_files = []
            for file in os.listdir(item_path):
                file_path = os.path.join(item_path, file)
                if os.path.isfile(file_path) and any(file.lower().endswith(ext) for ext in audio_extensions):
                    language_files.append(file_path)
            if language_files:
                language_specific[item.lower()] = language_files
    
    return {"general": general_files, "language_specific": language_specific}

def create_audio_clip_dict(file_path, clip_number):
    """Create a standardized audio clip dictionary"""
    filename = os.path.basename(file_path)
    name_without_ext = os.path.splitext(filename)[0]
    title = name_without_ext.replace("_", " ").replace("-", " ").title()
    
    return {
        "file": file_path,
        "title": title,
        "questions": [
            {
                "id": f"attitude_{clip_number}",
                "text": "Did the reporter have an appropriate attitude while reporting?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5],
                "labels": ["Not appropriate at all", "Very appropriate"]
            },
            {
                "id": f"naturalness_{clip_number}",
                "text": "How natural does the speech sound?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5],
                "labels": ["Very unnatural", "Very natural"]
            },
            {
                "id": f"trustworthiness_{clip_number}",
                "text": "How trustworthy/credible does it seem?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5],
                "labels": ["Not trustworthy/credible at all", "Very trustworthy/credible"]
            }
        ]
    }

def get_participant_audio_clips(mother_tongue=None):
    """Get randomized audio clips for a participant based on their mother tongue"""
    all_files = get_all_audio_files()
    selected_clips = {}
    clip_counter = 1
    
    # Select N random general clips
    general_files = all_files["general"]
    if len(general_files) > 0:
        n_clips = min(N_RANDOM_CLIPS, len(general_files))
        selected_general = random.sample(general_files, n_clips)
        
        for file_path in selected_general:
            clip_id = f"clip_{clip_counter}"
            selected_clips[clip_id] = create_audio_clip_dict(file_path, clip_counter)
            clip_counter += 1
    
    # If mother tongue matches a subfolder, add M random clips from that language
    if mother_tongue and mother_tongue.lower() in all_files["language_specific"]:
        language_files = all_files["language_specific"][mother_tongue.lower()]
        if len(language_files) > 0:
            m_clips = min(M_LANGUAGE_CLIPS, len(language_files))
            selected_language = random.sample(language_files, m_clips)
            
            for file_path in selected_language:
                clip_id = f"clip_{clip_counter}"
                selected_clips[clip_id] = create_audio_clip_dict(file_path, clip_counter)
                clip_counter += 1
    
    return selected_clips

# Don't load audio clips at module level anymore - they'll be loaded per participant
AUDIO_CLIPS = {}

def save_response(response_data):
    """Save response with Firebase priority and proper error handling"""
    response_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Try Firebase first
    if firebase_service and firebase_service.is_available():
        try:
            success = firebase_service.save_response(response_data)
            if success:
                # Update session state
                if 'responses' not in st.session_state:
                    st.session_state.responses = []
                st.session_state.responses.append(response_data)
                return True
        except Exception as e:
            pass  # Silently fail and try fallbacks
    
    # Fallback to Google Sheets
    if CLOUD_STORAGE_AVAILABLE and "gcp_service_account" in st.secrets:
        project_id = st.secrets["gcp_service_account"].get("project_id", "")
        private_key = st.secrets["gcp_service_account"].get("private_key", "")
        
        # Check if we have real credentials (not placeholders)
        if project_id and project_id != "your-project-id" and "BEGIN PRIVATE KEY" in private_key and "..." not in private_key:
            try:
                save_to_google_sheets(response_data)
                st.session_state.responses.append(response_data)
                return True
            except Exception as e:
                pass  # Silently fail and try local storage
    
    # Final fallback to local storage
    if 'responses' not in st.session_state:
        st.session_state.responses = []
    st.session_state.responses.append(response_data)
    save_responses(st.session_state.responses)
    return True

def save_to_google_sheets(response_data):
    """Save response to Google Sheets"""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)
    
    sheet = client.open_by_key(st.secrets["google_sheets"]["spreadsheet_id"]).sheet1
    
    # Convert response to row format - flatten all data
    row = [
        response_data.get('timestamp', ''),
        response_data.get('participant_id', ''),
        response_data.get('age', ''),
        response_data.get('mother_tongue', ''),
        response_data.get('naturalness_1', ''),
        response_data.get('trustworthiness_1', ''),
        json.dumps(response_data)  # Store complete response as JSON
    ]
    
    sheet.append_row(row)

def create_drag_drop_ranking(clip_id):
    """Create drag and drop ranking interface using streamlit-sortables"""
    st.markdown("**Which of the following features do you think influenced your opinion the most?**")
    
    # Display feature explanations
    st.markdown("**Linguistic Feature Definitions:**")
    for feature in LINGUISTIC_FEATURES:
        if feature in FEATURE_EXPLANATIONS:
            st.markdown(f"• **{feature}**: {FEATURE_EXPLANATIONS[feature]}")
    
    st.markdown("---")
    st.markdown("*Drag and drop to rearrange from most influential (top) to least influential (bottom):*")
    
    # Use streamlit-sortables for drag and drop
    try:
        sorted_items = sort_items(
            LINGUISTIC_FEATURES,
            direction="vertical",
            key=f"sortable_{clip_id}",
            multi_containers=False
        )
        
        # Display current ranking
        st.markdown("**Your Current Ranking:**")
        for i, item in enumerate(sorted_items):
            st.markdown(f"**{i+1}. {item}**")
        
        # Convert to ranking dictionary for processing
        ranking_dict = {}
        for i, feature in enumerate(sorted_items):
            ranking_dict[feature] = i + 1  # 1 = most influential
        
        return ranking_dict, sorted_items[:2]  # Return top 2 features
        
    except Exception as e:
        st.error(f"Drag-and-drop failed: {e}")
        st.markdown("**Using manual ranking instead:**")
        
        # Simple fallback - just ask for top 2 most influential
        st.markdown("Please select your **top 2 most influential** features:")
        
        first_choice = st.selectbox(
            "Most influential feature:",
            options=LINGUISTIC_FEATURES,
            key=f"first_choice_{clip_id}"
        )
        
        remaining_features = [f for f in LINGUISTIC_FEATURES if f != first_choice]
        second_choice = st.selectbox(
            "Second most influential feature:",
            options=remaining_features,
            key=f"second_choice_{clip_id}"
        )
        
        # Create a simple ranking dict for compatibility
        ranking_dict = {first_choice: 1, second_choice: 2}
        for i, feature in enumerate(LINGUISTIC_FEATURES):
            if feature not in ranking_dict:
                ranking_dict[feature] = i + 3
        
        return ranking_dict, [first_choice, second_choice]

def main():
    st.markdown('<h1 class="main-header">Distinguishing between AI and Human Newscasters</h1>', unsafe_allow_html=True)
    st.markdown("**Research Study: How Linguistic Features Affect Perception of AI vs Human Speech**")
    
    # Check if audio files exist
    all_files = get_all_audio_files()
    if not all_files["general"] and not all_files["language_specific"]:
        st.error("No audio files found in the 'audio' folder. Please add audio files (.mp3, .wav, .m4a, .ogg) to continue.")
        st.info("Expected audio folder location: `audio/`")
        return
    
    # Progress indicator
    if st.session_state.survey_step != 'participant_info' and st.session_state.survey_step != 'completed':
        participant_clips = st.session_state.participant_audio_clips
        if participant_clips:
            total_clips = len(participant_clips)
            progress = (st.session_state.current_clip) / total_clips
            st.progress(progress, text=f"Audio Clip {st.session_state.current_clip + 1} of {total_clips}")
    
    # Survey steps
    if st.session_state.survey_step == 'participant_info':
        show_participant_info()
    elif st.session_state.survey_step == 'audio_questions':
        show_audio_questions()
    elif st.session_state.survey_step == 'ranking':
        show_ranking_interface()
    elif st.session_state.survey_step == 'follow_up':
        show_follow_up_questions()
    elif st.session_state.survey_step == 'completed':
        show_completion_page()

def show_participant_info():
    """Show participant information form"""
    st.header("Participant Information")
    
    with st.form("participant_form"):
        age = st.number_input("Age", min_value=18, max_value=100, value=None)
        mother_tongue = st.text_input("Mother tongue")
        
        if st.form_submit_button("Start Survey", type="primary"):
            if not mother_tongue.strip():
                st.error("Please enter your mother tongue.")
            else:
                # Generate randomized audio clips for this participant
                participant_clips = get_participant_audio_clips(mother_tongue.strip())
                
                if not participant_clips:
                    st.error("No audio files found. Please contact the administrator.")
                    return
                
                st.session_state.participant_audio_clips = participant_clips
                st.session_state.current_responses = {
                    'participant_id': f"participant_{len(st.session_state.responses)+1}",
                    'age': age,
                    'mother_tongue': mother_tongue.strip(),
                    'n_general_clips': sum(1 for k, v in participant_clips.items() if not any(lang in v['file'].lower() for lang in get_all_audio_files()['language_specific'].keys())),
                    'n_language_clips': sum(1 for k, v in participant_clips.items() if any(lang in v['file'].lower() for lang in get_all_audio_files()['language_specific'].keys()))
                }
                st.session_state.survey_step = 'audio_questions'
                st.session_state.current_clip = 0
                st.rerun()

def show_audio_questions():
    """Show audio questions for current clip"""
    participant_clips = st.session_state.participant_audio_clips
    
    if not participant_clips:
        st.error("No audio clips assigned. Please restart the survey.")
        return
    
    clip_ids = list(participant_clips.keys())
    current_clip_id = clip_ids[st.session_state.current_clip]
    clip_data = participant_clips[current_clip_id]
    
    st.markdown(f'<div class="audio-section">', unsafe_allow_html=True)
    st.subheader(f"{clip_data['title']}")
    
    # Display audio file
    if os.path.exists(clip_data['file']):
        st.audio(clip_data['file'])
    else:
        st.warning(f"Audio file not found: {clip_data['file']}")
    
    st.markdown("**Please listen to the audio clip above and answer the following questions:**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.form(f"audio_form_{current_clip_id}"):
        responses = {}
        
        # Standard questions for this clip
        for question in clip_data['questions']:
            if question['type'] == 'scale':
                response = st.select_slider(
                    question['text'],
                    options=question['scale'],
                    format_func=lambda x, labels=question['labels']: f"{x} - {labels[0] if x == 1 else labels[1] if x == 7 else ''}",
                    key=f"{current_clip_id}_{question['id']}"
                )
                responses[question['id']] = response
        
        if st.form_submit_button("Continue to Ranking", type="primary"):
            # Save current responses
            st.session_state.current_responses.update(responses)
            st.session_state.survey_step = 'ranking'
            st.rerun()

def show_ranking_interface():
    """Show drag-and-drop ranking interface"""
    participant_clips = st.session_state.participant_audio_clips
    clip_ids = list(participant_clips.keys())
    current_clip_id = clip_ids[st.session_state.current_clip]
    
    st.subheader(f"Feature Ranking - {participant_clips[current_clip_id]['title']}")
    
    # Create the drag-drop interface
    ranking_dict, top_2_features = create_drag_drop_ranking(current_clip_id)
    
    st.info("You will be asked follow-up questions about each linguistic feature.")
    
    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("← Back to Questions", key="back_to_questions"):
            st.session_state.survey_step = 'audio_questions'
            st.rerun()
    
    with col2:
        if st.button("Continue to Follow-up →", type="primary", key="continue_to_followup"):
            # Save rankings
            for feature, rank in ranking_dict.items():
                st.session_state.current_responses[f"{current_clip_id}_ranking_{feature.replace(' ', '_').lower()}"] = rank
            
            # Save top 2 features for follow-up questions
            st.session_state.current_responses[f"{current_clip_id}_top_features"] = top_2_features
            st.session_state.survey_step = 'follow_up'
            st.rerun()

def show_follow_up_questions():
    """Show follow-up questions for all linguistic features"""
    participant_clips = st.session_state.participant_audio_clips
    clip_ids = list(participant_clips.keys())
    current_clip_id = clip_ids[st.session_state.current_clip]
    
    st.markdown(f'<div class="follow-up-section">', unsafe_allow_html=True)
    st.subheader(f"Follow-up Questions")
    st.markdown(f"Please answer the following questions about each linguistic feature:")
    st.markdown('</div>', unsafe_allow_html=True)
    
    with st.form(f"followup_form_{current_clip_id}"):
        follow_up_responses = {}
        
        # Questions for all linguistic features
        for feature in LINGUISTIC_FEATURES:
            if feature in FOLLOW_UP_QUESTIONS:
                st.markdown(f"**{feature}**")
                if feature in FEATURE_EXPLANATIONS:
                    st.markdown(f"*{FEATURE_EXPLANATIONS[feature]}*")
                for question in FOLLOW_UP_QUESTIONS[feature]:
                    if question['type'] == 'slider':
                        response = st.select_slider(
                            question['text'],
                            options=question['scale'],
                            value=3,  # Default to middle value
                            format_func=lambda x, labels=question['labels']: f"{x} - {labels[0] if x == 1 else labels[1] if x == 3 else labels[2] if x == 5 else ''}",
                            key=f"{current_clip_id}_followup_{feature.replace(' ', '_').lower()}_{question['id']}"
                        )
                    else:
                        # Fallback for any remaining radio questions
                        response = st.radio(
                            question['text'],
                            options=question.get('options', []),
                            key=f"{current_clip_id}_followup_{feature.replace(' ', '_').lower()}_{question['id']}"
                        )
                    
                    follow_up_responses[f"{current_clip_id}_followup_{feature.replace(' ', '_').lower()}_{question['id']}"] = response
                
                st.markdown("---")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.form_submit_button("← Back to Ranking", key="back_to_ranking"):
                st.session_state.survey_step = 'ranking'
                st.rerun()
        
        with col2:
            if st.form_submit_button("Next →", type="primary", key="next_clip"):
                # Save follow-up responses
                st.session_state.current_responses.update(follow_up_responses)
                
                # Move to next clip or finish
                participant_clips = st.session_state.participant_audio_clips
                if st.session_state.current_clip < len(participant_clips) - 1:
                    st.session_state.current_clip += 1
                    st.session_state.survey_step = 'audio_questions'
                else:
                    # Complete survey
                    save_response(st.session_state.current_responses)
                    st.session_state.survey_step = 'completed'
                st.rerun()

def show_completion_page():
    """Show survey completion page"""
    st.success("Survey Completed Successfully!")
    st.markdown("Thank you for participating in our research on distinguishing between AI and human newscasters!")
    st.balloons()
    
    if st.button("Take Another Survey"):
        # Reset session state
        st.session_state.survey_step = 'participant_info'
        st.session_state.current_clip = 0
        st.session_state.current_responses = {}
        st.session_state.participant_audio_clips = {}
        st.rerun()

if __name__ == "__main__":
    main()