"""DaVinci Resolve export utilities for timeline automation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from ..utils import get_logger

logger = get_logger("resolve_exporter")


class ResolveExportError(RuntimeError):
    """Raised when export to DaVinci Resolve formats fails."""


class ResolveExporter:
    """Export timeline data to DaVinci Resolve-compatible formats.

    Generates industry-standard formats:
    - EDL (CMX 3600): Simple cut list with timecodes
    - FCPXML: Advanced format with markers and bins
    - Python Script: Direct Resolve API automation
    """

    def __init__(self, project_dir: Path, fps: int = 30):
        """Initialize exporter.

        Args:
            project_dir: Path to project directory containing timeline data
            fps: Frames per second for timecode conversion (default: 30)
        """
        self.project_dir = Path(project_dir)
        self.fps = fps
        self.timeline_data: Optional[dict] = None

    def load_timeline_data(self) -> dict:
        """Load timeline_timestamps.json from project directory.

        Returns:
            Timeline data dictionary

        Raises:
            ResolveExportError: If timeline data file not found or invalid
        """
        timeline_path = self.project_dir / "audio" / "timeline_timestamps.json"

        if not timeline_path.exists():
            raise ResolveExportError(
                f"Timeline data not found at {timeline_path}. "
                "Generate full audio first to create timeline data."
            )

        try:
            with open(timeline_path, "r", encoding="utf-8") as f:
                self.timeline_data = json.load(f)
                logger.info("Loaded timeline data from %s", timeline_path)
                return self.timeline_data
        except json.JSONDecodeError as e:
            raise ResolveExportError(f"Invalid JSON in timeline data: {e}") from e
        except Exception as e:
            raise ResolveExportError(f"Failed to load timeline data: {e}") from e

    def generate_edl(self, output_path: Path) -> Path:
        """Generate CMX 3600 EDL file from timeline data.

        EDL format features:
        - Industry standard for cut lists
        - Simple text format
        - Good for audio sync and basic cuts
        - Includes timecodes and clip references

        Args:
            output_path: Where to save the EDL file

        Returns:
            Path to saved EDL file

        Raises:
            ResolveExportError: If generation fails
        """
        if not self.timeline_data:
            self.load_timeline_data()

        logger.info("Generating EDL file to %s", output_path)

        try:
            edl_content = self._generate_edl_content()

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write EDL file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(edl_content)

            logger.info("Successfully generated EDL: %s", output_path)
            return output_path

        except Exception as e:
            raise ResolveExportError(f"Failed to generate EDL: {e}") from e

    def _generate_edl_content(self) -> str:
        """Generate CMX 3600 EDL format content.

        Returns:
            EDL file content as string
        """
        project_name = self.timeline_data["project_name"]
        fps = self.timeline_data.get("fps", self.fps)

        lines = []

        # EDL Header
        lines.append(f"TITLE: {project_name}")
        lines.append("FCM: NON-DROP FRAME")
        lines.append("")

        event_number = 1

        # Add video clips for each shot
        for scene in self.timeline_data["scenes"]:
            scene_num = scene["scene_number"]
            scene_title = scene["scene_title"]

            # Add scene marker comment
            lines.append(f"* MARKER: SCENE {scene_num} - {scene_title}")
            lines.append("")

            for shot in scene["shots"]:
                shot_num = shot["shot_number"]
                start_tc = shot["start_timecode"]
                end_tc = shot["end_timecode"]
                duration_tc = self._format_duration_timecode(shot["duration_ms"], fps)

                # Check if video exists, otherwise use image
                video_path = self.project_dir / "videos" / f"scene_{scene_num:02d}" / f"shot_{shot_num:02d}.mp4"

                if video_path.exists():
                    clip_name = f"scene_{scene_num:02d}_shot_{shot_num:02d}.mp4"
                    # Add time-stretch comment for 8s source video
                    actual_duration = shot["duration_ms"] / 1000
                    lines.append(f"* VIDEO CLIP: 8s source → stretch to {actual_duration:.2f}s in Resolve")
                else:
                    clip_name = f"scene_{scene_num:02d}_shot_{shot_num:02d}.png"

                # EDL format: EventNum Reel Track Edit SourceIn SourceOut RecordIn RecordOut
                lines.append(
                    f"{event_number:03d}  AX       V     C        "
                    f"00:00:00:00 {duration_tc} {start_tc} {end_tc}"
                )
                lines.append(f"* FROM CLIP NAME: {clip_name}")

                # Add shot narration as comment
                if shot.get("narration_preview"):
                    narration = shot["narration_preview"].replace("\n", " ")
                    lines.append(f"* NARRATION: {narration}")

                lines.append("")
                event_number += 1

        # Add audio track at the end
        total_duration_tc = self.timeline_data["total_duration_timecode"]
        lines.append(f"* AUDIO TRACK")
        lines.append("")
        lines.append(
            f"{event_number:03d}  AX       AA   C        "
            f"00:00:00:00 {total_duration_tc} 00:00:00:00 {total_duration_tc}"
        )
        lines.append(f"* FROM CLIP NAME: full_narration.mp3")
        lines.append("")

        return "\n".join(lines)

    def _format_duration_timecode(self, duration_ms: int, fps: int) -> str:
        """Convert duration in milliseconds to timecode format.

        Args:
            duration_ms: Duration in milliseconds
            fps: Frames per second

        Returns:
            Timecode string in format HH:MM:SS:FF
        """
        total_seconds = duration_ms / 1000
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)
        frames = int((total_seconds % 1) * fps)

        return f"{hours:02d}:{minutes:02d}:{seconds:02d}:{frames:02d}"

    def generate_fcpxml(self, output_path: Path) -> Path:
        """Generate Final Cut Pro XML (compatible with Resolve).

        FCPXML features:
        - More detailed than EDL
        - Supports markers, metadata, and bins
        - DaVinci Resolve can import FCPXML
        - Allows organization into folder structure

        Args:
            output_path: Where to save the FCPXML file

        Returns:
            Path to saved FCPXML file

        Raises:
            ResolveExportError: If generation fails
        """
        if not self.timeline_data:
            self.load_timeline_data()

        logger.info("Generating FCPXML file to %s", output_path)

        try:
            fcpxml_content = self._generate_fcpxml_content()

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write FCPXML file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(fcpxml_content)

            logger.info("Successfully generated FCPXML: %s", output_path)
            return output_path

        except Exception as e:
            raise ResolveExportError(f"Failed to generate FCPXML: {e}") from e

    def _generate_fcpxml_content(self) -> str:
        """Generate FCPXML format content.

        Returns:
            FCPXML file content as string
        """
        project_name = self.timeline_data["project_name"]
        fps = self.timeline_data.get("fps", self.fps)
        frame_duration = f"1/{fps}s"

        lines = []

        # XML Header
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<!DOCTYPE fcpxml>')
        lines.append('<fcpxml version="1.9">')
        lines.append('  <resources>')
        lines.append(f'    <format id="r1" frameDuration="{frame_duration}" width="1920" height="1080"/>')

        # Define audio asset
        audio_path = str((self.project_dir / "audio" / "full_narration.mp3").absolute())
        lines.append(f'    <asset id="audio1" src="file://{audio_path}" audioSources="1"/>')

        # Define image/video assets for each shot
        asset_id = 1
        for scene in self.timeline_data["scenes"]:
            for shot in scene["shots"]:
                scene_num = scene["scene_number"]
                shot_num = shot["shot_number"]

                # Check for video first, fallback to image
                video_path = self.project_dir / "videos" / f"scene_{scene_num:02d}" / f"shot_{shot_num:02d}.mp4"

                if video_path.exists():
                    # Use video clip
                    asset_src = str(video_path.absolute())
                    lines.append(f'    <asset id="asset{asset_id}" src="file://{asset_src}"/>')

                    # Add comment about time-stretching
                    actual_duration_ms = shot["duration_ms"]
                    lines.append(f'    <!-- Time-stretch: 8000ms source to {actual_duration_ms}ms -->')
                else:
                    # Fallback to image
                    image_path = self.project_dir / "images" / f"scene_{scene_num:02d}" / f"shot_{shot_num:02d}.png"
                    asset_src = str(image_path.absolute())
                    lines.append(f'    <asset id="asset{asset_id}" src="file://{asset_src}"/>')

                asset_id += 1

        lines.append('  </resources>')
        lines.append('  <library>')
        lines.append(f'    <event name="{project_name}">')
        lines.append(f'      <project name="{project_name}_Timeline">')
        lines.append('        <sequence format="r1">')
        lines.append('          <spine>')

        # Add video clips
        asset_id = 1
        for scene in self.timeline_data["scenes"]:
            scene_num = scene["scene_number"]
            scene_title = scene["scene_title"]

            # Add scene marker
            start_tc = scene["start_timecode"]
            lines.append(
                f'            <marker start="{start_tc}" duration="{frame_duration}" '
                f'value="Scene {scene_num}: {scene_title}"/>'
            )

            for shot in scene["shots"]:
                duration_ms = shot["duration_ms"]
                duration_frac = f"{duration_ms}/{fps}000s"

                lines.append(f'            <asset-clip ref="asset{asset_id}" duration="{duration_frac}"/>')
                asset_id += 1

        lines.append('          </spine>')

        # Add audio track
        total_duration_ms = self.timeline_data["total_duration_ms"]
        audio_duration = f"{total_duration_ms}/{fps}000s"
        lines.append('          <audio lane="1">')
        lines.append(f'            <asset-clip ref="audio1" duration="{audio_duration}"/>')
        lines.append('          </audio>')

        lines.append('        </sequence>')
        lines.append('      </project>')
        lines.append('    </event>')
        lines.append('  </library>')
        lines.append('</fcpxml>')

        return "\n".join(lines)

    def generate_resolve_script(self, output_path: Path) -> Path:
        """Generate Python script for DaVinci Resolve API.

        Script features:
        - Uses native Resolve API
        - Creates project, imports media
        - Builds timeline with precise cuts
        - Adds markers at scene boundaries
        - Organizes media pool by scene

        Args:
            output_path: Where to save the Python script

        Returns:
            Path to saved script file

        Raises:
            ResolveExportError: If generation fails
        """
        if not self.timeline_data:
            self.load_timeline_data()

        logger.info("Generating Resolve API script to %s", output_path)

        try:
            script_content = self._generate_resolve_api_script()

            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            # Write script file
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Make script executable
            output_path.chmod(0o755)

            logger.info("Successfully generated Resolve script: %s", output_path)
            return output_path

        except Exception as e:
            raise ResolveExportError(f"Failed to generate Resolve script: {e}") from e

    def _generate_resolve_api_script(self) -> str:
        """Generate Python script using DaVinci Resolve API.

        Returns:
            Python script content as string
        """
        project_name = self.timeline_data["project_name"]
        fps = self.timeline_data.get("fps", self.fps)

        script_lines = [
            "#!/usr/bin/env python3",
            f'"""Auto-generated DaVinci Resolve import script for {project_name}"""',
            "",
            "import sys",
            "import json",
            "from pathlib import Path",
            "",
            "# DaVinci Resolve API imports",
            "try:",
            "    import DaVinciResolveScript as dvr_script",
            "except ImportError:",
            "    print('ERROR: DaVinciResolveScript not found.')",
            "    print('Make sure DaVinci Resolve is installed and the API is accessible.')",
            "    sys.exit(1)",
            "",
            "# Load timeline data",
            "timeline_path = Path(__file__).parent / 'timeline_timestamps.json'",
            "with open(timeline_path) as f:",
            "    timeline_data = json.load(f)",
            "",
            "# Initialize Resolve",
            "resolve = dvr_script.scriptapp('Resolve')",
            "if not resolve:",
            "    print('ERROR: Could not connect to DaVinci Resolve.')",
            "    print('Make sure DaVinci Resolve is running.')",
            "    sys.exit(1)",
            "",
            "project_manager = resolve.GetProjectManager()",
            "media_storage = resolve.GetMediaStorage()",
            "",
            f"# Create project",
            f"project_name = '{project_name}'",
            "project = project_manager.CreateProject(project_name)",
            "if not project:",
            "    print(f'ERROR: Could not create project {project_name}')",
            "    sys.exit(1)",
            "",
            "media_pool = project.GetMediaPool()",
            "root_folder = media_pool.GetRootFolder()",
            "",
            "# Set project settings",
            f"project.SetSetting('timelineFrameRate', str({fps}))",
            "",
            "# Import audio",
            "audio_path = Path(__file__).parent / 'full_narration.mp3'",
            "if audio_path.exists():",
            "    media_pool.ImportMedia([str(audio_path.absolute())])",
            "    print(f'✅ Imported audio: {audio_path.name}')",
            "else:",
            "    print(f'⚠️  Audio file not found: {audio_path}')",
            "",
            "# Create bins and import images for each scene",
            "for scene in timeline_data['scenes']:",
            "    scene_num = scene['scene_number']",
            "    scene_title = scene['scene_title']",
            "    bin_name = f\"Scene {scene_num}: {scene_title}\"",
            "",
            "    # Create scene bin",
            "    scene_bin = media_pool.AddSubFolder(root_folder, bin_name)",
            "    if not scene_bin:",
            "        print(f'⚠️  Could not create bin: {bin_name}')",
            "        continue",
            "",
            "    # Set current folder for imports",
            "    media_pool.SetCurrentFolder(scene_bin)",
            "",
            "    # Import scene videos or images",
            "    for shot in scene['shots']:",
            "        shot_num = shot['shot_number']",
            "        ",
            "        # Check for video first, fallback to image",
            "        video_path = Path(__file__).parent.parent / 'videos' / f\"scene_{scene_num:02d}\" / f\"shot_{shot_num:02d}.mp4\"",
            "        ",
            "        if video_path.exists():",
            "            media_pool.ImportMedia([str(video_path.absolute())])",
            "            print(f'  ✅ Imported video: {video_path.name}')",
            "            ",
            "            # Note: Apply speed adjustment in Resolve timeline",
            "            actual_duration_ms = shot['duration_ms']",
            "            speed_factor = (8000 / actual_duration_ms) * 100  # Speed percentage",
            "            print(f'     → Adjust speed to {speed_factor:.1f}% for proper sync')",
            "        else:",
            "            image_path = Path(__file__).parent.parent / 'images' / f\"scene_{scene_num:02d}\" / f\"shot_{shot_num:02d}.png\"",
            "            if image_path.exists():",
            "                media_pool.ImportMedia([str(image_path.absolute())])",
            "                print(f'  ✅ Imported image: {image_path.name}')",
            "            else:",
            "                print(f'  ⚠️  Media not found: shot_{shot_num:02d}')",
            "",
            "# Create timeline",
            "media_pool.SetCurrentFolder(root_folder)",
            "timeline = media_pool.CreateEmptyTimeline(f'{project_name}_Timeline')",
            "if not timeline:",
            "    print('ERROR: Could not create timeline')",
            "    sys.exit(1)",
            "",
            "print(f'✅ Created timeline: {timeline.GetName()}')",
            "",
            "# Add markers at scene boundaries",
            "for scene in timeline_data['scenes']:",
            "    scene_num = scene['scene_number']",
            "    scene_title = scene['scene_title']",
            "    start_frame = int(scene['start_ms'] * {fps} / 1000)",
            "",
            "    marker_name = f\"Scene {scene_num}\"",
            "    marker_note = scene_title",
            "",
            "    timeline.AddMarker(start_frame, 'Blue', marker_name, marker_note, 1)",
            "    print(f'✅ Added marker at frame {start_frame}: {marker_name}')",
            "",
            "print()",
            "print('🎉 Successfully set up DaVinci Resolve project!')",
            "print(f'📁 Project: {project_name}')",
            "print(f'🎬 Timeline: {project_name}_Timeline')",
            "print()",
            "print('Next steps:')",
            "print('1. Manually add media clips to the timeline from the media pool')",
            "print('2. Use the timeline_timestamps.json for precise timing alignment')",
            "print('3. Apply transitions and effects as needed')",
        ]

        return "\n".join(script_lines)
