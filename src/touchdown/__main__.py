import json
import sys
import click
from .highlight_extractor import HighlightExtractor


@click.command()
@click.argument('video_url', type=str)
@click.option('--max-highlights', '-n', default=20, type=int, 
              help='Maximum number of highlights to extract (1-50, default: 20)')
@click.option('--pretty', '-p', is_flag=True, 
              help='Pretty print JSON output')
def main(video_url: str, max_highlights: int, pretty: bool):
    """
    Extract highlight moments from a YouTube sports video.
    
    VIDEO_URL: YouTube video URL to analyze
    """
    try:
        # Validate input
        if not video_url:
            click.echo("Error: Please provide a YouTube video URL", err=True)
            sys.exit(1)
        
        if max_highlights < 1 or max_highlights > 50:
            click.echo("Error: max-highlights must be between 1 and 50", err=True)
            sys.exit(1)
        
        # Initialize extractor
        extractor = HighlightExtractor()
        
        # Extract highlights
        click.echo(f"Analyzing video: {video_url}", err=True)
        result = extractor.extract_highlights_to_json(video_url, max_highlights)
        
        # Output JSON
        if pretty:
            json_output = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            json_output = json.dumps(result, ensure_ascii=False)
        
        click.echo(json_output)
        
    except ValueError as e:
        click.echo(f"Input Error: {e}", err=True)
        sys.exit(1)
    except RuntimeError as e:
        click.echo(f"Processing Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    main()