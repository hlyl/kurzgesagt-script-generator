#!/usr/bin/env python3
"""Download video from Google Gemini API URI."""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("❌ Error: GEMINI_API_KEY not found in environment")
    print("Make sure your .env file contains GEMINI_API_KEY=your_key_here")
    sys.exit(1)

# Video URI from command line or hardcoded
if len(sys.argv) > 1:
    video_uri = sys.argv[1]
else:
    video_uri = "https://generativelanguage.googleapis.com/v1beta/files/ej9z601zavdp:download?alt=media"

# Output file from command line or default
if len(sys.argv) > 2:
    output_file = sys.argv[2]

    # If filename contains scene/shot info, try to save to correct directory
    if "scene_" in output_file and "shot_" in output_file:
        # Extract scene number
        import re
        scene_match = re.search(r'scene_(\d+)', output_file)
        if scene_match:
            scene_num = scene_match.group(1)

            # Check if we're in a project directory
            projects_dir = Path("./projects")
            if projects_dir.exists():
                # Find the current project (assume most recent)
                project_dirs = [d for d in projects_dir.iterdir() if d.is_dir()]
                if project_dirs:
                    # Sort by modification time, get most recent
                    current_project = max(project_dirs, key=lambda p: p.stat().st_mtime)
                    videos_dir = current_project / "videos" / f"scene_{scene_num}"
                    videos_dir.mkdir(parents=True, exist_ok=True)
                    output_file = videos_dir / Path(output_file).name
                    print(f"📁 Saving to project directory: {current_project.name}")
else:
    output_file = "downloaded_video.mp4"

print(f"📥 Downloading video from: {video_uri}")
print(f"💾 Saving to: {output_file}")

try:
    # Download with API key
    headers = {
        "x-goog-api-key": api_key
    }

    response = requests.get(video_uri, headers=headers, stream=True)
    response.raise_for_status()

    # Save to file
    with open(output_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    file_size = os.path.getsize(output_file)
    print(f"✅ Successfully downloaded video ({file_size:,} bytes)")
    print(f"📁 Saved to: {Path(output_file).absolute()}")

except requests.exceptions.HTTPError as e:
    print(f"❌ HTTP Error {e.response.status_code}: {e.response.reason}")
    if e.response.status_code == 400:
        print("This might mean:")
        print("  - The API key is invalid or missing permissions")
        print("  - The download URL has expired")
    elif e.response.status_code == 403:
        print("Permission denied. Your API key might need Cloud Storage permissions.")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
