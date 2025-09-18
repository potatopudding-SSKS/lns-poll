import pickle
import pandas as pd
import os
from datetime import datetime

def view_survey_data():
    """View and analyze survey response data"""
    DATA_FILE = "survey_responses.pkl"
    
    if not os.path.exists(DATA_FILE):
        print("❌ No survey data file found.")
        print("📝 Data will be created when the first survey response is submitted.")
        return
    
    try:
        # Load the data
        with open(DATA_FILE, 'rb') as f:
            responses = pickle.load(f)
        
        print(f"📊 SURVEY DATA OVERVIEW")
        print("=" * 50)
        print(f"📁 File location: {os.path.abspath(DATA_FILE)}")
        print(f"📝 Total responses: {len(responses)}")
        print(f"💾 File size: {os.path.getsize(DATA_FILE)} bytes")
        print()
        
        if not responses:
            print("📋 No responses recorded yet.")
            return
        
        # Convert to DataFrame for better analysis
        df = pd.DataFrame(responses)
        
        print("🔍 DATA STRUCTURE:")
        print(f"   • Participant info: age, mother_tongue, participant_id, timestamp")
        print(f"   • Audio ratings: naturalness_X, trustworthiness_X")
        print(f"   • Feature rankings: clip_X_ranking_[feature]")
        print(f"   • Follow-up responses: clip_X_followup_[feature]_[question]")
        print()
        
        print("👥 PARTICIPANT SUMMARY:")
        print(f"   • Age range: {df['age'].min()}-{df['age'].max()} years")
        print(f"   • Average age: {df['age'].mean():.1f} years")
        print(f"   • Languages: {', '.join(df['mother_tongue'].unique())}")
        print()
        
        print("⏰ RESPONSE TIMELINE:")
        df['date'] = pd.to_datetime(df['timestamp']).dt.date
        response_counts = df['date'].value_counts().sort_index()
        for date, count in response_counts.items():
            print(f"   • {date}: {count} response(s)")
        print()
        
        print("🎵 AUDIO RATINGS SUMMARY:")
        naturalness_cols = [col for col in df.columns if 'naturalness' in col]
        trustworthiness_cols = [col for col in df.columns if 'trustworthiness' in col]
        
        for col in naturalness_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                avg_rating = df[col].mean()
                print(f"   • {col}: {avg_rating:.1f}/5 average")
            
        for col in trustworthiness_cols:
            if pd.api.types.is_numeric_dtype(df[col]):
                avg_rating = df[col].mean()
                print(f"   • {col}: {avg_rating:.1f}/5 average")
        print()
        
        print("🏆 FEATURE RANKING SUMMARY:")
        ranking_cols = [col for col in df.columns if 'ranking' in col and not 'top_features' in col]
        
        # Calculate average rankings
        feature_rankings = {}
        for col in ranking_cols:
            feature_name = col.split('_ranking_')[-1].replace('_', ' ').title()
            if pd.api.types.is_numeric_dtype(df[col]):
                avg_rank = df[col].mean()
                feature_rankings[feature_name] = avg_rank
        
        # Sort by average rank (lower = more important)
        sorted_features = sorted(feature_rankings.items(), key=lambda x: x[1])
        
        print("   Most influential features (lower rank = more important):")
        for i, (feature, avg_rank) in enumerate(sorted_features, 1):
            print(f"   {i}. {feature}: {avg_rank:.1f} average rank")
        print()
        
        print("💾 DATA PERSISTENCE:")
        print(f"   • Local storage: {DATA_FILE}")
        print(f"   • Format: Python pickle (binary)")
        print(f"   • Automatic backup: No")
        print(f"   • Cloud sync: No (local only)")
        print()
        
        print("🔧 ADMIN ACCESS:")
        print(f"   • View data: Run admin.py")
        print(f"   • Export data: CSV/JSON available in admin portal")
        print(f"   • Clear data: Available in admin portal")
        
    except Exception as e:
        print(f"❌ Error loading data: {e}")

if __name__ == "__main__":
    view_survey_data()