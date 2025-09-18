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
    page_icon="🎤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Data persistence file
DATA_FILE = "survey_responses.pkl"

def load_responses():
    """Load responses with cloud storage support"""
    # Try cloud storage first - but check for real credentials
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
    
    # Fallback to local storage
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
    """Save responses to persistent storage"""
    try:
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(responses, f)
    except Exception as e:
        pass  # Silently ignore save errors

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
            "text": "Was the speaking speed right for you?",
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
            "text": "Did the voice changes help you understand?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Made it harder", "No difference", "Made it easier"]
        }
    ],
    "Intonation": [
        {
            "id": "intonation_variety",
            "text": "How much did the voice melody change?",
            "type": "slider",
            "scale": [1, 2, 3, 4, 5],
            "labels": ["Very flat", "Normal", "Very varied"]
        },
        {
            "id": "emotional_impact",
            "text": "How did the voice melody make you feel?",
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

def get_audio_files():
    """Automatically detect audio files in the audio folder"""
    audio_folder = "audio"
    if not os.path.exists(audio_folder):
        return {}
    
    audio_extensions = ["*.mp3", "*.wav", "*.m4a", "*.ogg"]
    audio_files = {}
    
    for ext in audio_extensions:
        files = glob.glob(os.path.join(audio_folder, ext))
        for file_path in files:
            filename = os.path.basename(file_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            # Create a clean title from filename
            title = name_without_ext.replace("_", " ").replace("-", " ").title()
            
            clip_id = f"clip_{len(audio_files) + 1}"
            audio_files[clip_id] = {
                "file": file_path,
                "title": title,
                "questions": [
                    {
                        "id": f"attitude_{len(audio_files) + 1}",
                        "text": "Did the reporter have an appropriate attitude while reporting?",
                        "type": "scale",
                        "scale": [1, 2, 3, 4, 5],
                        "labels": ["Not appropriate at all", "Very appropriate"]
                    },
                    {
                        "id": f"naturalness_{len(audio_files) + 1}",
                        "text": "How natural does the speech sound?",
                        "type": "scale",
                        "scale": [1, 2, 3, 4, 5],
                        "labels": ["Very unnatural", "Very natural"]
                    },
                    {
                        "id": f"trustworthiness_{len(audio_files) + 1}",
                        "text": "How trustworthy/credible does it seem?",
                        "type": "scale",
                        "scale": [1, 2, 3, 4, 5],
                        "labels": ["Not trustworthy/credible at all", "Very trustworthy/credible"]
                    }
                ]
            }
    
    return audio_files

# Get audio clips dynamically
AUDIO_CLIPS = get_audio_files()

def save_response(response_data):
    """Save response with cloud storage support"""
    response_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Try cloud storage first (Google Sheets) - but check for real credentials
    if CLOUD_STORAGE_AVAILABLE and "gcp_service_account" in st.secrets:
        project_id = st.secrets["gcp_service_account"].get("project_id", "")
        private_key = st.secrets["gcp_service_account"].get("private_key", "")
        
        # Check if we have real credentials (not placeholders)
        if project_id and project_id != "your-project-id" and "BEGIN PRIVATE KEY" in private_key and "..." not in private_key:
            try:
                save_to_google_sheets(response_data)
                st.session_state.responses.append(response_data)
                return
            except Exception as e:
                pass  # Silently fall back to local storage
    
    # Fallback to local storage
    st.session_state.responses.append(response_data)
    save_responses(st.session_state.responses)

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

def display_results():
    """Display survey results with charts"""
    if not st.session_state.responses:
        st.info("No responses yet!")
        return
    
    df = pd.DataFrame(st.session_state.responses)
    
    st.subheader("AI vs Human Newscaster Study Results")
    
    # Display total responses
    st.metric("Total Responses", len(df))
    
    # Color scheme for charts (blue theme)
    color_palette = ['#4A90E2', '#64B5F6', '#1976D2', '#0D47A1', '#42A5F5']
    
    # Create charts for each audio clip
    for clip_id, clip_data in AUDIO_CLIPS.items():
        st.subheader(f"Results for {clip_data['title']}")
        
        col1, col2 = st.columns(2)
        
        # Get the clip number from clip_id
        clip_num = clip_id.replace('clip_', '')
        
        # Naturalness results
        naturalness_col = f"naturalness_{clip_num}"
        if naturalness_col in df.columns:
            with col1:
                st.write("**Speech Naturalness Ratings**")
                naturalness_counts = df[naturalness_col].value_counts().sort_index()
                fig1 = px.bar(x=naturalness_counts.index, y=naturalness_counts.values,
                             title="Speech Naturalness Distribution",
                             labels={'x': 'Rating', 'y': 'Count'},
                             color_discrete_sequence=[color_palette[0]])
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig1, use_container_width=True)
        
        # Trustworthiness results  
        trust_col = f"trustworthiness_{clip_num}"
        if trust_col in df.columns:
            with col2:
                st.write("**AI vs Human Perception Ratings**")
                trust_counts = df[trust_col].value_counts().sort_index()
                fig2 = px.bar(x=trust_counts.index, y=trust_counts.values,
                             title="AI vs Human Perception Distribution", 
                             labels={'x': 'Rating', 'y': 'Count'},
                             color_discrete_sequence=[color_palette[1]])
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        # Linguistic features ranking analysis
        st.write("**Linguistic Features Influence Ranking**")
        ranking_data = []
        
        for feature in LINGUISTIC_FEATURES:
            feature_key = f"{clip_id}_ranking_{feature.replace(' ', '_').lower()}"
            if feature_key in df.columns:
                avg_rank = df[feature_key].mean()
                ranking_data.append({"Feature": feature, "Average Rank": avg_rank})
        
        if ranking_data:
            rank_df = pd.DataFrame(ranking_data).sort_values("Average Rank")
            fig4 = px.bar(rank_df, x="Feature", y="Average Rank", 
                         title="Average Influence Ranking (Lower = More Influential)",
                         labels={'Average Rank': 'Average Rank (1=Most Influential)'},
                         color_discrete_sequence=[color_palette[3]])
            fig4.update_layout(
                xaxis_tickangle=-45,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig4, use_container_width=True)
        
        # Most influential feature summary
        if f"{clip_id}_most_influential" in df.columns:
            st.write("**Most Influential Feature Summary**")
            most_influential_counts = df[f"{clip_id}_most_influential"].value_counts()
            fig5 = px.pie(values=most_influential_counts.values, 
                         names=most_influential_counts.index,
                         title="Most Influential Linguistic Feature",
                         color_discrete_sequence=color_palette)
            fig5.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig5, use_container_width=True)
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Overall analysis across all clips
    st.subheader("Overall Analysis")
    
    # Native language distribution
    if 'mother_tongue' in df.columns:
        col1, col2 = st.columns(2)
        with col1:
            lang_counts = df['mother_tongue'].value_counts()
            fig_lang = px.pie(values=lang_counts.values, names=lang_counts.index,
                             title="Participant Mother Tongues",
                             color_discrete_sequence=color_palette)
            fig_lang.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_lang, use_container_width=True)
        
        with col2:
            if 'age' in df.columns:
                fig_age = px.histogram(df, x='age', nbins=10,
                               title="Age Distribution",
                               labels={'age': 'Age', 'count': 'Count'},
                               color_discrete_sequence=[color_palette[4]])
                fig_age.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig_age, use_container_width=True)
    
    # Raw data
    with st.expander("View Raw Data"):
        st.dataframe(df, use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">Distinguishing between AI and Human Newscasters</h1>', unsafe_allow_html=True)
    st.markdown("**Research Study: How Linguistic Features Affect Perception of AI vs Human Speech**")
    
    # Simple owner authentication
    owner_password = st.text_input("Owner password (optional - for viewing results)", type="password", key="owner_auth")
    is_owner = owner_password == "letmein"

    # Create tabs for survey and results
    if is_owner:
        tab1, tab2 = st.tabs(["Take Survey", "View Results"])
    else:
        tab1, = st.tabs(["Take Survey"])

    with tab1:
        if not AUDIO_CLIPS:
            st.error("No audio files found in the 'audio' folder. Please add audio files (.mp3, .wav, .m4a, .ogg) to continue.")
            st.info("Expected audio folder location: `audio/`")
            return
        
        # Progress indicator
        total_clips = len(AUDIO_CLIPS)
        if st.session_state.survey_step != 'participant_info' and st.session_state.survey_step != 'completed':
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

    if is_owner:
        with tab2:
            display_results()

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
                st.session_state.current_responses = {
                    'participant_id': f"participant_{len(st.session_state.responses)+1}",
                    'age': age,
                    'mother_tongue': mother_tongue.strip()
                }
                st.session_state.survey_step = 'audio_questions'
                st.session_state.current_clip = 0
                st.rerun()

def show_audio_questions():
    """Show audio questions for current clip"""
    clip_ids = list(AUDIO_CLIPS.keys())
    current_clip_id = clip_ids[st.session_state.current_clip]
    clip_data = AUDIO_CLIPS[current_clip_id]
    
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
    clip_ids = list(AUDIO_CLIPS.keys())
    current_clip_id = clip_ids[st.session_state.current_clip]
    
    st.subheader(f"Feature Ranking - {AUDIO_CLIPS[current_clip_id]['title']}")
    
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
    clip_ids = list(AUDIO_CLIPS.keys())
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
                if st.session_state.current_clip < len(AUDIO_CLIPS) - 1:
                    st.session_state.current_clip += 1
                    st.session_state.survey_step = 'audio_questions'
                else:
                    # Complete survey without final questions
                    save_response(st.session_state.current_responses)
                    st.session_state.survey_step = 'completed'
                st.rerun()

def show_final_questions():
    """Show final survey questions"""
    st.subheader("Final Questions")
    
    with st.form("final_questions_form"):
        comments = st.text_area(
            "Additional comments about the survey or audio clips (optional)"
        )
        
        overall_experience = st.slider(
            "How would you rate your overall experience with this survey?",
            min_value=1, max_value=7, value=None,
            help="1 = Very poor, 7 = Excellent"
        )
        
        if st.form_submit_button("Complete Survey", type="primary"):
            # Add final responses
            st.session_state.current_responses['comments'] = comments
            st.session_state.current_responses['overall_experience'] = overall_experience
            
            # Save the complete response
            save_response(st.session_state.current_responses)
            
            # Move to completion
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
        st.rerun()

if __name__ == "__main__":
    main()