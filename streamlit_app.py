import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json
import os

# Set page configuration
st.set_page_config(
    page_title="News Audio Trustworthiness Survey",
    page_icon="🎙️",
    layout="wide"
)

# Hardcoded audio clips and questions
AUDIO_CLIPS = {
    "clip1": {
        "file": "audio/news_clip_1.mp3",  # Place your audio files in an 'audio' folder
        "title": "News Report 1: Economic Update",
        "questions": [
            {
                "id": "trustworthiness_1",
                "text": "How trustworthy does this news report sound?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Not trustworthy at all", "Extremely trustworthy"]
            },
            {
                "id": "clarity_1", 
                "text": "How clear and understandable is the speaker?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Very unclear", "Very clear"]
            },
            {
                "id": "credibility_1",
                "text": "How credible does the information seem?",
                "type": "scale", 
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Not credible at all", "Extremely credible"]
            }
        ]
    },
    "clip2": {
        "file": "audio/news_clip_2.mp3",
        "title": "News Report 2: Weather Forecast",
        "questions": [
            {
                "id": "trustworthiness_2",
                "text": "How trustworthy does this news report sound?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Not trustworthy at all", "Extremely trustworthy"]
            },
            {
                "id": "clarity_2",
                "text": "How clear and understandable is the speaker?", 
                "type": "scale",
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Very unclear", "Very clear"]
            },
            {
                "id": "credibility_2",
                "text": "How credible does the information seem?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5, 6, 7], 
                "labels": ["Not credible at all", "Extremely credible"]
            }
        ]
    },
    "clip3": {
        "file": "audio/news_clip_3.mp3",
        "title": "News Report 3: Sports Update",
        "questions": [
            {
                "id": "trustworthiness_3",
                "text": "How trustworthy does this news report sound?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Not trustworthy at all", "Extremely trustworthy"]
            },
            {
                "id": "clarity_3",
                "text": "How clear and understandable is the speaker?",
                "type": "scale", 
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Very unclear", "Very clear"]
            },
            {
                "id": "credibility_3",
                "text": "How credible does the information seem?",
                "type": "scale",
                "scale": [1, 2, 3, 4, 5, 6, 7],
                "labels": ["Not credible at all", "Extremely credible"]
            }
        ]
    }
}

# Initialize session state for storing responses
if 'responses' not in st.session_state:
    st.session_state.responses = []

def save_response(response_data):
    """Save response to session state"""
    response_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.responses.append(response_data)

def display_results():
    """Display survey results with charts"""
    if not st.session_state.responses:
        st.info("No responses yet!")
        return
    
    df = pd.DataFrame(st.session_state.responses)
    
    st.subheader("📈 News Audio Trustworthiness Survey Results")
    
    # Display total responses
    st.metric("Total Responses", len(df))
    
    # Create charts for each audio clip
    for clip_id, clip_data in AUDIO_CLIPS.items():
        st.subheader(f"Results for {clip_data['title']}")
        
        col1, col2, col3 = st.columns(3)
        
        # Trustworthiness results
        trust_col = f"trustworthiness_{clip_id.replace('clip', '')}"
        if trust_col in df.columns:
            with col1:
                st.write("**Trustworthiness Ratings**")
                trust_counts = df[trust_col].value_counts().sort_index()
                fig1 = px.bar(x=trust_counts.index, y=trust_counts.values,
                             title="Trustworthiness Distribution",
                             labels={'x': 'Rating', 'y': 'Count'})
                st.plotly_chart(fig1, use_container_width=True)
        
        # Clarity results  
        clarity_col = f"clarity_{clip_id.replace('clip', '')}"
        if clarity_col in df.columns:
            with col2:
                st.write("**Clarity Ratings**")
                clarity_counts = df[clarity_col].value_counts().sort_index()
                fig2 = px.bar(x=clarity_counts.index, y=clarity_counts.values,
                             title="Clarity Distribution", 
                             labels={'x': 'Rating', 'y': 'Count'})
                st.plotly_chart(fig2, use_container_width=True)
        
        # Credibility results
        cred_col = f"credibility_{clip_id.replace('clip', '')}"
        if cred_col in df.columns:
            with col3:
                st.write("**Credibility Ratings**")
                cred_counts = df[cred_col].value_counts().sort_index()
                fig3 = px.bar(x=cred_counts.index, y=cred_counts.values,
                             title="Credibility Distribution",
                             labels={'x': 'Rating', 'y': 'Count'})
                st.plotly_chart(fig3, use_container_width=True)
        
        st.divider()
    
    # Raw data
    with st.expander("View Raw Data"):
        st.dataframe(df)

def main():
    st.title("🎙️ News Audio Trustworthiness Survey")
    st.markdown("**Research Study: How Linguistic Features Affect News Audio Trustworthiness**")
    st.markdown("Please listen to each audio clip carefully and answer the questions about your perception of trustworthiness.")
    
    # Owner authentication for results
    st.sidebar.header("🔒 Owner Access")
    owner_password = st.sidebar.text_input("Enter owner password to view results", type="password")
    is_owner = owner_password == "letmein"  # Change this password as needed

    # Create tabs for survey and results
    if is_owner:
        tab1, tab2 = st.tabs(["📝 Take Survey", "📊 View Results"])
    else:
        tab1, = st.tabs(["📝 Take Survey"])

    with tab1:
        st.header("Survey Form")
        
        with st.form("trustworthiness_survey"):
            # Participant information
            st.subheader("👤 Participant Information")
            participant_id = st.text_input("Participant ID (optional)", placeholder="Enter a unique identifier")
            age = st.number_input("Age", min_value=18, max_value=100, value=25)
            native_language = st.selectbox("Native Language", 
                                         ["English", "Spanish", "French", "German", "Chinese", "Other"])
            
            st.divider()
            
            # Collect responses for all audio clips
            responses = {}
            
            for clip_id, clip_data in AUDIO_CLIPS.items():
                st.subheader(f"🎵 {clip_data['title']}")
                
                # Try to display audio file if it exists
                if os.path.exists(clip_data['file']):
                    st.audio(clip_data['file'])
                else:
                    st.warning(f"Audio file not found: {clip_data['file']}")
                    st.info("Please place your audio files in the 'audio' folder with the correct names.")
                
                st.markdown("**Please listen to the audio clip above and answer the following questions:**")
                
                # Display questions for this clip
                for question in clip_data['questions']:
                    if question['type'] == 'scale':
                        response = st.select_slider(
                            question['text'],
                            options=question['scale'],
                            format_func=lambda x: f"{x} - {question['labels'][0] if x == 1 else question['labels'][1] if x == 7 else ''}",
                            key=f"{clip_id}_{question['id']}"
                        )
                        responses[question['id']] = response
                
                st.divider()
            
            # Additional questions
            st.subheader("📝 Additional Information")
            overall_familiarity = st.slider(
                "How familiar are you with news media analysis?",
                min_value=1, max_value=7, value=4,
                help="1 = Not familiar at all, 7 = Very familiar"
            )
            
            comments = st.text_area(
                "Additional comments about the survey or audio clips (optional)",
                placeholder="Any observations about linguistic features, audio quality, etc."
            )
            
            # Submit button
            submitted = st.form_submit_button("Submit Survey", type="primary")
            
            if submitted:
                # Collect all form data
                response_data = {
                    'participant_id': participant_id if participant_id else f"anon_{len(st.session_state.responses)+1}",
                    'age': age,
                    'native_language': native_language,
                    'overall_familiarity': overall_familiarity,
                    'comments': comments,
                    **responses  # Add all the audio clip responses
                }
                
                # Save response
                save_response(response_data)
                st.success("Thank you for participating in our research! 🎉")
                st.balloons()

    if is_owner:
        with tab2:
            display_results()
    
    # Sidebar with additional features
    st.sidebar.header("📋 Survey Controls")
    
    # Download results as CSV
    if st.session_state.responses:
        df = pd.DataFrame(st.session_state.responses)
        csv = df.to_csv(index=False)
        st.sidebar.download_button(
            label="Download Results as CSV",
            data=csv,
            file_name=f"survey_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    # Clear all responses
    if st.sidebar.button("Clear All Responses", type="secondary"):
        st.session_state.responses = []
        st.sidebar.success("All responses cleared!")
        st.rerun()
    
    # Display response count in sidebar
    st.sidebar.metric("Current Responses", len(st.session_state.responses))

if __name__ == "__main__":
    main()