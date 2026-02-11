# Audio Duration and Transition Updates

## Overview
This document summarizes the changes made to ensure audio generation updates shot/scene durations and transition breaks in the project_config.yaml with decimal precision.

## Changes Made

### 1. Shot Model Updates (`src/kurzgesagt/models/scene.py`)
- **Duration field**: Changed from `int` to `float` to support decimal precision
  - `duration: int` → `duration: float = Field(..., ge=0.1, le=60.0)`
  - Now stores actual audio duration in seconds with decimal precision
- **New field**: Added `transition_duration: float`
  - Default: 0.5 seconds
  - Range: 0.0 to 5.0 seconds
  - Represents transition time to the next shot

### 2. Scene Model Updates (`src/kurzgesagt/models/scene.py`)
- **Duration field**: Changed from `int` to `float`
  - `duration: int` → `duration: float = Field(..., ge=0.1)`
  - Stores actual scene duration in seconds
- **New field**: Added `transition_duration: float`
  - Default: 1.0 second
  - Range: 0.0 to 5.0 seconds
  - Represents transition time to the next scene
- **Updated `calculate_duration()` method**: Now returns `float` and includes transition durations
  - Sums all shot durations + their transitions (except last shot's transition)

### 3. ProjectConfig Model Updates (`src/kurzgesagt/models/project.py`)
- **Updated `total_duration` property**: Now returns `float`
  - Includes all scene durations + scene transitions
  - Excludes the last scene's transition duration

### 4. AudioGenerator Updates (`src/kurzgesagt/core/audio_generator.py`)
- **Added pydub support**: Optional import for calculating actual audio duration
  - Falls back to text-length estimation if pydub unavailable
- **Updated return types**: All audio generation methods now return `Tuple[Path, float]`
  - Returns both the file path and actual audio duration
  - Methods affected:
    - `save_audio()` → `Tuple[Path, float]`
    - `generate_scene_audio()` → `Tuple[Path, float]`
    - `generate_shot_audio()` → `Tuple[Path, float]`
- **Duration calculation**:
  - **With pydub**: Reads actual MP3 duration using `AudioSegment.from_mp3()`
  - **Without pydub**: Estimates ~2.5 words per second

### 5. ProjectManager Updates (`src/kurzgesagt/core/project_manager.py`)
Added three new methods for updating durations and transitions:

#### `update_shot_duration(project_name, scene_number, shot_number, actual_duration)`
- Updates a specific shot's duration with actual audio duration
- Automatically recalculates scene duration
- Saves updated project_config.yaml

#### `update_scene_duration(project_name, scene_number, actual_duration)`
- Updates a specific scene's duration
- Saves updated project_config.yaml

#### `update_transition_durations(project_name, shot_transition=0.5, scene_transition=1.0)`
- Updates all shot and scene transition durations in the project
- Useful for applying consistent transitions across the project
- Saves updated project_config.yaml

### 6. ScriptGenerator Updates (`src/kurzgesagt/core/script_generator.py`)
- **Updated `_format_duration()` method**: Now accepts `float` instead of `int`
  - Converts to int internally for MM:SS formatting

## Usage Example

```python
from pathlib import Path
from src.kurzgesagt.core import AudioGenerator, ProjectManager

# Initialize
audio_gen = AudioGenerator(api_key="your_key")
pm = ProjectManager()

# Generate audio and get actual duration
project_dir = Path("projects/my_project")
audio_path, actual_duration = audio_gen.generate_shot_audio(
    project_dir=project_dir,
    scene_number=1,
    shot_number=1,
    narration="This is the first shot narration"
)

# Update project config with actual duration
pm.update_shot_duration(
    project_name="my_project",
    scene_number=1,
    shot_number=1,
    actual_duration=actual_duration
)

# Set transition durations
pm.update_transition_durations(
    project_name="my_project",
    shot_transition=0.5,  # 0.5s between shots
    scene_transition=1.0  # 1.0s between scenes
)
```

## Project Config YAML Structure

The project_config.yaml now includes decimal durations and transition data:

```yaml
scenes:
  - number: 1
    title: INTRODUCTION
    purpose: Introduce the topic
    duration: 15.3  # Actual total duration in seconds (decimal)
    transition_duration: 1.0  # Transition to next scene
    shots:
      - number: 1
        narration: "Welcome to our video..."
        duration: 7.2  # Actual audio duration (decimal)
        transition_duration: 0.5  # Transition to next shot
        description: Opening shot
        image_prompt: "..."
        video_prompt: "..."
        key_elements: []
      - number: 2
        narration: "Today we'll explore..."
        duration: 8.1  # Actual audio duration (decimal)
        transition_duration: 0.5  # Transition to next shot
        # ...
```

## Benefits

1. **Precision**: Decimal durations provide accurate timing (e.g., 7.35 seconds instead of just 7)
2. **Synchronization**: Actual audio durations ensure video and audio are perfectly synced
3. **Editing**: Transition durations help editors plan smooth scene/shot transitions
4. **Timeline**: Accurate durations enable precise timeline generation for video editing software
5. **Automation**: Audio generation automatically updates the project config with real durations

## Testing Updates

- Updated all audio generation tests to handle new tuple return type
- All tests passing with 82.40% coverage
- Tests verify both path and duration are returned correctly

## Backward Compatibility

**Breaking Changes**:
- Shot.duration: `int` → `float`
- Scene.duration: `int` → `float`
- Audio generation methods now return tuples instead of just Path
- Existing project_config.yaml files with integer durations will need migration

## Dependencies

- Added optional `pydub` dependency for accurate audio duration calculation
- Falls back gracefully if pydub not available
- Requires `ffmpeg` or `libav` for pydub to work with MP3 files

## UI Integration (Completed)

The Streamlit UI has been fully integrated with automatic duration updates. All four audio generation functions in `src/kurzgesagt/ui/app.py` now automatically update the project configuration with actual audio durations:

### 1. **generate_full_audio()** (Lines 1511-1558)
- Generates combined audio with timeline data
- Updates shot durations in real-time during generation
- Continues processing even if individual duration updates fail

### 2. **generate_audio_by_scene()** (Lines 1654-1672)
- Generates separate audio files per scene
- Updates scene durations with actual audio length
- Displays warnings for any update failures

### 3. **generate_audio_by_shot()** (Lines 1710-1755)
- Generates individual shot audio files
- Updates shot durations and recalculates scene durations
- Shows warnings if config updates fail

### 4. **generate_selected_audio()** (Lines 1774-1819)
- Handles both scene and shot selection
- Updates appropriate durations based on item type
- Displays actual duration in success message (e.g., "duration: 7.35s")

### Error Handling
All UI functions include try-catch blocks around duration updates to ensure:
- Audio generation succeeds even if config update fails
- User is notified of any update issues via warnings
- Batch operations continue processing remaining items

### User Feedback
- Success messages now include actual duration for selected audio generation
- Warnings displayed if project config cannot be updated
- Timeline data includes precise durations for video editing software

## Next Steps

1. Consider adding a migration script for existing projects with integer durations
2. Add duration validation to ensure audio matches planned timing
3. Consider displaying duration comparison (estimated vs. actual) in UI
