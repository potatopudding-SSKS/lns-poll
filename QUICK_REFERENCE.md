# Quick Reference Guide

## Configuration Settings

Located at the top of `streamlit_app.py`:

```python
N_RANDOM_CLIPS = 10  # General clips shown to all participants
M_LANGUAGE_CLIPS = 5  # Language-specific clips (if mother tongue matches)
```

## How to Change Clip Numbers

1. Open `streamlit_app.py`
2. Find lines 14-15 (near the top)
3. Change the numbers:
   ```python
   N_RANDOM_CLIPS = 15  # Example: increase to 15
   M_LANGUAGE_CLIPS = 3  # Example: decrease to 3
   ```
4. Save and restart the app

## Audio Folder Structure

```
audio/
├── general_clip1.mp3     ← N clips randomly selected from here
├── general_clip2.mp3
├── ...
├── english/              ← M clips randomly selected if mother tongue = "English"
│   ├── en_clip1.mp3
│   └── ...
├── spanish/              ← M clips randomly selected if mother tongue = "Spanish"
│   └── ...
└── mandarin/             ← M clips randomly selected if mother tongue = "Mandarin"
    └── ...
```

## Participant Flow

1. **Enter Info** → Age + Mother Tongue
2. **System Generates** → N random clips + M language clips (if match)
3. **For Each Clip**:
   - Listen to audio
   - Answer 3 rating questions
   - Rank 5 linguistic features
   - Answer 10 follow-up questions
4. **Complete** → Data saved to Firebase

## Data Storage

- Primary: Firebase Firestore
- Fallback: Local pickle file
- Each response includes all clip answers + participant info

## Common Tasks

### Add New Audio Files
1. Drop files into `audio/` folder
2. No restart needed - files are detected dynamically

### Add New Language Support
1. Create subfolder: `audio/french/`
2. Add audio files to that subfolder
3. Participants entering "French" will get those clips

### View Data
- Firebase Console → Firestore Database → `survey_responses` collection
- Or query Firebase directly using the service

## Troubleshooting

**No clips showing up?**
- Check audio files are in `audio/` folder
- Verify file extensions: .mp3, .wav, .m4a, or .ogg

**Language clips not working?**
- Folder name must match mother tongue (case-insensitive)
- Verify files exist in the subfolder

**Want to test?**
- Enter any mother tongue → get N general clips
- Enter "English" (if folder exists) → get N + M clips
