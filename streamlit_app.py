import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import glob

# Set page configuration
st.set_page_config(
    page_title="News Audio Trustworthiness Survey",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better dark theme styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #64B5F6;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .audio-section {
        background-color: #1E1E1E;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #64B5F6;
        margin: 1rem 0;
    }
    
    .ranking-container {
        background-color: #2D2D2D;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #444;
        margin: 1rem 0;
    }
    
    .feature-item {
        background-color: #4A90E2;
        color: white;
        padding: 0.8rem;
        margin: 0.3rem 0;
        border-radius: 6px;
        text-align: center;
        font-weight: 500;
        border: 1px solid #357ABD;
    }
    
    .feature-item:hover {
        background-color: #357ABD;
        cursor: pointer;
    }
    
    .instructions {
        color: #B3B3B3;
        font-style: italic;
        margin-bottom: 1rem;
    }
    
    .section-divider {
        border-top: 2px solid #444;
        margin: 2rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Linguistic features for ranking
LINGUISTIC_FEATURES = [
    "Rate of speech",
    "Tone", 
    "Inflection",
    "Intonation",
    "Stress"
]

# Follow-up questions based on most influential feature
FOLLOW_UP_QUESTIONS = {
    "Rate of speech": [
        "Did you find the speaking pace too fast, too slow, or just right?",
        "How did the speaking speed affect your perception of urgency?"
    ],
    "Tone": [
        "Would you describe the tone as formal, casual, or somewhere in between?",
        "Did the tone convey confidence or uncertainty to you?"
    ],
    "Inflection": [
        "Did the speaker's inflection sound natural or forced?",
        "How did the inflection patterns affect your understanding?"
    ],
    "Intonation": [
        "Did the intonation sound monotonous or varied?",
        "How did the intonation affect the emotional impact of the message?"
    ],
    "Stress": [
        "Were the emphasized words appropriate for the content?",
        "Did the stress patterns help or hinder comprehension?"
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
                        "id": f"trustworthiness_{len(audio_files) + 1}",
                        "text": "How trustworthy does this news report sound?",
                        "type": "scale",
                        "scale": [1, 2, 3, 4, 5, 6, 7],
                        "labels": ["Not trustworthy at all", "Extremely trustworthy"]
                    },
                    {
                        "id": f"clarity_{len(audio_files) + 1}", 
                        "text": "How clear and understandable is the speaker?",
                        "type": "scale",
                        "scale": [1, 2, 3, 4, 5, 6, 7],
                        "labels": ["Very unclear", "Very clear"]
                    },
                    {
                        "id": f"credibility_{len(audio_files) + 1}",
                        "text": "How credible does the information seem?",
                        "type": "scale", 
                        "scale": [1, 2, 3, 4, 5, 6, 7],
                        "labels": ["Not credible at all", "Extremely credible"]
                    }
                ]
            }
    
    return audio_files

# Get audio clips dynamically
AUDIO_CLIPS = get_audio_files()

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
    
    # Color scheme for charts (blue theme)
    color_palette = ['#4A90E2', '#64B5F6', '#1976D2', '#0D47A1', '#42A5F5']
    
    # Create charts for each audio clip
    for clip_id, clip_data in AUDIO_CLIPS.items():
        st.subheader(f"Results for {clip_data['title']}")
        
        col1, col2, col3 = st.columns(3)
        
        # Get the clip number from clip_id
        clip_num = clip_id.replace('clip_', '')
        
        # Trustworthiness results
        trust_col = f"trustworthiness_{clip_num}"
        if trust_col in df.columns:
            with col1:
                st.write("**Trustworthiness Ratings**")
                trust_counts = df[trust_col].value_counts().sort_index()
                fig1 = px.bar(x=trust_counts.index, y=trust_counts.values,
                             title="Trustworthiness Distribution",
                             labels={'x': 'Rating', 'y': 'Count'},
                             color_discrete_sequence=[color_palette[0]])
                fig1.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig1, use_container_width=True)
        
        # Clarity results  
        clarity_col = f"clarity_{clip_num}"
        if clarity_col in df.columns:
            with col2:
                st.write("**Clarity Ratings**")
                clarity_counts = df[clarity_col].value_counts().sort_index()
                fig2 = px.bar(x=clarity_counts.index, y=clarity_counts.values,
                             title="Clarity Distribution", 
                             labels={'x': 'Rating', 'y': 'Count'},
                             color_discrete_sequence=[color_palette[1]])
                fig2.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig2, use_container_width=True)
        
        # Credibility results
        cred_col = f"credibility_{clip_num}"
        if cred_col in df.columns:
            with col3:
                st.write("**Credibility Ratings**")
                cred_counts = df[cred_col].value_counts().sort_index()
                fig3 = px.bar(x=cred_counts.index, y=cred_counts.values,
                             title="Credibility Distribution",
                             labels={'x': 'Rating', 'y': 'Count'},
                             color_discrete_sequence=[color_palette[2]])
                fig3.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig3, use_container_width=True)
        
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
    st.subheader("📊 Overall Analysis")
    
    # Native language distribution
    if 'native_language' in df.columns:
        col1, col2 = st.columns(2)
        with col1:
            lang_counts = df['native_language'].value_counts()
            fig_lang = px.pie(values=lang_counts.values, names=lang_counts.index,
                             title="Participant Native Languages",
                             color_discrete_sequence=color_palette)
            fig_lang.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='white'
            )
            st.plotly_chart(fig_lang, use_container_width=True)
        
        with col2:
            if 'overall_familiarity' in df.columns:
                fam_counts = df['overall_familiarity'].value_counts().sort_index()
                fig_fam = px.bar(x=fam_counts.index, y=fam_counts.values,
                               title="News Media Analysis Familiarity",
                               labels={'x': 'Familiarity Level', 'y': 'Count'},
                               color_discrete_sequence=[color_palette[4]])
                fig_fam.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='white'
                )
                st.plotly_chart(fig_fam, use_container_width=True)
    
    # Raw data
    with st.expander("View Raw Data"):
        st.dataframe(df, use_container_width=True)

def main():
    st.markdown('<h1 class="main-header">🎙️ News Audio Trustworthiness Survey</h1>', unsafe_allow_html=True)
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
        
        if not AUDIO_CLIPS:
            st.error("No audio files found in the 'audio' folder. Please add audio files (.mp3, .wav, .m4a, .ogg) to continue.")
            st.info("Expected audio folder location: `audio/`")
            return
        
        with st.form("trustworthiness_survey"):
            # Participant information
            st.subheader("👤 Participant Information")
            participant_id = st.text_input("Participant ID (optional)", placeholder="Enter a unique identifier")
            age = st.number_input("Age", min_value=18, max_value=100, value=25)
            native_language = st.selectbox("Native Language", 
                                         ["English", "Spanish", "French", "German", "Chinese", "Other"])
            
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # Collect responses for all audio clips
            responses = {}
            
            for clip_id, clip_data in AUDIO_CLIPS.items():
                st.markdown(f'<div class="audio-section">', unsafe_allow_html=True)
                st.subheader(f"🎵 {clip_data['title']}")
                
                # Display audio file
                if os.path.exists(clip_data['file']):
                    st.audio(clip_data['file'])
                else:
                    st.warning(f"Audio file not found: {clip_data['file']}")
                
                st.markdown("**Please listen to the audio clip above and answer the following questions:**")
                
                # Standard questions for this clip
                for question in clip_data['questions']:
                    if question['type'] == 'scale':
                        response = st.select_slider(
                            question['text'],
                            options=question['scale'],
                            format_func=lambda x, labels=question['labels']: f"{x} - {labels[0] if x == 1 else labels[1] if x == 7 else ''}",
                            key=f"{clip_id}_{question['id']}"
                        )
                        responses[question['id']] = response
                
                # Improved ranking question using select boxes
                st.markdown("**Which of the following features do you think influenced your opinion the most?**")
                st.markdown('<p class="instructions">Rank each feature from 1 (most influential) to 5 (least influential):</p>', unsafe_allow_html=True)
                
                st.markdown('<div class="ranking-container">', unsafe_allow_html=True)
                
                # Create ranking for each feature
                feature_rankings = {}
                cols = st.columns(len(LINGUISTIC_FEATURES))
                
                for idx, feature in enumerate(LINGUISTIC_FEATURES):
                    with cols[idx]:
                        st.markdown(f'<div class="feature-item">{feature}</div>', unsafe_allow_html=True)
                        ranking = st.selectbox(
                            f"Rank for {feature}",
                            options=[1, 2, 3, 4, 5],
                            key=f"{clip_id}_rank_{feature.replace(' ', '_').lower()}",
                            label_visibility="collapsed"
                        )
                        feature_rankings[feature] = ranking
                        responses[f"{clip_id}_ranking_{feature.replace(' ', '_').lower()}"] = ranking
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Find most influential feature (lowest ranking number)
                most_influential = min(feature_rankings, key=feature_rankings.get)
                responses[f"{clip_id}_most_influential"] = most_influential
                
                # Follow-up questions based on most influential feature
                if most_influential in FOLLOW_UP_QUESTIONS:
                    st.markdown(f"**Follow-up questions about {most_influential.lower()}:**")
                    
                    for idx, follow_up_q in enumerate(FOLLOW_UP_QUESTIONS[most_influential]):
                        follow_up_response = st.text_input(
                            follow_up_q,
                            key=f"{clip_id}_followup_{idx}",
                            placeholder="Please share your thoughts..."
                        )
                        responses[f"{clip_id}_followup_{most_influential.replace(' ', '_').lower()}_{idx}"] = follow_up_response
                
                st.markdown('</div>', unsafe_allow_html=True)
                st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
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
                # Validate that rankings are unique for each clip
                valid_submission = True
                for clip_id in AUDIO_CLIPS.keys():
                    clip_rankings = [responses[f"{clip_id}_ranking_{feature.replace(' ', '_').lower()}"] for feature in LINGUISTIC_FEATURES]
                    if len(set(clip_rankings)) != len(clip_rankings):
                        st.error(f"Please ensure each feature has a unique ranking for {AUDIO_CLIPS[clip_id]['title']}")
                        valid_submission = False
                        break
                
                if valid_submission:
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