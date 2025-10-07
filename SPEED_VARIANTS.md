# Speed Variant Filtering & Clean Display Names

## What Was Changed

### 1. Speed Duplicate Filtering
Added `filter_speed_duplicates()` function that:
- Detects files with `_spedup` suffix
- Groups them with their normal-speed counterparts
- Randomly selects ONE version per participant
- Ensures no participant hears both versions

### 2. Clean Display Names
Changed clip titles from filenames to sequential numbers:
- **Before**: "News Clip 4 Spedup"
- **After**: "Audio Clip 1", "Audio Clip 2", etc.

## File Naming Convention

### For Speed Variants
```
clip_name.mp3          # Original version
clip_name_spedup.mp3   # Speed variant
```

### Examples
```
audio/
├── news_clip_4.mp3
├── news_clip_4_spedup.mp3       # Only ONE will be selected
├── news_clip_5.mp3
├── news_clip_5_spedup.mp3       # Only ONE will be selected
└── english/
    ├── news_clip_1.mp3
    └── news_clip_2_spedup.mp3   # Can have just the spedup version
```

## How It Works

### Detection Algorithm
1. For each file, extract base name (remove `_spedup` suffix)
2. Group files by base name
3. For each group, randomly pick one version
4. Use selected files for participant assignment

### Example
If you have:
- `news_clip_4.mp3`
- `news_clip_4_spedup.mp3`

**Participant A** might get: `news_clip_4.mp3` (shown as "Audio Clip 3")
**Participant B** might get: `news_clip_4_spedup.mp3` (shown as "Audio Clip 5")

They'll never know which version they got!

## Benefits

✅ **No filename leakage**: Participants don't see technical names
✅ **Balanced distribution**: Equal chance of normal/spedup versions
✅ **Clean UX**: Simple "Audio Clip N" naming
✅ **Flexible**: Can have just normal, just spedup, or both versions

## Testing

To verify it's working:
1. Add files: `test.mp3` and `test_spedup.mp3`
2. Start survey multiple times
3. Check Firebase data - some responses will have `test.mp3`, others `test_spedup.mp3`
4. UI should always show "Audio Clip N" (not filename)
