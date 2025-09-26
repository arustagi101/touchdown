# Touchdown

YouTube Sports Video Highlight Extractor - Extract the top highlight moments from sports videos using AI.

## Features

- Extract top 20 highlight moments from YouTube sports videos
- Support for videos up to 4 hours long
- AI-powered analysis using OpenAI GPT-4
- JSON output with precise timestamps and descriptions
- Sports-focused categorization (goals, saves, fouls, etc.)
- Importance scoring (1-10) for each highlight

## Setup

### 1. Install Dependencies

```bash
uv sync
```

### 2. Configure OpenAI API Key

Create a `.env` file in the project root:

```bash
# .env
OPENAI_API_KEY=your_openai_api_key_here
```

## Usage

### Basic Usage

```bash
# Extract highlights from a YouTube sports video
uv run python -m touchdown "https://www.youtube.com/watch?v=VIDEO_ID"

# Pretty print JSON output
uv run python -m touchdown "https://www.youtube.com/watch?v=VIDEO_ID" --pretty

# Limit number of highlights
uv run python -m touchdown "https://www.youtube.com/watch?v=VIDEO_ID" --max-highlights 10
```

### Example Output

```json
{
  "video_url": "https://www.youtube.com/watch?v=example",
  "video_title": null,
  "total_duration": 5400.0,
  "total_duration_formatted": "01:30:00",
  "highlights": [
    {
      "start_time": 1245.5,
      "end_time": 1265.2,
      "start_time_formatted": "20:45",
      "end_time_formatted": "21:05", 
      "duration": 19.7,
      "description": "Amazing goal in the 21st minute with spectacular teamwork",
      "importance_score": 9.5,
      "category": "goal"
    }
  ]
}
```

### Command Line Options

- `VIDEO_URL`: YouTube video URL (required)
- `--max-highlights, -n`: Maximum number of highlights (1-50, default: 20)
- `--pretty, -p`: Pretty print JSON output

## Requirements

- Python 3.13+
- OpenAI API key
- YouTube videos with available transcripts

## Supported Video Length

- Up to 4 hours (14,400 seconds)

## Highlight Categories

The AI identifies various types of sports highlights:
- `goal`: Scoring moments
- `save`: Defensive saves/stops
- `foul`: Fouls and penalties
- `turnover`: Ball possession changes
- `celebration`: Notable celebrations
- `controversy`: Disputed calls/moments