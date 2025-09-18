import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pickle
import os

# Set page configuration
st.set_page_config(
    page_title="Survey Admin Portal",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Data persistence file
DATA_FILE = "survey_responses.pkl"

def load_responses():
    """Load responses from persistent storage"""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                return pickle.load(f)
        return []
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return []

def create_results_dashboard():
    """Create the dashboard for viewing survey results"""
    st.title("News Audio Trustworthiness Survey - Admin Portal")
    
    responses = load_responses()
    
    if not responses:
        st.warning("No survey responses found.")
        return
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame(responses)
    
    # Sidebar for filtering
    st.sidebar.header("Filter Options")
    
    # Date range filter
    if len(df) > 0:
        min_date = pd.to_datetime(df['timestamp']).dt.date.min()
        max_date = pd.to_datetime(df['timestamp']).dt.date.max()
        
        date_range = st.sidebar.date_input(
            "Select date range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        # Filter by date
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        if len(date_range) == 2:
            df = df[(df['date'] >= date_range[0]) & (df['date'] <= date_range[1])]
    
    # Display summary statistics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Responses", len(df))
    
    with col2:
        if len(df) > 0:
            avg_age = df['age'].mean() if 'age' in df.columns else 0
            st.metric("Average Age", f"{avg_age:.1f}")
        else:
            st.metric("Average Age", "N/A")
    
    with col3:
        if len(df) > 0:
            unique_languages = df['mother_tongue'].nunique() if 'mother_tongue' in df.columns else 0
            st.metric("Languages", unique_languages)
        else:
            st.metric("Languages", "N/A")
    
    with col4:
        if len(df) > 0:
            recent_responses = len(df[pd.to_datetime(df['timestamp']).dt.date == datetime.now().date()])
            st.metric("Today's Responses", recent_responses)
        else:
            st.metric("Today's Responses", "0")
    
    if len(df) == 0:
        st.info("No data available for the selected date range.")
        return
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Overview", "Audio Analysis", "Rankings", "Follow-up Responses", "Raw Data"])
    
    with tab1:
        st.header("Survey Overview")
        
        # Response timeline
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        daily_responses = df.groupby('date').size().reset_index(name='count')
        
        fig_timeline = px.line(daily_responses, x='date', y='count', 
                              title="Daily Response Count",
                              template="plotly_dark")
        fig_timeline.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Demographics
        col1, col2 = st.columns(2)
        
        with col1:
            if 'age' in df.columns:
                fig_age = px.histogram(df, x='age', nbins=10, 
                                     title="Age Distribution",
                                     template="plotly_dark")
                fig_age.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig_age, use_container_width=True)
        
        with col2:
            if 'mother_tongue' in df.columns:
                language_counts = df['mother_tongue'].value_counts()
                fig_lang = px.pie(values=language_counts.values, 
                                names=language_counts.index,
                                title="Mother Tongue Distribution",
                                template="plotly_dark")
                fig_lang.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig_lang, use_container_width=True)
    
    with tab2:
        st.header("Audio Clip Analysis")
        
        # Analyze ratings for each audio clip
        audio_data = []
        for _, row in df.iterrows():
            if 'audio_responses' in row:
                for clip_id, responses in row['audio_responses'].items():
                    for question_id, rating in responses.items():
                        if isinstance(rating, (int, float)):
                            question_type = "naturalness" if "naturalness" in question_id else "trustworthiness"
                            audio_data.append({
                                'clip_id': clip_id,
                                'question_type': question_type,
                                'rating': rating,
                                'participant_id': row.get('timestamp', 'unknown')
                            })
        
        if audio_data:
            audio_df = pd.DataFrame(audio_data)
            
            # Average ratings by clip and question type
            avg_ratings = audio_df.groupby(['clip_id', 'question_type'])['rating'].mean().reset_index()
            
            fig_ratings = px.bar(avg_ratings, x='clip_id', y='rating', color='question_type',
                               title="Average Ratings by Audio Clip",
                               template="plotly_dark",
                               barmode='group')
            fig_ratings.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                yaxis_range=[1, 5]
            )
            st.plotly_chart(fig_ratings, use_container_width=True)
            
            # Rating distribution
            fig_dist = px.histogram(audio_df, x='rating', color='question_type',
                                  title="Rating Distribution",
                                  template="plotly_dark",
                                  nbins=5)
            fig_dist.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_dist, use_container_width=True)
        else:
            st.info("No audio rating data available.")
    
    with tab3:
        st.header("Feature Rankings Analysis")
        
        # Analyze linguistic feature rankings
        ranking_data = []
        for _, row in df.iterrows():
            if 'feature_rankings' in row:
                for clip_id, rankings in row['feature_rankings'].items():
                    if isinstance(rankings, list):
                        for rank, feature in enumerate(rankings, 1):
                            ranking_data.append({
                                'clip_id': clip_id,
                                'feature': feature,
                                'rank': rank,
                                'participant_id': row.get('timestamp', 'unknown')
                            })
        
        if ranking_data:
            ranking_df = pd.DataFrame(ranking_data)
            
            # Average rank by feature
            avg_ranks = ranking_df.groupby('feature')['rank'].mean().sort_values()
            
            fig_ranks = px.bar(x=avg_ranks.values, y=avg_ranks.index,
                             orientation='h',
                             title="Average Ranking by Linguistic Feature (Lower = More Important)",
                             template="plotly_dark")
            fig_ranks.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis_title="Average Rank",
                yaxis_title="Linguistic Feature"
            )
            st.plotly_chart(fig_ranks, use_container_width=True)
            
            # Ranking frequency heatmap
            rank_counts = ranking_df.pivot_table(index='feature', columns='rank', 
                                                values='participant_id', aggfunc='count', fill_value=0)
            
            fig_heatmap = px.imshow(rank_counts.values,
                                  x=[f"Rank {i}" for i in rank_counts.columns],
                                  y=rank_counts.index,
                                  title="Feature Ranking Frequency",
                                  template="plotly_dark",
                                  color_continuous_scale="Blues")
            fig_heatmap.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
            )
            st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("No ranking data available.")
    
    with tab4:
        st.header("Follow-up Question Analysis")
        
        # Analyze follow-up responses
        followup_data = []
        for _, row in df.iterrows():
            if 'followup_responses' in row:
                for clip_id, responses in row['followup_responses'].items():
                    for question_id, answer in responses.items():
                        followup_data.append({
                            'clip_id': clip_id,
                            'question_id': question_id,
                            'answer': answer,
                            'participant_id': row.get('timestamp', 'unknown')
                        })
        
        if followup_data:
            followup_df = pd.DataFrame(followup_data)
            
            # Show sample responses
            st.subheader("Sample Follow-up Responses")
            
            # Group by question type
            question_types = followup_df['question_id'].str.split('_').str[0].unique()
            
            for q_type in question_types:
                if pd.notna(q_type):
                    st.write(f"**{q_type.title()} Questions:**")
                    q_data = followup_df[followup_df['question_id'].str.startswith(q_type)]
                    
                    # Show frequency of answers for radio button questions
                    if len(q_data) > 0:
                        answer_counts = q_data['answer'].value_counts().head(10)
                        if len(answer_counts) > 0:
                            st.write(answer_counts.to_dict())
                    st.write("---")
        else:
            st.info("No follow-up response data available.")
    
    with tab5:
        st.header("Raw Data Export")
        
        st.subheader("Download Options")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV file",
                    data=csv,
                    file_name=f"survey_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Download JSON"):
                json_data = df.to_json(orient='records', indent=2)
                st.download_button(
                    label="Download JSON file",
                    data=json_data,
                    file_name=f"survey_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        # Display raw data table
        st.subheader("Raw Response Data")
        st.dataframe(df, use_container_width=True)
        
        # Data management
        st.subheader("Data Management")
        
        if st.button("Clear All Data", type="secondary"):
            if st.checkbox("I understand this will permanently delete all survey responses"):
                try:
                    if os.path.exists(DATA_FILE):
                        os.remove(DATA_FILE)
                    st.success("All data has been cleared.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error clearing data: {e}")

def main():
    """Main admin portal function"""
    
    # Simple authentication
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.title("Admin Portal Login")
        
        password = st.text_input("Enter admin password:", type="password")
        
        if st.button("Login"):
            if password == "survey_admin_2024":  # Change this password as needed
                st.session_state.admin_authenticated = True
                st.success("Authentication successful!")
                st.rerun()
            else:
                st.error("Invalid password. Please try again.")
        
        st.info("This portal is for survey administrators only.")
        return
    
    # Logout button in sidebar
    if st.sidebar.button("Logout"):
        st.session_state.admin_authenticated = False
        st.rerun()
    
    # Main admin interface
    create_results_dashboard()

if __name__ == "__main__":
    main()