import json
import re
from typing import List, Optional
from openai import OpenAI
from .models import Highlight


class SportsHighlightAnalyzer:
    """Analyzes sports video transcripts using OpenAI to identify highlight moments."""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def analyze_transcript(self, transcript_text: str, max_highlights: int = 20) -> List[Highlight]:
        """
        Analyze transcript to identify sports highlights.
        
        Args:
            transcript_text: Formatted transcript with timestamps
            max_highlights: Maximum number of highlights to return
            
        Returns:
            List of Highlight objects sorted by importance
        """
        prompt = self._create_sports_analysis_prompt(transcript_text, max_highlights)
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-5",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert sports analyst who identifies the most exciting and important moments in sports games from transcripts."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ], # Lower temperature for more consistent results
            )
            
            content = response.choices[0].message.content
            return self._parse_highlights_response(content)
            
        except Exception as e:
            raise RuntimeError(f"Error analyzing transcript with OpenAI: {str(e)}")
    
    def _create_sports_analysis_prompt(self, transcript_text: str, max_highlights: int) -> str:
        """Create a detailed prompt for sports highlight analysis."""
        return f"""
Analyze this sports game transcript and identify the top {max_highlights} most exciting and important highlight moments. Focus on:

1. **Scoring moments** (goals, touchdowns, baskets, runs, etc.)
2. **Game-changing plays** (turnovers, interceptions, saves, blocks)
3. **Dramatic moments** (close calls, controversial decisions, clutch plays)
4. **Exceptional individual performances** (great saves, spectacular plays)
5. **Momentum shifts** (comebacks, key defensive stops)
6. **Critical game situations** (overtime, final minutes, penalties)

For each highlight, provide:
- **Exact start time** (in seconds from video start)
- **Exact end time** (in seconds from video start) 
- **Brief description** (1-2 sentences max)
- **Importance score** (1-10, where 10 is most exciting/important)
- **Category** (goal, save, foul, turnover, celebration, controversy, etc.)

**IMPORTANT FORMATTING REQUIREMENTS:**
- Return ONLY a JSON array of highlights
- Each highlight must be a JSON object with exactly these fields: start_time, end_time, description, importance_score, category
- Times must be in seconds (numbers, not strings)
- Importance scores must be numbers between 1-10
- Sort by importance_score (highest first)

**Transcript:**
{transcript_text}

**Response format (JSON only):**
[
  {{
    "start_time": 125.5,
    "end_time": 135.2,
    "description": "Amazing goal in the 15th minute",
    "importance_score": 9.5,
    "category": "goal"
  }}
]
"""
    
    def _parse_highlights_response(self, response_content: str) -> List[Highlight]:
        """Parse OpenAI response to extract highlights."""
        try:
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\[.*\]', response_content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = response_content.strip()
            
            highlights_data = json.loads(json_str)
            
            highlights = []
            for item in highlights_data:
                try:
                    highlight = Highlight(
                        start_time=float(item['start_time']),
                        end_time=float(item['end_time']),
                        description=str(item['description']).strip(),
                        importance_score=float(item['importance_score']),
                        category=str(item['category']).lower().strip()
                    )
                    
                    # Validate highlight data
                    if self._validate_highlight(highlight):
                        highlights.append(highlight)
                        
                except (KeyError, ValueError, TypeError) as e:
                    print(f"Warning: Skipping invalid highlight: {e}")
                    continue
            
            # Sort by importance score (highest first)
            highlights.sort(key=lambda x: x.importance_score, reverse=True)
            
            return highlights
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse OpenAI response as JSON: {e}")
        except Exception as e:
            raise RuntimeError(f"Error parsing highlights response: {e}")
    
    def _validate_highlight(self, highlight: Highlight) -> bool:
        """Validate a highlight object."""
        if highlight.start_time < 0 or highlight.end_time < 0:
            return False
        
        if highlight.start_time >= highlight.end_time:
            return False
        
        if not highlight.description or len(highlight.description.strip()) == 0:
            return False
        
        if highlight.importance_score < 1 or highlight.importance_score > 10:
            return False
        
        # Duration should be reasonable (between 5 seconds and 5 minutes)
        duration = highlight.end_time - highlight.start_time
        if duration < 5 or duration > 300:
            return False
        
        return True
