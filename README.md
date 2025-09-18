# �️ News Audio Trustworthiness Survey

A Streamlit application for conducting research on how linguistic features affect the perceived trustworthiness of news audio clips.

## 📊 Survey Features

- **Multiple Audio Clips**: Participants listen to different news reports
- **Trustworthiness Assessment**: Rate trustworthiness, clarity, and credibility
- **Research Focus**: Study linguistic features that influence trust perception
- **Owner-Only Results**: Secure access to survey results and analytics

## 🚀 How to run it

### Prerequisites
- Python 3.7+
- Audio files in MP3 or WAV format

### Setup Instructions

1. **Install the requirements**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add your audio files**
   Place your news audio clips in the `audio/` folder:
   - `audio/news_clip_1.mp3`
   - `audio/news_clip_2.mp3` 
   - `audio/news_clip_3.mp3`

3. **Run the app**
   ```bash
   streamlit run streamlit_app.py
   ```

## 🔒 Owner Access
- Use the sidebar password to access survey results
- Default password: `letmein` (change in code as needed)

## 📈 Survey Data
- Responses are stored in session state
- Export results as CSV
- Visual analytics for each audio clip
