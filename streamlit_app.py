import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import json

# Set page configuration
st.set_page_config(
    page_title="Survey & Poll App",
    page_icon="📊",
    layout="wide"
)

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
    
    st.subheader("📈 Survey Results")
    
    # Display total responses
    st.metric("Total Responses", len(df))
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Favorite programming language chart
        if 'favorite_language' in df.columns:
            st.subheader("Favorite Programming Language")
            lang_counts = df['favorite_language'].value_counts()
            fig1 = px.pie(values=lang_counts.values, names=lang_counts.index, 
                         title="Programming Language Preferences")
            st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        # Experience level chart
        if 'experience_level' in df.columns:
            st.subheader("Experience Level Distribution")
            exp_counts = df['experience_level'].value_counts()
            fig2 = px.bar(x=exp_counts.index, y=exp_counts.values,
                         title="Experience Level Distribution",
                         labels={'x': 'Experience Level', 'y': 'Count'})
            st.plotly_chart(fig2, use_container_width=True)
    
    # Rating distribution
    if 'satisfaction_rating' in df.columns:
        st.subheader("Satisfaction Rating Distribution")
        rating_counts = df['satisfaction_rating'].value_counts().sort_index()
        fig3 = px.histogram(df, x='satisfaction_rating', nbins=10,
                           title="Satisfaction Rating Distribution",
                           labels={'satisfaction_rating': 'Rating (1-10)', 'count': 'Frequency'})
        st.plotly_chart(fig3, use_container_width=True)
    
    # Raw data
    with st.expander("View Raw Data"):
        st.dataframe(df)

def main():
    st.title("📊 Survey & Poll Application")
    st.markdown("Welcome to our interactive survey! Please fill out the form below.")
    
    # Owner authentication for results
    st.sidebar.header("🔒 Owner Access")
    owner_password = st.sidebar.text_input("Enter owner password to view results", type="password")
    is_owner = owner_password == "letmein"  # Change this password as needed

    # Audio file upload (owner only)
    st.sidebar.header("🎵 Audio for Poll Question")
    if is_owner:
        audio_file = st.sidebar.file_uploader("Upload an audio file (mp3, wav)", type=["mp3", "wav"])
        if audio_file:
            st.session_state.poll_audio = audio_file.read()
            st.session_state.poll_audio_type = audio_file.type
    # If not owner, use previous audio if available
    poll_audio = st.session_state.get("poll_audio", None)
    poll_audio_type = st.session_state.get("poll_audio_type", None)

    # Create tabs for survey and results
    tab1, tab2 = st.tabs(["📝 Take Survey", "📊 View Results"])

    with tab1:
        st.header("Survey Form")

        # Embed audio in the question if available
        if poll_audio and poll_audio_type:
            st.audio(poll_audio, format=poll_audio_type)
            st.markdown("**Listen to the audio and answer the question below:**")

        with st.form("survey_form"):
            # Personal Information
            st.subheader("👤 Personal Information")
            name = st.text_input("Name (optional)")
            age = st.number_input("Age", min_value=13, max_value=100, value=25)
            

            # Multiple choice question (now with audio context)
            st.subheader("💻 Poll Question")
            favorite_language = st.selectbox(
                "What's your answer to the audio question? (Choose one)",
                ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "Other"]
            )
            
            # Radio buttons
            experience_level = st.radio(
                "What's your programming experience level?",
                ["Beginner (0-1 years)", "Intermediate (2-5 years)", 
                 "Advanced (5+ years)", "Expert (10+ years)"]
            )
            
            # Checkboxes for multiple selections
            st.subheader("🛠️ Technologies Used")
            technologies = st.multiselect(
                "Which technologies do you use? (Select all that apply)",
                ["React", "Vue.js", "Angular", "Django", "Flask", "FastAPI", 
                 "Node.js", "Express", "Docker", "Kubernetes", "AWS", "Azure"]
            )
            
            # Slider for rating
            satisfaction_rating = st.slider(
                "Rate your satisfaction with current tools (1-10)",
                min_value=1, max_value=10, value=7
            )
            
            # Text area for feedback
            st.subheader("💭 Feedback")
            feedback = st.text_area(
                "Any additional comments or suggestions?",
                placeholder="Share your thoughts here..."
            )
            
            # Yes/No question
            newsletter = st.checkbox("Would you like to subscribe to our newsletter?")
            
            # Submit button
            submitted = st.form_submit_button("Submit Survey", type="primary")
            
            if submitted:
                # Collect all form data
                response_data = {
                    'name': name if name else "Anonymous",
                    'age': age,
                    'favorite_language': favorite_language,
                    'experience_level': experience_level,
                    'technologies': ', '.join(technologies) if technologies else "None",
                    'satisfaction_rating': satisfaction_rating,
                    'feedback': feedback,
                    'newsletter_subscription': newsletter
                }
                
                # Save response
                save_response(response_data)
                st.success("Thank you for your response! 🎉")
                st.balloons()
    
    with tab2:
        if is_owner:
            display_results()
        else:
            st.warning("Results are restricted to the survey owner.")
    
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