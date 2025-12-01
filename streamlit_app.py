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
from copy import deepcopy
from html import escape
from uuid import uuid4
from streamlit_sortables import sort_items

# Configuration variables
N_RANDOM_CLIPS = 4  # Number of random clips to show all participants
M_LANGUAGE_CLIPS = 2  # Number of language-specific clips to show

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
        except Exception:
            pass
    
    # Fallback to local storage
    try:
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(responses, f)
    except Exception as e:
        pass  # Silently ignore save errors

def save_single_response(response_data):
    """Convenience wrapper to save a single response payload."""
    return save_response(response_data)

# Initialize session state for storing responses
if 'responses' not in st.session_state:
    st.session_state.responses = load_responses()

if 'survey_step' not in st.session_state:
    st.session_state.survey_step = 'participant_info'

if 'current_clip' not in st.session_state:
    st.session_state.current_clip = 0

if 'current_responses' not in st.session_state:
    st.session_state.current_responses = {}

if 'participant_audio_clips' not in st.session_state:
    st.session_state.participant_audio_clips = {}

if 'scroll_to_top' not in st.session_state:
    st.session_state.scroll_to_top = False


SCROLL_TO_TOP_SCRIPT = """
<script>
(function() {
    function scrollToTop() {
        // Try scrolling the window
        try { window.scrollTo(0, 0); } catch(e) {}
        
        // Try scrolling the parent window (Streamlit iframe)
        try { window.parent.scrollTo(0, 0); } catch(e) {}
        
        // Try scrolling the document body and html
        try {
            document.body.scrollTop = 0;
            document.documentElement.scrollTop = 0;
        } catch(e) {}
        
        // Try parent document
        try {
            window.parent.document.body.scrollTop = 0;
            window.parent.document.documentElement.scrollTop = 0;
        } catch(e) {}
        
        // Try scrollIntoView on first element
        try {
            const firstElement = document.body.firstElementChild;
            if (firstElement) {
                firstElement.scrollIntoView({ behavior: 'auto', block: 'start' });
            }
        } catch(e) {}
    }
    
    // Execute immediately
    scrollToTop();
    
    // Execute again after a short delay to ensure it works after render
    setTimeout(scrollToTop, 100);
    setTimeout(scrollToTop, 300);
})();
</script>
"""


THEME_OPTIONS = ["Summery Light", "Vibrant Dark"]

THEME_PALETTES = {
    "Summery Light": {
        "background": "#FFF9F1",
        "text": "#2C3E50",
        "primary": "#FF8A65",
        "secondary": "#4DB6AC",
        "accent": "#F9A825",
        "card": "#FFFFFF",
        "card_secondary": "#FFF3E0",
        "notice_bg": "#FFF8E1",
        "notice_border": "#FFE0B2",
        "attention_bg": "#FFE5E5",
        "attention_border": "#FFCDD2",
        "success_bg": "#E8F5E9",
        "success_border": "#C8E6C9",
        "progress_track": "#FFE0B2",
        "slider_track": "#FFB74D",
        "slider_handle": "#FF7043"
    },
    "Vibrant Dark": {
        "background": "#0B1120",
        "text": "#E2E8F0",
        "primary": "#F97316",
        "secondary": "#22D3EE",
        "accent": "#A855F7",
        "card": "#111827",
        "card_secondary": "#1F2937",
        "notice_bg": "#1E293B",
        "notice_border": "#334155",
        "attention_bg": "#2C1C24",
        "attention_border": "#F97316",
        "success_bg": "#1E293B",
        "success_border": "#10B981",
        "progress_track": "#1F2937",
        "slider_track": "#F97316",
        "slider_handle": "#FB923C"
    }
}


MESSAGE_VARIANTS = {
    "neutral": "notice-neutral",
    "attention": "notice-attention",
    "success": "notice-success"
}


def apply_theme(theme_name):
    palette = THEME_PALETTES.get(theme_name, THEME_PALETTES[THEME_OPTIONS[0]])
    css_template = """
    <style>
        body, .stApp {{
            background-color: {background};
            color: {text};
        }}

        .main .block-container {{
            font-size: 1.2rem;
            padding: 2rem 3rem;
            background: transparent;
        }}

        .main-header {{
            font-size: 3rem;
            color: {primary};
            text-align: center;
            margin-bottom: 1.5rem;
        }}

        h2, h3 {{
            font-size: 1.5rem !important;
            color: {text};
        }}

        .stSelectbox > label, .stSlider > label, .stRadio > label, .stTextInput > label {{
            font-size: 1.15rem !important;
            font-weight: 600 !important;
            color: {text};
        }}

        .stMarkdown p {{
            font-size: 1.05rem !important;
            color: {text};
        }}

        .audio-section {{
            background-color: {card};
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid {primary};
            margin: 1rem 0;
            color: {text};
            box-shadow: 0 12px 24px rgba(0,0,0,0.04);
        }}

        .follow-up-section {{
            background-color: {card_secondary};
            padding: 1.5rem;
            border-radius: 12px;
            border-left: 4px solid {accent};
            margin: 1rem 0;
            color: {text};
            box-shadow: 0 12px 24px rgba(0,0,0,0.04);
        }}

        .notice-neutral {{
            background-color: {notice_bg};
            border: 1px solid {notice_border};
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0;
            color: {text};
        }}

        .notice-attention {{
            background-color: {attention_bg};
            border: 1px solid {attention_border};
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0;
            color: {text};
        }}

        .notice-success {{
            background-color: {success_bg};
            border: 1px solid {success_border};
            border-radius: 10px;
            padding: 0.85rem 1rem;
            margin: 0.75rem 0;
            color: {text};
        }}

        div[data-testid="stProgress"] {{
            height: 14px;
            border-radius: 8px;
            background-color: {progress_track};
        }}

        div[data-testid="stProgress"] div[role="progressbar"] {{
            background-color: {primary};
            border-radius: 8px;
        }}

        div[data-testid="stProgress"] div[role="progressbar"] > div {{
            background-color: {secondary};
        }}

        .stSlider > div {{
            font-size: 1.05rem !important;
        }}

        .stSlider [role="slider"] {{
            background-color: {slider_handle} !important;
            box-shadow: none !important;
        }}

        .stSlider > div > div > div {{
            background: linear-gradient(90deg, {slider_track}, {primary});
        }}

        .stSelectbox > div > div {{
            background-color: {card};
            color: {text};
        }}

        .theme-switcher {{
            background-color: {card};
            border: 1px solid {notice_border};
            border-radius: 12px;
            padding: 0.75rem 1rem;
            margin-bottom: 1.5rem;
        }}

        .theme-switcher label {{
            color: {text};
            font-size: 0.95rem;
            font-weight: 600;
        }}

        .theme-switcher .stSlider > div > div {{
            background-color: transparent;
        }}

        .stButton > button {{
            background: {primary};
            color: {card};
            border: none;
            border-radius: 999px;
            padding: 0.6rem 1.5rem;
            font-weight: 600;
            box-shadow: 0 8px 18px rgba(0,0,0,0.12);
        }}

        .stButton > button:hover {{
            background: {accent};
        }}

        .stRadio > div, .stSelectbox > div, .stTextInput > div {{
            color: {text};
        }}

        .nav-button {{
            display: flex;
            width: 100%;
        }}

        .nav-button-left {{
            justify-content: flex-start;
        }}

        .nav-button-right {{
            justify-content: flex-end;
        }}

        .nav-button .stButton {{
            margin: 0;
        }}
    </style>
    """

    st.markdown(css_template.format(**palette), unsafe_allow_html=True)


def render_message(text, variant="neutral", container=None):
    css_class = MESSAGE_VARIANTS.get(variant, MESSAGE_VARIANTS['neutral'])
    html = f'<div class="{css_class}">{escape(str(text))}</div>'
    if container is not None:
        container.markdown(html, unsafe_allow_html=True)
    else:
        st.markdown(html, unsafe_allow_html=True)

# Linguistic features for ranking with explanations
LINGUISTIC_FEATURES = []

# Explanations for linguistic features
FEATURE_EXPLANATIONS = {
    "Rate of speech": "How fast or slow the speaker talks",
    "Tone": "The attitude or feeling in the speaker's voice (friendly, serious, confident, etc.)",
    "Inflection": "How the voice goes up and down within words",
    "Intonation": "The overall melody and flow of the speech",
    "Stress": "Which words or parts the speaker emphasizes to make them stand out"
}

for i in FEATURE_EXPLANATIONS.keys():
    temp = ''
    temp = temp + i + " - " + FEATURE_EXPLANATIONS[i]
    LINGUISTIC_FEATURES.append(temp)

# Follow-up questions based on most influential feature
FOLLOW_UP_QUESTIONS = {
    "Rate of speech": [
        {
            "id": "pace_assessment",
            "text": "Did you find the rate of speech to be natural?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Too slow",
                2: "Slightly slow",
                3: "Just right",
                4: "Slightly fast",
                5: "Too fast"
            }
        },
        {
            "id": "urgency_perception",
            "text": "Did the speed make the news sound urgent?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Very calm",
                2: "Somewhat calm",
                3: "Neutral",
                4: "Somewhat urgent",
                5: "Very urgent"
            }
        }
    ],
    "Tone": [
        {
            "id": "tone_formality",
            "text": "How formal did the speaker sound?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Very casual",
                2: "Somewhat casual",
                3: "Moderately formal",
                4: "Quite formal",
                5: "Very formal"
            }
        },
        {
            "id": "tone_confidence",
            "text": "How confident did the speaker sound?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Not confident",
                2: "Slightly confident",
                3: "Moderately confident",
                4: "Very confident",
                5: "Extremely confident"
            }
        }
    ],
    "Inflection": [
        {
            "id": "inflection_naturalness",
            "text": "Did the voice changes sound natural?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Very artificial",
                2: "Somewhat artificial",
                3: "Neutral",
                4: "Somewhat natural",
                5: "Very natural"
            }
        },
        {
            "id": "inflection_understanding",
            "text": "Does the inflection affect your ability to understand the speech?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Much harder",
                2: "Slightly harder",
                3: "No difference",
                4: "Slightly easier",
                5: "Much easier"
            }
        }
    ],
    "Intonation": [
        {
            "id": "intonation_variety",
            "text": "How much did the melodic pattern of the voice change?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Very flat",
                2: "Mostly flat",
                3: "Moderate variety",
                4: "Quite varied",
                5: "Very varied"
            }
        },
        {
            "id": "emotional_impact",
            "text": "How did the melodic pattern affect the way you felt?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Strongly negative",
                2: "Slightly negative",
                3: "Neutral",
                4: "Slightly positive",
                5: "Strongly positive"
            }
        }
    ],
    "Stress": [
        {
            "id": "stress_appropriateness",
            "text": "Were the right words emphasized?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Wrong emphasis",
                2: "Mostly wrong",
                3: "Mixed",
                4: "Mostly right",
                5: "Exactly right"
            }
        },
        {
            "id": "stress_comprehension",
            "text": "Did the emphasized words help you understand?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "value_labels": {
                1: "Much harder",
                2: "Slightly harder",
                3: "No difference",
                4: "Slightly easier",
                5: "Much easier"
            }
        }
    ]
}


def create_slider_format_func(value_labels):
    """Generate a format function that shows a tooltip for every slider value."""
    value_labels = value_labels or {}

    def _format(option):
        label = value_labels.get(option)
        return f"{option} - {label}" if label else str(option)

    return _format


def normalize_feature_key(text):
    """Normalize feature text to a lowercase underscore key."""
    return text.strip().lower().replace(" ", "_")

def filter_speed_duplicates(file_list):
    """Filter out speed duplicates, keeping only one version (normal or spedup)"""
    # Group files by base name (without _spedup suffix)
    file_groups = {}
    
    for file_path in file_list:
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        # Remove _spedup suffix to get base name
        if name_without_ext.endswith('_spedup'):
            base_name = name_without_ext[:-7]  # Remove '_spedup'
        else:
            base_name = name_without_ext
        
        # Store both versions if they exist
        if base_name not in file_groups:
            file_groups[base_name] = []
        file_groups[base_name].append(file_path)
    
    # For each group, randomly pick one version
    selected_files = []
    for base_name, versions in file_groups.items():
        selected_files.append(random.choice(versions))
    
    return selected_files

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
    
    # Filter out speed duplicates from general files
    general_files = filter_speed_duplicates(general_files)
    
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
                # Filter out speed duplicates from language-specific files
                language_specific[item.lower()] = filter_speed_duplicates(language_files)
    
    return {"general": general_files, "language_specific": language_specific}

def create_audio_clip_dict(file_path, clip_number):
    """Create a standardized audio clip dictionary"""
    # Use simple numbered title instead of filename
    title = f"Audio Clip {clip_number}"

    return {
        "file": file_path,
        "file_name": os.path.basename(file_path),
        "title": title,
        "questions": [
            {
                "id": "attitude",
                "text": "Did the reporter have an appropriate attitude while reporting?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5],
                "value_labels": {
                    1: "Not appropriate at all",
                    2: "Somewhat inappropriate",
                    3: "Neutral",
                    4: "Somewhat appropriate",
                    5: "Very appropriate"
                }
            },
            {
                "id": "naturalness",
                "text": "How natural does the speech sound?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5],
                "value_labels": {
                    1: "Very unnatural",
                    2: "Somewhat unnatural",
                    3: "Neutral",
                    4: "Somewhat natural",
                    5: "Very natural"
                }
            },
            {
                "id": "trustworthiness",
                "text": "How trustworthy/credible does it seem?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5],
                "value_labels": {
                    1: "Not trustworthy at all",
                    2: "Slightly trustworthy",
                    3: "Moderately trustworthy",
                    4: "Very trustworthy",
                    5: "Extremely trustworthy"
                }
            }
        ]
    }

def get_participant_audio_clips(mother_tongue=None, language_competence=None):
    """Get randomized audio clips for a participant based on their language competence or mother tongue"""
    all_files = get_all_audio_files()
    selected_clips = {}
    clip_counter = 1
    
    # Select N random general clips with balanced news_clip/news_real distribution
    general_files = all_files["general"]
    if len(general_files) > 0:
        n_clips = min(N_RANDOM_CLIPS, len(general_files))

        news_clip_pool = [f for f in general_files if os.path.basename(f).lower().startswith("news_clip_")]
        news_real_pool = [f for f in general_files if os.path.basename(f).lower().startswith("news_real_")]
        categorized_files = set(news_clip_pool + news_real_pool)
        other_general_pool = [f for f in general_files if f not in categorized_files]

        random.shuffle(news_clip_pool)
        random.shuffle(news_real_pool)
        random.shuffle(other_general_pool)

        clip_quota = n_clips // 2
        real_quota = n_clips - clip_quota
        if n_clips % 2 and len(news_clip_pool) > len(news_real_pool):
            clip_quota, real_quota = real_quota, clip_quota

        selected_general = []
        clip_selected_count = 0
        real_selected_count = 0

        clip_take = min(clip_quota, len(news_clip_pool))
        for _ in range(clip_take):
            selected_general.append(news_clip_pool.pop())
            clip_selected_count += 1

        real_take = min(real_quota, len(news_real_pool))
        for _ in range(real_take):
            selected_general.append(news_real_pool.pop())
            real_selected_count += 1

        remaining_slots = n_clips - len(selected_general)
        while remaining_slots > 0:
            if news_clip_pool and (clip_selected_count <= real_selected_count or not news_real_pool):
                selected_general.append(news_clip_pool.pop())
                clip_selected_count += 1
            elif news_real_pool:
                selected_general.append(news_real_pool.pop())
                real_selected_count += 1
            elif other_general_pool:
                selected_general.append(other_general_pool.pop())
            else:
                break
            remaining_slots -= 1

        random.shuffle(selected_general)

        for file_path in selected_general:
            clip_id = f"clip_{clip_counter}"
            selected_clips[clip_id] = create_audio_clip_dict(file_path, clip_counter)
            clip_counter += 1
    
    # Determine which language to use for language-specific clips
    # Priority: language_competence (if valid) > mother_tongue
    target_language = None
    if language_competence and language_competence not in ["Select a language", "None / Not applicable"]:
        target_language = language_competence
    elif mother_tongue:
        target_language = mother_tongue
    
    # If target language matches a subfolder, add M random clips from that language
    if target_language and target_language.lower() in all_files["language_specific"]:
        language_files = all_files["language_specific"][target_language.lower()]
        if len(language_files) > 0:
            m_clips = min(M_LANGUAGE_CLIPS, len(language_files))
            news_clip_pool = [f for f in language_files if os.path.basename(f).lower().startswith("news_clip_")]
            news_real_pool = [f for f in language_files if os.path.basename(f).lower().startswith("news_real_")]
            categorized_files = set(news_clip_pool + news_real_pool)
            other_lang_pool = [f for f in language_files if f not in categorized_files]

            random.shuffle(news_clip_pool)
            random.shuffle(news_real_pool)
            random.shuffle(other_lang_pool)

            clip_quota = m_clips // 2
            real_quota = m_clips - clip_quota
            if m_clips % 2 and len(news_clip_pool) > len(news_real_pool):
                clip_quota, real_quota = real_quota, clip_quota

            selected_language = []
            clip_selected_count = 0
            real_selected_count = 0

            clip_take = min(clip_quota, len(news_clip_pool))
            for _ in range(clip_take):
                selected_language.append(news_clip_pool.pop())
                clip_selected_count += 1

            real_take = min(real_quota, len(news_real_pool))
            for _ in range(real_take):
                selected_language.append(news_real_pool.pop())
                real_selected_count += 1

            remaining_slots = m_clips - len(selected_language)
            while remaining_slots > 0:
                if news_clip_pool and (clip_selected_count <= real_selected_count or not news_real_pool):
                    selected_language.append(news_clip_pool.pop())
                    clip_selected_count += 1
                elif news_real_pool:
                    selected_language.append(news_real_pool.pop())
                    real_selected_count += 1
                elif other_lang_pool:
                    selected_language.append(other_lang_pool.pop())
                else:
                    break
                remaining_slots -= 1

            random.shuffle(selected_language)

            for file_path in selected_language:
                clip_id = f"clip_{clip_counter}"
                selected_clips[clip_id] = create_audio_clip_dict(file_path, clip_counter)
                clip_counter += 1
    
    return selected_clips

# Don't load audio clips at module level anymore - they'll be loaded per participant
AUDIO_CLIPS = {}

def save_response(response_data):
    """Save response with Firebase priority and proper error handling."""
    payload = deepcopy(response_data)
    payload['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if 'responses' not in st.session_state:
        st.session_state.responses = []

    if firebase_service and firebase_service.is_available():
        try:
            if firebase_service.save_response(payload):
                st.session_state.responses.append(payload)
                return True
        except Exception:
            pass  # Fall back if Firebase write fails

    if CLOUD_STORAGE_AVAILABLE and "gcp_service_account" in st.secrets:
        project_id = st.secrets["gcp_service_account"].get("project_id", "")
        private_key = st.secrets["gcp_service_account"].get("private_key", "")

        if project_id and project_id != "your-project-id" and "BEGIN PRIVATE KEY" in private_key and "..." not in private_key:
            try:
                save_to_google_sheets(payload)
                st.session_state.responses.append(payload)
                return True
            except Exception:
                pass  # Fall back to local storage

    st.session_state.responses.append(payload)
    save_responses(st.session_state.responses)
    return True


def save_to_google_sheets(response_data):
    """Save response to Google Sheets."""
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scope)
    client = gspread.authorize(creds)

    sheet = client.open_by_key(st.secrets["google_sheets"]["spreadsheet_id"]).sheet1

    row = [
        response_data.get('timestamp', ''),
        response_data.get('participant_id', ''),
        response_data.get('age', ''),
        response_data.get('mother_tongue', ''),
        '',
        '',
        json.dumps(response_data)
    ]

    sheet.append_row(row)


def generate_participant_id():
    """Generate a unique participant identifier."""
    return f"P{uuid4().hex[:8].upper()}"


def ensure_slider_default(key, default):
    """Ensure a widget key has a default value in session state."""
    if key not in st.session_state:
        st.session_state[key] = default
    return st.session_state[key]


def render_standard_questions(clip_id, clip_data):
    """Render standard rating questions for a clip."""
    responses = {}
    missing = []

    for question in clip_data.get('questions', []):
        scale = question.get('scale', [])
        default_value = scale[len(scale) // 2] if scale else None
        slider_key = f"{clip_id}_{question['id']}"
        current_value = ensure_slider_default(slider_key, default_value)

        value = st.select_slider(
            question['text'],
            options=scale,
            key=slider_key,
            value=current_value,
            format_func=create_slider_format_func(question.get('value_labels', {}))
        )

        responses[question['id']] = value
        if value is None:
            missing.append(question['text'])

    return responses, missing


def create_drag_drop_ranking(clip_id):
    """Create drag and drop ranking interface using streamlit-sortables."""
    st.markdown("**Which of the following features do you think influenced your opinion the most?**")

    # st.markdown("**Linguistic Feature Definitions:**")
    # for feature in LINGUISTIC_FEATURES:
    #     explanation = FEATURE_EXPLANATIONS.get(feature)
    #     if explanation:
    #         st.markdown(f"• **{feature}**: {explanation}")

    # st.markdown("---")
    st.markdown("*Drag and drop to rearrange from most influential (top) to least influential (bottom):*")

    order_key = f"{clip_id}_ranking_order"
    initial_items = st.session_state.get(order_key, list(LINGUISTIC_FEATURES))

    try:
        sorted_items = sort_items(
            initial_items,
            direction="vertical",
            key=f"sortable_{clip_id}",
            multi_containers=False
        )
        st.session_state[order_key] = sorted_items

        # st.markdown("**Your Current Ranking:**")
        # for index, item in enumerate(sorted_items):
        #     st.markdown(f"**{index + 1}. {item}**")

        ranking_dict = {feature: idx + 1 for idx, feature in enumerate(sorted_items)}
        return ranking_dict, sorted_items[:2]

    except Exception:
        render_message("Drag-and-drop is temporarily unavailable. Please use the manual selectors.", variant="attention")
        st.markdown("**Using manual ranking instead:**")

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

        ranking_dict = {first_choice: 1, second_choice: 2}
        for idx, feature in enumerate(LINGUISTIC_FEATURES):
            if feature not in ranking_dict:
                ranking_dict[feature] = idx + 3

        st.session_state[order_key] = [first_choice, second_choice] + [f for f in LINGUISTIC_FEATURES if f not in {first_choice, second_choice}]
        return ranking_dict, [first_choice, second_choice]


def render_follow_up_questions(clip_id):
    """Render follow-up slider questions for each linguistic feature."""
    responses = {}
    missing = []

    for feature, questions in FOLLOW_UP_QUESTIONS.items():
        st.markdown(f"**{feature}**")
        # explanation = FEATURE_EXPLANATIONS.get(feature)
        # if explanation:
        #     st.markdown(f"*{explanation}*")

        feature_key = normalize_feature_key(feature)

        for question in questions:
            scale = question.get('scale', [])
            default_value = scale[len(scale) // 2] if scale else None
            slider_key = f"{clip_id}_{feature_key}_{question['id']}"
            current_value = ensure_slider_default(slider_key, default_value)

            value = st.select_slider(
                question['text'],
                options=scale,
                key=slider_key,
                value=current_value,
                format_func=create_slider_format_func(question.get('value_labels', {}))
            )

            responses[f"{feature_key}_{question['id']}"] = value
            if value is None:
                missing.append(f"{feature}: {question['text']}")

        # st.markdown("---")

    return responses, missing


def show_clip_page():
    """Render the full survey for the current clip on a single scrollable page."""
    participant_clips = st.session_state.participant_audio_clips

    if not participant_clips:
        render_message("No audio clips assigned. Please restart the survey.", variant="attention")
        return

    clip_ids = list(participant_clips.keys())
    current_index = st.session_state.current_clip
    current_clip_id = clip_ids[current_index]
    clip_data = participant_clips[current_clip_id]
    clip_name = clip_data.get('file_name') or os.path.basename(clip_data['file'])

    st.markdown(f'<div class="audio-section">', unsafe_allow_html=True)
    st.subheader(f"{clip_data['title']}")

    if os.path.exists(clip_data['file']):
        st.audio(clip_data['file'])
    else:
        render_message(f"Audio file not found: {clip_data['file']}", variant="attention")

    st.markdown("**Please listen to the audio clip above and answer the following questions:**")
    st.markdown('</div>', unsafe_allow_html=True)

    standard_responses, standard_missing = render_standard_questions(current_clip_id, clip_data)

    ## st.markdown("---")
    ranking_dict, top_features = create_drag_drop_ranking(current_clip_id)

    # render_message("You will be asked follow-up questions about each linguistic feature.")

    # st.markdown("---")
    st.markdown(f'<div class="follow-up-section">', unsafe_allow_html=True)
    # st.subheader("Follow-up Questions")
    # st.markdown("Please answer the following questions about each linguistic feature:")
    st.markdown('</div>', unsafe_allow_html=True)

    follow_up_responses, follow_up_missing = render_follow_up_questions(current_clip_id)

    error_placeholder = st.empty()

    action_col_left, action_col_spacer, action_col_right = st.columns([1, 0.2, 1])

    with action_col_left:
        st.markdown('<div class="nav-button nav-button-left">', unsafe_allow_html=True)
        previous_clicked = st.button("← Previous Clip", disabled=current_index == 0, key=f"prev_{current_clip_id}")
        st.markdown('</div>', unsafe_allow_html=True)

    with action_col_right:
        st.markdown('<div class="nav-button nav-button-right">', unsafe_allow_html=True)
        continue_clicked = st.button("Save and Continue →", type="primary", key=f"next_{current_clip_id}")
        st.markdown('</div>', unsafe_allow_html=True)

    if previous_clicked:
        if current_index > 0:
            st.session_state.scroll_to_top = True
            st.session_state.current_clip -= 1
            st.rerun()

    if continue_clicked:
        missing_fields = standard_missing + follow_up_missing
        if not ranking_dict:
            missing_fields.append("Feature ranking")
        if len(top_features) < 2:
            missing_fields.append("Top feature selection")

        if missing_fields:
            render_message("Please complete all questions before continuing.", variant="attention", container=error_placeholder)
        else:
            clip_payload = {}
            clip_payload.update(standard_responses)
            clip_payload.update(follow_up_responses)
            clip_payload['feature_ranking'] = ranking_dict
            clip_payload['top_features'] = top_features

            st.session_state.current_responses.setdefault('clips', {})
            st.session_state.current_responses['clips'][clip_name] = clip_payload

            if current_index < len(clip_ids) - 1:
                st.session_state.current_clip += 1
                st.session_state.scroll_to_top = True
                st.rerun()
            else:
                if save_response(st.session_state.current_responses):
                    st.session_state.survey_step = 'completed'
                    st.session_state.scroll_to_top = True
                    st.rerun()
                else:
                    render_message("Unable to save your responses. Please try again.", variant="attention", container=error_placeholder)


def show_participant_info():
    """Show participant information form."""
    st.header("Participant Information")

    language_choices = [
        "Select a language",
        "Malayalam",
        "Tamil",
        "Hindi",
        "None / Not applicable"
    ]

    with st.form("participant_form"):
        age = st.number_input("Age", value=18)
        mother_tongue = st.text_input("Mother tongue")
        competence_choice = st.selectbox(
            "If you are competent in Malayalam, Tamil, or Hindi, pick the one you know best (choose your mother tongue if listed). Otherwise select 'None / Not applicable'.",
            options=language_choices,
            index=0
        )

        submit = st.form_submit_button("Start Survey", type="primary")

    if submit:
        if not mother_tongue.strip():
            render_message("Please enter your mother tongue.", variant="attention")
            return

        if competence_choice == "Select a language":
            render_message("Please choose your level of competence among the listed languages.", variant="attention")
            return

        participant_clips = get_participant_audio_clips(
            mother_tongue=mother_tongue.strip(),
            language_competence=competence_choice
        )

        if not participant_clips:
            render_message("No audio files found. Please contact the administrator.", variant="attention")
            return

        participant_id = generate_participant_id()
        clip_sequence = [details.get('file_name') or os.path.basename(details['file']) for details in participant_clips.values()]

        st.session_state.participant_audio_clips = participant_clips
        st.session_state.current_responses = {
            'participant_id': participant_id,
            'age': int(age) if age else None,
            'mother_tongue': mother_tongue.strip(),
            'language_competence': competence_choice,
            'clip_sequence': clip_sequence,
            'clips': {}
        }
        st.session_state.current_clip = 0
        st.session_state.survey_step = 'clip_survey'
        st.rerun()


def show_completion_page():
    """Show survey completion page."""
    render_message("Survey completed successfully!", variant="success")
    st.markdown("Thank you for participating in our research on distinguishing between AI and human newscasters!")
    st.balloons()

    if st.button("Take Another Survey"):
        keys_to_clear = [
            key for key in list(st.session_state.keys())
            if key.startswith("clip_") or key.startswith("sortable_") or key.endswith("_ranking_order")
            or key.startswith("first_choice_") or key.startswith("second_choice_")
        ]
        for key in keys_to_clear:
            del st.session_state[key]

        st.session_state.survey_step = 'participant_info'
        st.session_state.current_clip = 0
        st.session_state.current_responses = {}
        st.session_state.participant_audio_clips = {}
        st.rerun()


def main():
    # if 'theme_choice' not in st.session_state:
    #     st.session_state.theme_choice = THEME_OPTIONS[0]

    # with st.container():
    #     st.markdown('<div class="theme-switcher">', unsafe_allow_html=True)
    #     theme_choice = st.select_slider(
    #         "Display theme",
    #         options=THEME_OPTIONS,
    #         value=st.session_state.theme_choice,
    #         key="theme_selector"
    #     )
    #     st.markdown('</div>', unsafe_allow_html=True)

    # if theme_choice != st.session_state.theme_choice:
    #     st.session_state.theme_choice = theme_choice
    # apply_theme(st.session_state.theme_choice)

    if st.session_state.get('scroll_to_top'):
        st.markdown(SCROLL_TO_TOP_SCRIPT, unsafe_allow_html=True)
        st.session_state.scroll_to_top = False

    st.markdown('<h1 class="main-header">Distinguishing between AI and Human Newscasters</h1>', unsafe_allow_html=True)
    st.markdown("**Research Study: How Linguistic Features Affect Perception of AI vs Human Speech**")

    all_files = get_all_audio_files()
    if not all_files["general"] and not all_files["language_specific"]:
        render_message("No audio files found in the 'audio' folder. Please add audio files (.mp3, .wav, .m4a, .ogg) to continue.", variant="attention")
        render_message("Expected audio folder location: audio/", variant="neutral")
        return

    if st.session_state.survey_step == 'clip_survey':
        participant_clips = st.session_state.participant_audio_clips
        if participant_clips:
            total_clips = len(participant_clips)
            progress = st.session_state.current_clip / total_clips if total_clips else 0
            st.progress(progress, text=f"Audio Clip {st.session_state.current_clip + 1} of {total_clips}")

    if st.session_state.survey_step == 'participant_info':
        show_participant_info()
    elif st.session_state.survey_step == 'clip_survey':
        show_clip_page()
    elif st.session_state.survey_step == 'completed':
        show_completion_page()


if __name__ == "__main__":
    main()