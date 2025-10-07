# Audio Files Structure

## Organization

Place your audio files in the `audio/` folder with the following structure:

```
audio/
├── clip1.mp3          # General clips (shown to all participants)
├── clip2.mp3
├── clip3.mp3
├── ...
├── english/           # Language-specific subfolder
│   ├── clip_en1.mp3
│   ├── clip_en2.mp3
│   └── ...
├── spanish/           # Another language-specific subfolder
│   ├── clip_es1.mp3
│   ├── clip_es2.mp3
│   └── ...
└── mandarin/          # Yet another language-specific subfolder
    ├── clip_zh1.mp3
    ├── clip_zh2.mp3
    └── ...
```

## How It Works

### Configuration Variables (in streamlit_app.py)
- `N_RANDOM_CLIPS = 10`: Number of random clips from the general folder shown to all participants
- `M_LANGUAGE_CLIPS = 5`: Number of random clips from language-specific folder (if mother tongue matches)

### Clip Selection Logic

1. **All Participants**: Get N random clips from the root `audio/` folder
2. **Language Match**: If participant's mother tongue matches a subfolder name (case-insensitive), add M random clips from that subfolder

### Example

If a participant enters "English" as their mother tongue:
- They will hear 10 random clips from `audio/` (general)
- Plus 5 random clips from `audio/english/` (language-specific)
- Total: 15 clips

If a participant enters "French" as their mother tongue (and no `audio/french/` folder exists):
- They will only hear 10 random clips from `audio/` (general)
- Total: 10 clips

## Supported Audio Formats

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- OGG (.ogg)

## Notes

- Subfolder names should match common language names (lowercase)
- Each participant gets a randomized set of clips
- Different participants will likely hear different clips in different orders
