from .models import VideoAnalysis
from .transcript_fetcher import YouTubeTranscriptFetcher
from .highlight_analyzer import SportsHighlightAnalyzer


class HighlightExtractor:
    """Main class that orchestrates the highlight extraction process."""

    def __init__(self):
        self.analyzer = SportsHighlightAnalyzer()
        self.transcript_fetcher = YouTubeTranscriptFetcher()

    def extract_highlights(
        self, video_url: str, max_highlights: int = 20
    ) -> VideoAnalysis:
        """
        Extract highlights from a YouTube video.

        Args:
            video_url: YouTube video URL
            max_highlights: Maximum number of highlights to extract (default 20)

        Returns:
            VideoAnalysis object containing all highlights

        Raises:
            ValueError: If video URL is invalid or transcript unavailable
            RuntimeError: If analysis fails
        """
        if not video_url or not isinstance(video_url, str):
            raise ValueError("Invalid video URL provided")

        if max_highlights < 1 or max_highlights > 50:
            raise ValueError("max_highlights must be between 1 and 50")

        # Step 1: Fetch transcript
        try:
            print(f"Fetching transcript for: {video_url}")
            transcript_entries = self.transcript_fetcher.fetch_transcript(video_url)

            if not transcript_entries:
                raise ValueError("No transcript data found for this video")

            print(f"Found {len(transcript_entries)} transcript entries")

        except Exception as e:
            raise ValueError(f"Failed to fetch transcript: {str(e)}")

        # Step 2: Format transcript for analysis
        formatted_transcript = self.transcript_fetcher.format_transcript_for_analysis(
            transcript_entries
        )
        total_duration = self.transcript_fetcher.get_total_duration(transcript_entries)

        print(
            f"Video duration: {total_duration:.1f} seconds ({total_duration / 3600:.1f} hours)"
        )

        # Validate video duration (up to 4 hours as requested)
        if total_duration > 14400:  # 4 hours in seconds
            raise ValueError(
                "Video is longer than 4 hours, which exceeds the supported limit"
            )

        # Step 3: Analyze transcript for highlights
        try:
            print("Analyzing transcript for sports highlights...")
            highlights = self.analyzer.analyze_transcript(
                formatted_transcript, max_highlights
            )

            if not highlights:
                raise RuntimeError("No highlights were identified in this video")

            print(f"Identified {len(highlights)} highlights")

        except Exception as e:
            raise RuntimeError(f"Failed to analyze transcript: {str(e)}")

        # Step 4: Create and return analysis result
        analysis = VideoAnalysis(
            video_url=video_url,
            video_title=None,  # Could be enhanced to fetch video title
            total_duration=total_duration,
            highlights=highlights[:max_highlights],  # Ensure we don't exceed the limit
        )

        return analysis

    def extract_highlights_to_json(
        self, video_url: str, max_highlights: int = 20
    ) -> dict:
        """
        Extract highlights and return as JSON-serializable dictionary.

        Args:
            video_url: YouTube video URL
            max_highlights: Maximum number of highlights to extract

        Returns:
            Dictionary containing the analysis results
        """
        analysis = self.extract_highlights(video_url, max_highlights)
        return analysis.to_json()
