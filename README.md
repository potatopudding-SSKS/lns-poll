# News Audio Trustworthiness Survey

A comprehensive Streamlit application for conducting research on how linguistic features affect the perception of trustworthiness in news audio clips.

## Features

### Main Survey Application (`streamlit_app.py`)
- **Multi-step survey flow**: Participant information → Audio evaluation → Feature ranking → Follow-up questions
- **Audio integration**: Automatic detection of audio files from the `audio/` folder
- **Dynamic scaling**: 1-5 point scales for naturalness and trustworthiness ratings
- **Drag-and-drop ranking**: Interactive ranking of linguistic features using streamlit-sortables
- **Persistent data storage**: Responses automatically saved to `survey_responses.pkl`
- **Professional styling**: Clean, dark theme optimized for academic research
- **Responsive design**: Works on desktop and mobile devices

### Admin Portal (`admin.py`)
- **Secure access**: Password-protected admin interface
- **Comprehensive analytics**: Overview, audio analysis, rankings, follow-up responses
- **Data visualization**: Interactive charts and graphs using Plotly
- **Export functionality**: Download data as CSV or JSON
- **Data management**: Clear all responses with confirmation
- **Real-time filtering**: Filter responses by date range

## Quick Start

### Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Setting Up Audio Files

1. Create an `audio/` folder in the project directory
2. Add your audio files (supported formats: MP3, WAV, M4A, OGG)
3. Audio files will be automatically detected and included in the survey

### Running the Applications

#### Local Development

**Main Survey**
```bash
streamlit run streamlit_app.py
```
Access at: http://localhost:8501

**Admin Portal**
```bash
streamlit run admin.py --server.port 8502
```
Access at: http://localhost:8502

**Default admin password**: `survey_admin_2024` (change this in `admin.py`)

#### Streamlit Cloud Deployment

When deploying to Streamlit Cloud, you'll need to deploy both applications separately:

**Main Survey Application**
1. Deploy `streamlit_app.py` as your main app
2. URL will be: `https://your-app-name.streamlit.app`

**Admin Portal Application**
1. Create a separate repository or branch for the admin portal
2. Set `admin.py` as the main file in your Streamlit Cloud app settings
3. Admin portal URL will be: `https://your-admin-app-name.streamlit.app`

**Important for Cloud Deployment:**
- Create separate Streamlit Cloud apps for survey and admin
- Ensure both apps have access to the same data storage (consider using a cloud database instead of local pickle files)
- Update the admin password before deploying to production
- Consider using Streamlit secrets for secure password management

## Survey Structure

### Step 1: Participant Information
- Age (numeric input)
- Mother tongue (text input)

### Step 2: Audio Evaluation
For each audio clip:
- Listen to audio clip
- Rate naturalness (1-5 scale)
- Rate trustworthiness/credibility (1-5 scale)

### Step 3: Feature Ranking
- Drag-and-drop ranking of linguistic features:
  - Rate of speech
  - Tone
  - Inflection
  - Intonation
  - Stress

### Step 4: Follow-up Questions
Detailed questions about each linguistic feature, including:
- Multiple choice questions about specific aspects
- Open-ended questions for qualitative feedback

## Data Storage

### Persistent Storage
- All responses automatically saved to `survey_responses.pkl`
- Data survives application restarts
- No database setup required

### Data Structure
Each response includes:
- Timestamp
- Participant demographics
- Audio clip ratings
- Feature rankings
- Follow-up question responses

## Admin Features

### Analytics Dashboard
- **Overview**: Response timeline, demographics, daily counts
- **Audio Analysis**: Average ratings per clip, rating distributions
- **Rankings**: Feature importance analysis, ranking frequency heatmaps
- **Follow-up Responses**: Qualitative response analysis
- **Raw Data**: Complete data export and management

### Data Export
- CSV format for statistical analysis
- JSON format for programmatic access
- Timestamped filenames for organization

## Customization

### Adding Audio Files
Simply add audio files to the `audio/` folder. The application will:
- Automatically detect new files
- Generate clean titles from filenames
- Create appropriate survey questions

### Modifying Questions
Edit the question structures in `streamlit_app.py`:
- Adjust rating scales
- Modify linguistic features list
- Update follow-up questions

### Changing Admin Password
In `admin.py`, modify the password check:
```python
if password == "your_new_password":
```

## Technical Requirements

- Python 3.7+
- Streamlit 1.28+
- Plotly 5.0+
- Pandas 2.0+
- streamlit-sortables

## Browser Compatibility

- Chrome (recommended)
- Firefox
- Safari
- Edge

## Security Notes

- Admin portal is password-protected
- No external data transmission
- All data stored locally
- Survey responses are anonymous

## Research Applications

This application is designed for:
- Academic research on speech perception
- News media trustworthiness studies
- Linguistic feature analysis
- Human-computer interaction research
- Audio quality assessment

## Support

For technical issues or feature requests, please check the documentation or create an issue in the repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.