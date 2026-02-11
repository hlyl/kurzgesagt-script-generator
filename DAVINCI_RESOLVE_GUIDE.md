# DaVinci Resolve Integration - Usage Guide

## Overview
The Kurzgesagt Script Generator now includes automated DaVinci Resolve export functionality. This feature generates industry-standard import files that can be used to automatically set up video editing timelines with precise timing, scene markers, and organized media bins.

## Features

### 1. **EDL Export (CMX 3600)**
- Industry-standard Edit Decision List format
- Simple text-based cut list
- Perfect for basic timeline structure and audio sync
- Compatible with all major video editing software

### 2. **FCPXML Export**
- Advanced XML format with rich metadata
- Includes scene markers at transitions
- Organizes media into bins by scene
- Contains shot information and timing data
- Compatible with DaVinci Resolve, Final Cut Pro, and Premiere Pro

### 3. **Resolve Python Script**
- Direct automation using DaVinci Resolve API
- Creates project, imports media, and builds timeline automatically
- Adds markers at scene boundaries
- Organizes media pool by scene structure
- Requires DaVinci Resolve to be running

## Workflow

### Step 1: Generate Timeline Data
1. Create or load a project in the Streamlit UI
2. Add your voice-over script in the **Script** tab
3. Parse the script into scenes
4. Generate images for your shots (at least the first image for testing)
5. Go to the **Audio** tab
6. Configure pause durations:
   - Break between sections (scenes): 0-5 seconds
   - Break between shots: 0-3 seconds
7. Click **"Generate Full Audio"**
   - This creates `full_narration.mp3` with precise timing
   - Also creates `timeline_timestamps.json` with frame-accurate data

### Step 2: Export for DaVinci Resolve
In the **Audio** tab, scroll to the **"DaVinci Resolve Export"** section:

#### Option A: EDL Export (Recommended for beginners)
1. Click **"Export EDL"**
2. Download the `.edl` file
3. Import into DaVinci Resolve:
   - File → Import → Timeline → EDL
   - Select the downloaded EDL file
   - Choose import options

#### Option B: FCPXML Export (Best for organization)
1. Click **"Export FCPXML"**
2. Download the `.fcpxml` file
3. Import into DaVinci Resolve:
   - File → Import → Timeline → Final Cut Pro XML
   - Select the downloaded FCPXML file
   - Media will be organized into scene bins
   - Scene markers will be added automatically

#### Option C: Python Script (Advanced)
1. Click **"Generate Resolve Script"**
2. Download the `_resolve.py` file
3. Copy the script to your project's audio directory
4. Make sure DaVinci Resolve is running
5. Run: `python3 <project_name>_resolve.py`
6. The script will:
   - Create a new project
   - Import audio and images
   - Organize media by scene
   - Add markers at scene transitions

## File Structure

After generation, your project directory will look like:

```
projects/<project_name>/
├── audio/
│   ├── full_narration.mp3           # Complete audio with pauses
│   └── timeline_timestamps.json     # Timing data
├── images/
│   └── scene_01/
│       ├── shot_01.png              # Scene images
│       └── shot_02.png
└── exports/<project_name>/          # Export directory
    ├── <project_name>.edl           # EDL file
    ├── <project_name>.fcpxml        # FCPXML file
    └── <project_name>_resolve.py    # Python script
```

## Timeline Data Format

The `timeline_timestamps.json` contains:
```json
{
  "project_name": "example_project",
  "total_duration_ms": 45230,
  "total_duration_timecode": "00:00:45:06",
  "fps": 30,
  "settings": {
    "tts_model": "tts-1",
    "tts_voice": "alloy",
    "tts_speed": 1.0,
    "shot_pause_seconds": 1.0,
    "section_pause_seconds": 2.0
  },
  "scenes": [
    {
      "scene_number": 1,
      "scene_title": "Introduction",
      "start_ms": 0,
      "end_ms": 12450,
      "start_timecode": "00:00:00:00",
      "end_timecode": "00:00:12:13",
      "shots": [
        {
          "shot_number": 1,
          "start_ms": 0,
          "end_ms": 5230,
          "duration_ms": 5230,
          "start_timecode": "00:00:00:00",
          "end_timecode": "00:00:05:06",
          "narration_preview": "Welcome to..."
        }
      ]
    }
  ]
}
```

## Tips and Best Practices

### Audio Generation
- Use appropriate pause durations for your content style
- Shorter pauses (0.5-1s) for fast-paced content
- Longer pauses (2-3s) for educational/contemplative content
- Preview the script with pauses before generating

### Image Generation
- Generate at least first image to test the workflow
- Images should be generated before exporting to Resolve
- Image filenames must match scene/shot numbering

### DaVinci Resolve Import
- **EDL**: Best for simple projects, easy to import
- **FCPXML**: Best for complex projects, includes markers and bins
- **Python Script**: Best for automation, requires Resolve API setup

### Troubleshooting
- **Timeline data not found**: Generate full audio first
- **Media not found in Resolve**: Check image paths match
- **Python script fails**: Ensure DaVinci Resolve is running
- **Wrong timing**: Check FPS settings (default: 30fps)

## Advanced Features

### Custom FPS
The default framerate is 30fps. To change:
1. Edit the export functions in the UI
2. Pass custom `fps` parameter to `ResolveExporter`

### Media Organization
FCPXML automatically organizes media:
- Root folder: Audio files
- Scene bins: Images organized by scene
- Markers: Scene transitions

### Timeline Markers
Scene markers include:
- Marker name: "Scene X"
- Marker note: Scene title
- Color: Blue (default)
- Duration: 1 frame

## Future Enhancements

Planned features:
- Direct Python API integration (auto-import when Resolve running)
- Additional formats: AAF, OTIO
- Transition presets
- Color grading automation
- Batch processing
- Custom marker colors and notes
- Timeline template support

## Requirements

### Core Features
- Python 3.8+
- No additional dependencies (EDL/XML generation)

### Python Script (Optional)
- DaVinci Resolve installed (free or Studio)
- `DaVinciResolveScript` module (ships with Resolve)
- DaVinci Resolve running during script execution

## Support

For issues or questions:
- Check the logs in `logs/app.log`
- Verify timeline data exists: `projects/<name>/audio/timeline_timestamps.json`
- Test with sample data: `timeline_example.json`

## Example EDL Output

```
TITLE: example_project
FCM: NON-DROP FRAME

* MARKER: SCENE 1 - Introduction

001  AX       V     C        00:00:00:00 00:00:05:06 00:00:00:00 00:00:05:06
* FROM CLIP NAME: scene_01_shot_01.png
* NARRATION: Welcome to our video...

002  AX       V     C        00:00:00:00 00:00:06:06 00:00:06:06 00:00:12:13
* FROM CLIP NAME: scene_01_shot_02.png

003  AX       AA   C        00:00:00:00 00:00:45:06 00:00:00:00 00:00:45:06
* FROM CLIP NAME: full_narration.mp3
```

## Success Criteria

Your DaVinci Resolve integration is working when:
- ✅ EDL file imports successfully
- ✅ Audio syncs perfectly with timeline
- ✅ Scene markers appear at correct timecodes
- ✅ Timeline duration matches audio duration
- ✅ FCPXML imports with organized bins
- ✅ Python script creates project automatically

Enjoy automated video editing with DaVinci Resolve! 🎬
