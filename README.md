# Daily Motivation: AI-Powered Video Content System

This repository contains a comprehensive video content system with **two main modes of operation** for creating video content on Twitter/X.

## 🎯 Two Main Functionalities

### 1. 📱 Daily Motivational Video Poster (`main.py`)
**Automated daily posting of short motivational videos**
- Searches YouTube for motivational content from successful people
- Downloads videos (1-10 minutes) optimized for Twitter
- Uses AI to generate inspiring post descriptions
- Automatically posts to Twitter with smart scheduling
- Maintains database of posted content to avoid duplicates

### 2. 🧠 AI-Powered Long-Form Video Snippet Extractor (`post_long_form_video.py`)
**Transform long interviews/podcasts into viral Twitter threads**
- Downloads long-form YouTube videos (interviews, podcasts)
- AI transcription using OpenAI Whisper with word-level timestamps
- GPT-4.1 identifies 5-10 powerful narrative themes that resonate with audiences
- Creates precise video clips from identified segments using FFmpeg
- Posts extracted snippets as engaging Twitter threads with contextual descriptions

## 🚀 What Each Mode Does

### Daily Poster Features:
- **Smart Video Discovery**: Searches for motivational content from 30+ successful people
- **Duration Filtering**: Only downloads 1-10 minute videos (Twitter-compatible)
- **SQLite Database**: Tracks posted content to prevent duplicates
- **Progressive Search**: Expands search if no suitable videos found
- **AI-Generated Captions**: Uses GPT-4.1 to create compelling post descriptions
- **Community Support**: Can post to Twitter communities

### Snippet Extractor Features:
- **AI-Powered Content Curation**: Identifies universally resonant themes like struggle & overcoming, mindset shifts, practical wisdom
- **Robust Text Matching**: Advanced fuzzy matching algorithms to accurately find transcript segments
- **Intelligent Thread Creation**: Posts snippets as Twitter threads with proper context and source attribution
- **Smart Deduplication**: Prevents overlapping video segments and optimizes content flow
- **Flexible Processing**: Multiple Whisper model sizes for different speed/accuracy tradeoffs

## 📋 Prerequisites

- Python 3.10+
- FFmpeg installed on your system
- OpenAI API key
- Twitter API credentials
- At least 4GB RAM for Whisper processing. NOTE: you would need a GPU if you're planning to use the base (and above) models on videos larger than 15-20 minutes. Its very slow on CPU.
- SQLite (included with Python)

## 🛠 Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/nishantkumar1292/daily_motivation.git
   cd daily_motivation
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install FFmpeg:
   - **macOS**: `brew install ffmpeg`
   - **Ubuntu**: `sudo apt update && sudo apt install ffmpeg`
   - **Windows**: Download from [FFmpeg official site](https://ffmpeg.org/download.html)

## ⚙️ Configuration

Create a `.env` file in the root directory with the following variables:

```env
# OpenAI API Key (required for AI features)
OPENAI_API_KEY=your_openai_api_key_here

# Twitter API Credentials (required for posting)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
TWITTER_BEARER_TOKEN=your_bearer_token

# Optional: Twitter Community ID for community posting
TWITTER_COMMUNITY_ID=your_community_id
```

## 🚀 Usage

### Mode 1: Daily Motivational Video Posting
```bash
python main.py
```
**What it does:**
- Checks database for unposted videos
- If none found, searches for new motivational videos from successful people
- Downloads and posts one video with AI-generated caption
- Updates database to track posted content

**Successful People List:** Edit `successful.txt` to customize the list of people to search for (includes Oprah, Elon Musk, Steve Jobs, etc.)

### Mode 2: AI-Powered Long-Form Video Processing
```bash
python post_long_form_video.py
```
**Customization:** Edit the variables in the script:
```python
video_url = "https://www.youtube.com/watch?v=YOUR_VIDEO_ID"
video_speaker_x_handle = "speaker_twitter_handle"  # for attribution
```

### Whisper Model Options (for long-form processing)
Choose transcription accuracy vs speed:
- `"tiny"`: Fastest (~39x realtime)
- `"base"`: Balanced (default, ~16x realtime)
- `"small"`: Better accuracy (~6x realtime)
- `"medium"`: High accuracy (~2x realtime)
- `"large"`: Best accuracy (~1x realtime)

## 📁 Output Structure

```
daily_motivation/
├── videos/                    # Downloaded video files
├── extracted_snippets/        # AI-generated video clips (Mode 2)
│   ├── snippets_metadata.json # Metadata for all clips
│   └── *.mp4                 # Individual snippet files
├── db.sqlite                 # Database for posted content (Mode 1)
├── transcription.json        # Full video transcription (Mode 2)
├── narratives.json          # AI-identified themes (Mode 2)
├── snippet_timestamps.json  # Timing data for clips (Mode 2)
└── successful.txt           # List of successful people to search
```

## 🔧 Core Components

- **`main.py`**: Daily motivational video poster with database management
- **`post_long_form_video.py`**: AI-powered long-form video snippet extractor
- **`poster.py`**: Twitter API integration and AI-powered post generation
- **`text_matching.py`**: Advanced text matching algorithms for precise timestamp extraction
- **`successful.txt`**: Curated list of successful people for content discovery
- **`requirements.txt`**: All Python dependencies


## 🎯 TODOs

- [ ] Automated scheduling for daily posting
- [ ] Integration between both modes
- [ ] WhatsApp channel integration
- [ ] Automated YouTube search integration for snippet extractor
- [ ] Support for longer videos (>10 minutes per clip)
- [ ] Speaker tagging and attribution improvements
- [ ] Custom theme configuration
- [ ] Auto detection of themes from the video
