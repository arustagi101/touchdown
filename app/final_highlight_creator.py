import asyncio
import os
import json
from typing import List, Tuple
import ffmpeg
from app.types import HighlightClip


class FinalHighlightCreator:
    """Creates a final highlight video by stitching clips together without overlap."""
    
    def __init__(self):
        self.temp_dir = "temp_clips"
        # Paths to intro and outro files
        self.intro_path = os.path.join(os.path.dirname(__file__), "highlights_intro.mp4")
        self.outro_path = os.path.join(os.path.dirname(__file__), "highlights_outro.mp4")
    
    def _get_video_duration(self, video_path: str) -> float:
        """
        Get the duration of a video file in seconds.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Duration in seconds, or 0 if unable to determine
        """
        try:
            probe = ffmpeg.probe(video_path)
            duration = float(probe['streams'][0]['duration'])
            return duration
        except Exception as e:
            print(f"Warning: Could not get duration for {video_path}: {str(e)}")
            return 0.0
    
    def _get_video_properties(self, video_path: str) -> dict:
        """
        Get video properties (resolution, codec, etc.) from a video file.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with video properties
        """
        try:
            probe = ffmpeg.probe(video_path)
            video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
            
            if video_stream:
                return {
                    'width': int(video_stream.get('width', 0)),
                    'height': int(video_stream.get('height', 0)),
                    'codec': video_stream.get('codec_name', 'unknown'),
                    'pixel_format': video_stream.get('pix_fmt', 'unknown'),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1'))
                }
            return {}
        except Exception as e:
            print(f"Warning: Could not get video properties for {video_path}: {str(e)}")
            return {}
    
    def _is_cache_valid(self, final_highlight_path: str, clips_json_path: str) -> bool:
        """
        Check if the cached final highlight is still valid.
        
        Args:
            final_highlight_path: Path to the final highlight video
            clips_json_path: Path to the clips.json file
            
        Returns:
            True if cache is valid, False otherwise
        """
        if not os.path.exists(final_highlight_path) or not os.path.exists(clips_json_path):
            return False
        
        # Check if final highlight is newer than clips.json
        final_highlight_mtime = os.path.getmtime(final_highlight_path)
        clips_json_mtime = os.path.getmtime(clips_json_path)
        
        return final_highlight_mtime >= clips_json_mtime
    
    def _detect_overlaps(self, highlights: List[HighlightClip]) -> List[HighlightClip]:
        """
        Detect and resolve overlapping clips by merging or adjusting them.
        
        Args:
            highlights: List of highlight clips sorted by start_time
            
        Returns:
            List of non-overlapping highlight clips
        """
        if not highlights:
            return []
        
        # Sort highlights by start_time
        sorted_highlights = sorted(highlights, key=lambda x: x.start_time)
        non_overlapping = []
        
        for highlight in sorted_highlights:
            if not non_overlapping:
                non_overlapping.append(highlight)
                continue
            
            last_highlight = non_overlapping[-1]
            
            # Check for overlap
            if highlight.start_time < last_highlight.end_time:
                # There's an overlap - merge the clips
                merged_highlight = HighlightClip(
                    start_time=last_highlight.start_time,
                    end_time=max(last_highlight.end_time, highlight.end_time),
                    start_time_formatted=last_highlight.start_time_formatted,
                    end_time_formatted=highlight.end_time_formatted,
                    duration=max(last_highlight.end_time, highlight.end_time) - last_highlight.start_time,
                    description=f"{last_highlight.description} | {highlight.description}",
                    importance_score=max(
                        last_highlight.importance_score or 0, 
                        highlight.importance_score or 0
                    ),
                    category=last_highlight.category or highlight.category
                )
                non_overlapping[-1] = merged_highlight
            else:
                # No overlap, add the highlight
                non_overlapping.append(highlight)
        
        return non_overlapping
    
    async def _extract_individual_clips(self, highlights: List[HighlightClip], 
                                      video_path: str, output_dir: str) -> List[str]:
        """
        Extract individual clips for stitching.
        
        Args:
            highlights: List of highlight clips
            video_path: Path to the source video
            output_dir: Directory to save clips
            
        Returns:
            List of paths to extracted clip files
        """
        clip_paths = []
        clips_dir = os.path.join(output_dir, self.temp_dir)
        os.makedirs(clips_dir, exist_ok=True)
        
        for i, highlight in enumerate(highlights):
            clip_filename = f"clip_{i:03d}_{highlight.start_time}-{highlight.end_time}.mp4"
            clip_path = os.path.join(clips_dir, clip_filename)
            
            try:
                duration = highlight.end_time - highlight.start_time
                stream = ffmpeg.input(video_path, ss=highlight.start_time, t=duration)
                stream = ffmpeg.output(stream, clip_path, c="copy")
                
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(
                    None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True)
                )
                
                clip_paths.append(clip_path)
                print(f"Extracted clip {i+1}/{len(highlights)}: {clip_filename}")
                
            except Exception as e:
                print(f"Failed to extract clip {i+1}: {str(e)}")
                continue
        
        return clip_paths
    
    async def _normalize_intro_outro(self, output_dir: str, main_clip_properties: dict) -> tuple:
        """
        Normalize intro and outro files to match main clip properties.
        
        Args:
            output_dir: Output directory
            main_clip_properties: Video properties from main clips
            
        Returns:
            Tuple of (normalized_intro_path, normalized_outro_path)
        """
        normalized_intro_path = None
        normalized_outro_path = None
        
        # Normalize intro if it exists
        if os.path.exists(self.intro_path):
            normalized_intro_path = os.path.join(output_dir, "normalized_intro.mp4")
            await self._normalize_video_file(
                self.intro_path, normalized_intro_path, main_clip_properties
            )
            print("Normalized intro file")
        
        # Normalize outro if it exists
        if os.path.exists(self.outro_path):
            normalized_outro_path = os.path.join(output_dir, "normalized_outro.mp4")
            await self._normalize_video_file(
                self.outro_path, normalized_outro_path, main_clip_properties
            )
            print("Normalized outro file")
        
        return normalized_intro_path, normalized_outro_path
    
    async def _normalize_video_file(self, input_path: str, output_path: str, 
                                   target_properties: dict, max_duration: float = 2.0) -> str:
        """
        Normalize a video file to match target properties and limit duration.
        
        Args:
            input_path: Path to input video
            output_path: Path to output video
            target_properties: Target video properties
            max_duration: Maximum duration in seconds (default 2.0)
            
        Returns:
            Path to normalized video
        """
        try:
            # Limit duration to max_duration seconds
            stream = ffmpeg.input(input_path, t=max_duration)
            
            # Build normalization parameters
            output_params = {
                'vcodec': 'libx264',
                'acodec': 'aac',
                'preset': 'fast',
                'crf': 23,
                'async': 1,
                'vsync': 'cfr',
                'af': 'aresample=async=1'
            }
            
            # Add target resolution
            if target_properties.get('width') and target_properties.get('height'):
                output_params['s'] = f"{target_properties['width']}x{target_properties['height']}"
            
            # Add target frame rate
            if target_properties.get('fps'):
                output_params['r'] = target_properties['fps']
            
            stream = ffmpeg.output(stream, output_path, **output_params)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True)
            )
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to normalize video {input_path}: {str(e)}")
    
    async def _create_concat_file_with_intro_outro(self, clip_paths: List[str], output_dir: str, 
                                                  main_clip_properties: dict) -> str:
        """
        Create a concat file for ffmpeg to stitch clips together with intro and outro.
        Uses normalized intro/outro files that match main clip properties.
        
        Args:
            clip_paths: List of paths to clip files
            output_dir: Output directory
            main_clip_properties: Video properties from main clips
            
        Returns:
            Path to the concat file
        """
        concat_file_path = os.path.join(output_dir, "concat_list.txt")
        
        # Normalize intro and outro files
        normalized_intro_path, normalized_outro_path = await self._normalize_intro_outro(
            output_dir, main_clip_properties
        )
        
        with open(concat_file_path, 'w') as f:
            # Add normalized intro first
            if normalized_intro_path and os.path.exists(normalized_intro_path):
                intro_abs_path = os.path.abspath(normalized_intro_path)
                intro_escaped_path = intro_abs_path.replace("\\", "\\\\").replace(":", "\\:")
                f.write(f"file '{intro_escaped_path}'\n")
                print("Added normalized intro to concat list")
            else:
                print("Warning: No normalized intro file available")
            
            # Add main clips (these determine the format)
            for clip_path in clip_paths:
                abs_path = os.path.abspath(clip_path)
                escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
                f.write(f"file '{escaped_path}'\n")
            
            # Add normalized outro last
            if normalized_outro_path and os.path.exists(normalized_outro_path):
                outro_abs_path = os.path.abspath(normalized_outro_path)
                outro_escaped_path = outro_abs_path.replace("\\", "\\\\").replace(":", "\\:")
                f.write(f"file '{outro_escaped_path}'\n")
                print("Added normalized outro to concat list")
            else:
                print("Warning: No normalized outro file available")
        
        return concat_file_path
    
    async def _stitch_clips(self, concat_file_path: str, output_path: str, 
                           main_clip_properties: dict) -> str:
        """
        Stitch clips together using ffmpeg concat.
        Since files are pre-normalized, we can use copy for efficiency.
        
        Args:
            concat_file_path: Path to the concat file
            output_path: Path for the final output video
            main_clip_properties: Video properties from main clips
            
        Returns:
            Path to the final stitched video
        """
        try:
            # Use ffmpeg concat demuxer - files are already normalized
            stream = ffmpeg.input(concat_file_path, format='concat', safe=0)
            stream = ffmpeg.output(stream, output_path, c='copy')
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: ffmpeg.run(stream, overwrite_output=True, quiet=True)
            )
            
            return output_path
            
        except Exception as e:
            raise Exception(f"Failed to stitch clips: {str(e)}")
    
    async def create_final_highlight(self, highlights: List[HighlightClip], 
                                  video_path: str, output_dir: str, 
                                  overwrite: bool = False) -> dict:
        """
        Create a final highlight video by stitching clips together with intro and outro.
        
        Args:
            highlights: List of highlight clips
            video_path: Path to the source video
            output_dir: Directory to save the final highlight
            overwrite: Whether to overwrite existing final highlight
            
        Returns:
            Dictionary with result information
        """
        try:
            # Check if final highlight already exists and is valid
            final_highlight_path = os.path.join(output_dir, "final_highlight.mp4")
            clips_json_path = os.path.join(output_dir, "clips.json")
            
            if not overwrite and self._is_cache_valid(final_highlight_path, clips_json_path):
                # Get file size and modification time for cache info
                file_size = os.path.getsize(final_highlight_path)
                file_mtime = os.path.getmtime(final_highlight_path)
                
                # Calculate durations for cached response
                highlights_duration = sum(h.end_time - h.start_time for h in highlights)
                # Intro and outro are limited to 2 seconds each
                intro_duration = 2.0 if os.path.exists(self.intro_path) else 0.0
                outro_duration = 2.0 if os.path.exists(self.outro_path) else 0.0
                total_duration = highlights_duration + intro_duration + outro_duration
                
                return {
                    "success": True,
                    "message": "Final highlight already exists (cached)",
                    "output_path": final_highlight_path,
                    "already_exists": True,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / 1024 / 1024, 2),
                    "cached_at": file_mtime,
                    "clips_used": len(highlights),
                    "highlights_duration": highlights_duration,
                    "intro_duration": intro_duration,
                    "outro_duration": outro_duration,
                    "total_duration": total_duration,
                    "has_intro": os.path.exists(self.intro_path),
                    "has_outro": os.path.exists(self.outro_path)
                }
            
            print(f"Creating final highlight from {len(highlights)} clips with intro/outro...")
            
            # Step 1: Detect and resolve overlaps
            non_overlapping_highlights = self._detect_overlaps(highlights)
            print(f"After overlap resolution: {len(non_overlapping_highlights)} clips")
            
            if not non_overlapping_highlights:
                return {
                    "success": False,
                    "error": "No valid clips to stitch together",
                    "message": "No highlights available for final video"
                }
            
            # Step 2: Extract individual clips
            print("Extracting individual clips...")
            clip_paths = await self._extract_individual_clips(
                non_overlapping_highlights, video_path, output_dir
            )
            
            if not clip_paths:
                return {
                    "success": False,
                    "error": "Failed to extract any clips",
                    "message": "No clips were successfully extracted"
                }
            
            # Step 3: Get video properties from first main clip
            print("Getting video properties from main clips...")
            main_clip_properties = self._get_video_properties(clip_paths[0])
            print(f"Main clip properties: {main_clip_properties}")
            
            # Step 4: Create concat file with intro and outro
            print("Creating concat file with intro and outro...")
            concat_file_path = await self._create_concat_file_with_intro_outro(
                clip_paths, output_dir, main_clip_properties
            )
            
            # Step 5: Stitch clips together with format conversion
            print("Stitching clips together with format conversion...")
            await self._stitch_clips(concat_file_path, final_highlight_path, main_clip_properties)
            
            # Step 6: Clean up temporary files
            print("Cleaning up temporary files...")
            await self._cleanup_temp_files(output_dir)
            
            # Calculate durations
            highlights_duration = sum(
                highlight.end_time - highlight.start_time 
                for highlight in non_overlapping_highlights
            )
            
            # Get intro and outro durations (limited to 2 seconds each)
            intro_duration = 2.0 if os.path.exists(self.intro_path) else 0.0
            outro_duration = 2.0 if os.path.exists(self.outro_path) else 0.0
            total_duration = highlights_duration + intro_duration + outro_duration
            
            return {
                "success": True,
                "message": "Final highlight created successfully with intro and outro",
                "output_path": final_highlight_path,
                "clips_used": len(clip_paths),
                "highlights_duration": highlights_duration,
                "intro_duration": intro_duration,
                "outro_duration": outro_duration,
                "total_duration": total_duration,
                "has_intro": os.path.exists(self.intro_path),
                "has_outro": os.path.exists(self.outro_path),
                "video_properties": main_clip_properties,
                "highlights": [
                    {
                        "start_time": h.start_time,
                        "end_time": h.end_time,
                        "description": h.description,
                        "importance_score": h.importance_score
                    }
                    for h in non_overlapping_highlights
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to create final highlight"
            }
    
    async def _cleanup_temp_files(self, output_dir: str):
        """Clean up temporary files."""
        try:
            temp_dir = os.path.join(output_dir, self.temp_dir)
            if os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
            
            concat_file = os.path.join(output_dir, "concat_list.txt")
            if os.path.exists(concat_file):
                os.remove(concat_file)
            
            # Clean up normalized intro/outro files
            normalized_intro = os.path.join(output_dir, "normalized_intro.mp4")
            if os.path.exists(normalized_intro):
                os.remove(normalized_intro)
            
            normalized_outro = os.path.join(output_dir, "normalized_outro.mp4")
            if os.path.exists(normalized_outro):
                os.remove(normalized_outro)
                
        except Exception as e:
            print(f"Warning: Failed to clean up temporary files: {str(e)}")