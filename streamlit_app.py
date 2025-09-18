import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import json
import os
import glob
from streamlit_sortables import sort_items

# Set page configuration
st.set_page_config(
    page_title="News Audio Trustworthiness Survey",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Clean CSS for better styling
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
    
    .follow-up-section {
        background-color: #0F172A;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #F59E0B;
        margin: 1rem 0;
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
        {
            "id": "pace_assessment",
            "text": "Did you find the speaking pace:",
            "type": "radio",
            "options": ["Too fast", "Too slow", "Just right"]
        },
        {
            "id": "urgency_perception", 
            "text": "How did the speaking speed affect your perception of urgency?",
            "type": "text"
        }
    ],
    "Tone": [
        {
            "id": "tone_formality",
            "text": "Would you describe the tone as:",
            "type": "radio", 
            "options": ["Very formal", "Somewhat formal", "Neutral", "Somewhat casual", "Very casual"]
        },
        {
            "id": "tone_confidence",
            "text": "Did the tone convey confidence or uncertainty to you?",
            "type": "radio",
            "options": ["Very confident", "Confident", "Neutral", "Uncertain", "Very uncertain"]
        }
    ],
    "Inflection": [
        {
            "id": "inflection_naturalness",
            "text": "Did the speaker's inflection sound:",
            "type": "radio",
            "options": ["Very natural", "Somewhat natural", "Neutral", "Somewhat forced", "Very forced"]
        },
        {
            "id": "inflection_understanding",
            "text": "How did the inflection patterns affect your understanding?",
            "type": "text"
        }
    ],
    "Intonation": [
        {
            "id": "intonation_variety",
            "text": "Did the intonation sound:",
            "type": "radio",
            "options": ["Very monotonous", "Somewhat monotonous", "Neutral", "Somewhat varied", "Very varied"]
        },
        {
            "id": "emotional_impact",
            "text": "How did the intonation affect the emotional impact of the message?",
            "type": "text"
        }
    ],
    "Stress": [
        {
            "id": "stress_appropriateness",
            "text": "Were the emphasized words appropriate for the content?",
            "type": "radio",
            "options": ["Very appropriate", "Appropriate", "Neutral", "Inappropriate", "Very inappropriate"]
        },
        {
            "id": "stress_comprehension",
            "text": "Did the stress patterns help or hinder comprehension?",
            "type": "radio", 
            "options": ["Helped a lot", "Helped somewhat", "No effect", "Hindered somewhat", "Hindered a lot"]
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

if 'survey_step' not in st.session_state:
    st.session_state.survey_step = 'participant_info'

if 'current_clip' not in st.session_state:
    st.session_state.current_clip = 0

if 'current_responses' not in st.session_state:
    st.session_state.current_responses = {}

if 'ranking_complete' not in st.session_state:
    st.session_state.ranking_complete = {}

def save_response(response_data):
    """Save response to session state"""
    response_data['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.session_state.responses.append(response_data)

def create_drag_drop_ranking(clip_id):
    """Create drag and drop ranking interface using streamlit-sortables"""
    st.markdown("**Which of the following features do you think influenced your opinion the most?**")
    st.markdown("*Drag and drop to rearrange from most influential (top) to least influential (bottom):*")
    
    # Use streamlit-sortables for drag and drop
    try:
        sorted_items = sort_items(
            LINGUISTIC_FEATURES,
            direction="vertical",
            key=f"sortable_{clip_id}",
            multi_containers=False
        )
        
        # Display current ranking with emphasis on top 2
        st.markdown("**Your Current Ranking:**")
        for i, item in enumerate(sorted_items):
            if i < 2:
                st.markdown(f"🏆 **{i+1}. {item}** *(will get follow-up questions)*")
            else:
                st.markdown(f"{i+1}. {item}")
        
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
    
    # Owner authentication for results
    st.sidebar.header("🔒 Owner Access")
    owner_password = st.sidebar.text_input("Enter owner password to view results", type="password")
    is_owner = owner_password == "letmein"

    # Create tabs for survey and results
    if is_owner:
        tab1, tab2 = st.tabs(["📝 Take Survey", "📊 View Results"])
    else:
        tab1, = st.tabs(["📝 Take Survey"])

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
        elif st.session_state.survey_step == 'final_questions':
            show_final_questions()
        elif st.session_state.survey_step == 'completed':
            show_completion_page()

    if is_owner:
        with tab2:
            display_results()

def show_participant_info():
    """Show participant information form"""
    st.header("👤 Participant Information")
    
    with st.form("participant_form"):
        participant_id = st.text_input("Participant ID (optional)", placeholder="Enter a unique identifier")
        age = st.number_input("Age", min_value=18, max_value=100, value=25)
        native_language = st.selectbox("Native Language", 
                                     ["English", "Spanish", "French", "German", "Chinese", "Other"])
        overall_familiarity = st.slider(
            "How familiar are you with news media analysis?",
            min_value=1, max_value=7, value=4,
            help="1 = Not familiar at all, 7 = Very familiar"
        )
        
        if st.form_submit_button("Start Survey", type="primary"):
            st.session_state.current_responses = {
                'participant_id': participant_id if participant_id else f"anon_{len(st.session_state.responses)+1}",
                'age': age,
                'native_language': native_language,
                'overall_familiarity': overall_familiarity
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
    st.subheader(f"🎵 {clip_data['title']}")
    
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
    
    st.subheader(f"🎯 Feature Ranking - {AUDIO_CLIPS[current_clip_id]['title']}")
    
    # Create the drag-drop interface
    ranking_dict, top_2_features = create_drag_drop_ranking(current_clip_id)
    
    st.info("📋 You will be asked follow-up questions about your **top 2** most influential features.")
    
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
    """Show follow-up questions based on top 2 most influential features"""
    clip_ids = list(AUDIO_CLIPS.keys())
    current_clip_id = clip_ids[st.session_state.current_clip]
    top_features = st.session_state.current_responses.get(f"{current_clip_id}_top_features", [])
    
    if top_features and len(top_features) >= 2:
        st.markdown(f'<div class="follow-up-section">', unsafe_allow_html=True)
        st.subheader(f"📋 Follow-up Questions")
        st.markdown(f"You ranked **{top_features[0]}** and **{top_features[1]}** as your most influential features. Please answer these specific questions:")
        st.markdown('</div>', unsafe_allow_html=True)
        
        with st.form(f"followup_form_{current_clip_id}"):
            follow_up_responses = {}
            
            # Questions for first most influential feature
            if top_features[0] in FOLLOW_UP_QUESTIONS:
                st.markdown(f"### Questions about **{top_features[0]}** (Most Influential)")
                for question in FOLLOW_UP_QUESTIONS[top_features[0]]:
                    if question['type'] == 'radio':
                        response = st.radio(
                            question['text'],
                            options=question['options'],
                            key=f"{current_clip_id}_followup_1st_{question['id']}"
                        )
                    elif question['type'] == 'text':
                        response = st.text_area(
                            question['text'],
                            key=f"{current_clip_id}_followup_1st_{question['id']}",
                            placeholder="Please share your thoughts..."
                        )
                    
                    follow_up_responses[f"{current_clip_id}_followup_1st_{question['id']}"] = response
            
            st.markdown("---")
            
            # Questions for second most influential feature
            if top_features[1] in FOLLOW_UP_QUESTIONS:
                st.markdown(f"### Questions about **{top_features[1]}** (Second Most Influential)")
                for question in FOLLOW_UP_QUESTIONS[top_features[1]]:
                    if question['type'] == 'radio':
                        response = st.radio(
                            question['text'],
                            options=question['options'],
                            key=f"{current_clip_id}_followup_2nd_{question['id']}"
                        )
                    elif question['type'] == 'text':
                        response = st.text_area(
                            question['text'],
                            key=f"{current_clip_id}_followup_2nd_{question['id']}",
                            placeholder="Please share your thoughts..."
                        )
                    
                    follow_up_responses[f"{current_clip_id}_followup_2nd_{question['id']}"] = response
            
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
                        # Add final questions
                        st.session_state.survey_step = 'final_questions'
                    st.rerun()
    else:
        # Skip to next clip if no follow-up questions
        if st.session_state.current_clip < len(AUDIO_CLIPS) - 1:
            st.session_state.current_clip += 1
            st.session_state.survey_step = 'audio_questions'
        else:
            st.session_state.survey_step = 'final_questions'
        st.rerun()

def show_final_questions():
    """Show final survey questions"""
    st.subheader("📝 Final Questions")
    
    with st.form("final_questions_form"):
        comments = st.text_area(
            "Additional comments about the survey or audio clips (optional)",
            placeholder="Any observations about linguistic features, audio quality, etc."
        )
        
        overall_experience = st.slider(
            "How would you rate your overall experience with this survey?",
            min_value=1, max_value=7, value=4,
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
    st.success("🎉 Survey Completed Successfully!")
    st.markdown("Thank you for participating in our research on news audio trustworthiness!")
    st.balloons()
    
    if st.button("Take Another Survey"):
        # Reset session state
        st.session_state.survey_step = 'participant_info'
        st.session_state.current_clip = 0
        st.session_state.current_responses = {}
        st.rerun()
    
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