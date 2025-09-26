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
    
    async def _create_concat_file(self, clip_paths: List[str], output_dir: str) -> str:
        """
        Create a concat file for ffmpeg to stitch clips together.
        
        Args:
            clip_paths: List of paths to clip files
            output_dir: Output directory
            
        Returns:
            Path to the concat file
        """
        concat_file_path = os.path.join(output_dir, "concat_list.txt")
        
        with open(concat_file_path, 'w') as f:
            for clip_path in clip_paths:
                abs_path = os.path.abspath(clip_path)
                escaped_path = abs_path.replace("\\", "\\\\").replace(":", "\\:")
                f.write(f"file '{escaped_path}'\n")
        
        return concat_file_path
    
    async def _stitch_clips(self, concat_file_path: str, output_path: str) -> str:
        """
        Stitch clips together using ffmpeg concat.
        
        Args:
            concat_file_path: Path to the concat file
            output_path: Path for the final output video
            
        Returns:
            Path to the final stitched video
        """
        try:
            # Use ffmpeg concat demuxer for better compatibility
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
                
                # Calculate duration for cached response
                total_duration = sum(h.end_time - h.start_time for h in highlights)
                
                return {
                    "success": True,
                    "message": "Final highlight already exists (cached)",
                    "output_path": final_highlight_path,
                    "already_exists": True,
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / 1024 / 1024, 2),
                    "cached_at": file_mtime,
                    "clips_used": len(highlights),
                    "total_duration": total_duration
                }
            
            print(f"Creating final highlight from {len(highlights)} clips...")
            
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
            
            # Step 3: Create concat file
            print("Creating concat file...")
            concat_file_path = await self._create_concat_file(clip_paths, output_dir)
            
            # Step 4: Stitch clips together
            print("Stitching clips together...")
            await self._stitch_clips(concat_file_path, final_highlight_path)
            
            # Step 5: Clean up temporary files
            print("Cleaning up temporary files...")
            await self._cleanup_temp_files(output_dir)
            
            # Calculate total duration
            total_duration = sum(
                highlight.end_time - highlight.start_time 
                for highlight in non_overlapping_highlights
            )
            
            return {
                "success": True,
                "message": "Final highlight created successfully",
                "output_path": final_highlight_path,
                "clips_used": len(clip_paths),
                "total_duration": total_duration,
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
                
        except Exception as e:
            print(f"Warning: Failed to clean up temporary files: {str(e)}")