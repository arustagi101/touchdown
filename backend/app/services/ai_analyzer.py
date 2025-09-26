import openai
import json
import asyncio
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import re
from app.core.config import settings

class AIAnalyzer:
    def __init__(self):
        self.client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.whisper_model = settings.WHISPER_MODEL
        self.gpt_model = settings.GPT_MODEL

    async def transcribe_audio(self, audio_path: str) -> Dict:
        try:
            with open(audio_path, 'rb') as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model=self.whisper_model,
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment", "word"]
                )

            segments = []
            for segment in transcript.segments:
                segments.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'],
                    'words': segment.get('words', [])
                })

            return {
                'text': transcript.text,
                'segments': segments,
                'language': transcript.language,
                'duration': transcript.duration
            }
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")

    async def analyze_highlights(self, transcript: Dict, sport_type: str = "general", num_highlights: int = 10) -> List[Dict]:
        prompt = self._create_analysis_prompt(transcript, sport_type, num_highlights)

        try:
            response = await self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt(sport_type)},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            highlights = self._process_highlights(result.get('highlights', []), transcript)

            return sorted(highlights, key=lambda x: x['score'], reverse=True)[:num_highlights]
        except Exception as e:
            raise Exception(f"Highlight analysis failed: {str(e)}")

    def _get_system_prompt(self, sport_type: str) -> str:
        base_prompt = """You are an expert sports video analyst specializing in identifying key moments and highlights from game footage.
        Your task is to analyze transcripts of sports commentary and identify the most exciting, important, and memorable moments."""

        sport_specific = {
            "soccer": "Focus on goals, near misses, penalties, red cards, exceptional saves, and skillful plays.",
            "basketball": "Focus on dunks, three-pointers, buzzer beaters, blocks, steals, and fast breaks.",
            "football": "Focus on touchdowns, interceptions, sacks, long passes, fumbles, and field goals.",
            "baseball": "Focus on home runs, strikeouts, double plays, stolen bases, and spectacular catches.",
            "tennis": "Focus on aces, break points, long rallies, match points, and exceptional shots.",
            "general": "Focus on scoring plays, dramatic moments, exceptional skills, and game-changing events."
        }

        return f"{base_prompt}\n\n{sport_specific.get(sport_type, sport_specific['general'])}"

    def _create_analysis_prompt(self, transcript: Dict, sport_type: str, num_highlights: int) -> str:
        return f"""Analyze this sports commentary transcript and identify the top {num_highlights} highlight moments.

Transcript:
{transcript['text']}

For each highlight, provide:
1. start_time: The timestamp when the highlight begins (in seconds)
2. end_time: The timestamp when the highlight ends (in seconds)
3. score: A score from 0-100 indicating how exciting/important this moment is
4. category: The type of highlight (e.g., "goal", "save", "skill", "drama")
5. description: A brief description of what happens
6. key_phrases: Key commentary phrases that indicate this highlight

Return the response as a JSON object with a 'highlights' array containing these moments.

Consider factors like:
- Excitement level in commentary (exclamations, raised voice indicators)
- Game-critical moments (scores, saves, turnovers)
- Exceptional individual performances
- Dramatic narrative moments
- Crowd reactions mentioned in commentary

Focus on {sport_type} specific highlights."""

    def _process_highlights(self, raw_highlights: List[Dict], transcript: Dict) -> List[Dict]:
        processed = []
        segments = transcript['segments']

        for highlight in raw_highlights:
            start_time = float(highlight.get('start_time', 0))
            end_time = float(highlight.get('end_time', start_time + 10))

            start_time = max(0, start_time - 3)
            end_time = end_time + 2

            relevant_text = self._extract_relevant_text(segments, start_time, end_time)

            processed.append({
                'start_time': start_time,
                'end_time': end_time,
                'duration': end_time - start_time,
                'score': float(highlight.get('score', 50)),
                'category': highlight.get('category', 'general'),
                'description': highlight.get('description', ''),
                'transcript_segment': relevant_text,
                'key_phrases': highlight.get('key_phrases', [])
            })

        return processed

    def _extract_relevant_text(self, segments: List[Dict], start_time: float, end_time: float) -> str:
        relevant_text = []
        for segment in segments:
            seg_start = segment['start']
            seg_end = segment['end']

            if seg_start <= end_time and seg_end >= start_time:
                relevant_text.append(segment['text'])

        return ' '.join(relevant_text)

    async def enhance_description(self, highlight: Dict, context: str = "") -> str:
        try:
            prompt = f"""Create a brief, engaging description for this sports highlight:

Highlight: {highlight['description']}
Category: {highlight['category']}
Transcript: {highlight['transcript_segment']}
Context: {context}

Write a 1-2 sentence description that would excite viewers."""

            response = await self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )

            return response.choices[0].message.content.strip()
        except Exception:
            return highlight.get('description', 'Highlight moment')

    async def suggest_music(self, highlights: List[Dict], sport_type: str) -> Dict:
        try:
            categories = [h['category'] for h in highlights]
            avg_score = sum(h['score'] for h in highlights) / len(highlights) if highlights else 50

            prompt = f"""Suggest background music characteristics for a {sport_type} highlight reel with these moments: {categories}.
            Average excitement level: {avg_score}/100.

            Return a JSON object with:
            - tempo: suggested BPM
            - energy: low/medium/high
            - genre: music genre
            - mood: emotional tone
            - example_tracks: 2-3 example track suggestions"""

            response = await self.client.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)
        except Exception:
            return {
                "tempo": 120,
                "energy": "high",
                "genre": "electronic",
                "mood": "epic",
                "example_tracks": ["Epic Sports Theme"]
            }