# Audio Files Structure

## Organization

Place your audio files in the `audio/` folder with the following structure:

```
audio/
├── clip1.mp3                # General clips (shown to all participants)
├── clip2.mp3
├── clip2_spedup.mp3         # Speed variant (system picks one randomly)
├── clip3.mp3
├── ...
├── english/                 # Language-specific subfolder
│   ├── clip_en1.mp3
│   ├── clip_en1_spedup.mp3  # Speed variant
│   ├── clip_en2.mp3
│   └── ...
├── spanish/                 # Another language-specific subfolder
│   ├── clip_es1.mp3
│   ├── clip_es2.mp3
│   └── ...
└── mandarin/                # Yet another language-specific subfolder
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
3. **Speed Variant Filtering**: If both `clip.mp3` and `clip_spedup.mp3` exist, the system randomly picks ONE version per participant
4. **Display**: Clips are shown as "Audio Clip 1", "Audio Clip 2", etc. (not the filename)

### Example

If a participant enters "English" as their mother tongue:
- They will hear 10 random clips from `audio/` (general)
- Plus 5 random clips from `audio/english/` (language-specific)
- Total: 15 clips
- For any clip with both normal and spedup versions, only one version is randomly selected

If a participant enters "French" as their mother tongue (and no `audio/french/` folder exists):
- They will only hear 10 random clips from `audio/` (general)
- Total: 10 clips

### Speed Variants

You can create speed variants using the naming convention:
- Original: `news_clip_4.mp3`
- Speed variant: `news_clip_4_spedup.mp3`

The system will:
1. Detect both versions
2. Randomly pick ONE version for each participant
3. Never show both versions to the same participant

## Supported Audio Formats

- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- OGG (.ogg)

## Notes

- Subfolder names should match common language names (lowercase)
- Each participant gets a randomized set of clips
- Different participants will likely hear different clips in different orders
