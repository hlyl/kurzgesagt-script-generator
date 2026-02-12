# Google Drive Integration Setup Guide

This guide explains how to set up automatic Google Drive uploads for videos generated using Gemini's Veo 3.1.

## Overview

When enabled, videos generated from images will be:
1. Generated using Gemini's Veo 3.1 API
2. Temporarily saved locally (for upload)
3. **Automatically uploaded to Google Drive**
4. Organized in folders by scene (e.g., `scene_01`, `scene_02`)
5. Optionally deleted from your machine (Cloud-Only Mode)

You'll get clickable Google Drive links in the UI for easy access to your videos in the cloud.

### Two Modes:
- **Cloud-Only Mode**: Videos uploaded to Drive, local copies deleted (saves disk space)
- **Hybrid Mode**: Videos kept both locally and in Drive (backup + local access)

## Prerequisites

- Google account with access to Google Drive
- Google Cloud project with Drive API enabled
- Videos can be kept locally or deleted after upload (your choice)

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the **Google Drive API**:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

## Step 2: Create OAuth2 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless you have a Google Workspace)
   - Fill in the required app information
   - Add your email as a test user
4. Choose "Desktop app" as the application type
5. Download the JSON file and save it as `credentials.json` in your project root

## Step 3: Get Your Drive Folder ID

1. Create a folder in Google Drive where you want videos uploaded
2. Open the folder and copy the folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
   ```
3. Copy the `FOLDER_ID_HERE` part

## Step 4: Configure Environment Variables

Edit your `.env` file and add these settings:

```bash
# Google Drive Settings (optional - for automatic video uploads)
GOOGLE_DRIVE_ENABLED=true
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_from_step_3
GOOGLE_DRIVE_CREDENTIALS_PATH=./credentials.json
GOOGLE_DRIVE_TOKEN_PATH=token.json
GOOGLE_DRIVE_KEEP_LOCAL_COPY=false
```

### Configuration Options:

- **GOOGLE_DRIVE_ENABLED**: Set to `true` to enable automatic uploads
- **GOOGLE_DRIVE_FOLDER_ID**: The folder ID from Step 3
- **GOOGLE_DRIVE_CREDENTIALS_PATH**: Path to your OAuth2 credentials JSON file
- **GOOGLE_DRIVE_TOKEN_PATH**: Where to save the authentication token (default: `token.json`)
- **GOOGLE_DRIVE_KEEP_LOCAL_COPY**: Set to `false` to delete local videos after Drive upload (default: `false`)

### Storage Options

**Cloud-Only Mode** (Recommended for limited disk space):
```bash
GOOGLE_DRIVE_KEEP_LOCAL_COPY=false
```
- Videos generated and uploaded to Drive
- Local files deleted after successful upload
- Access videos only through Google Drive links
- Saves disk space on your machine

**Hybrid Mode** (Keep both local and cloud copies):
```bash
GOOGLE_DRIVE_KEEP_LOCAL_COPY=true
```
- Videos saved locally AND uploaded to Drive
- Best of both worlds: local access + cloud backup
- Requires more disk space

## Step 5: First-Time Authentication

The first time you generate a video with Drive enabled:

1. A browser window will open automatically
2. Sign in to your Google account
3. Grant the app permission to access your Google Drive
4. The authentication token will be saved to `token.json`
5. Future uploads will use this token automatically

## Step 6: Install Dependencies

Make sure to install the required Google Drive dependencies:

```bash
pip install -e .
```

Or if using uv:

```bash
uv sync
```

## Usage

Once configured, video uploads happen automatically:

### Generate Videos

1. Go to the **🎥 Img2Video** tab
2. Click any video generation button:
   - "🎬 Generate All Videos"
   - "🎞️ Generate by Scene"
   - "🎥 Generate First Video"
   - Or select individual shots

### Results

When videos are generated:
- ✅ Video generation confirmation
- ☁️ Google Drive upload confirmation
- 📎 Clickable links to open videos directly in Google Drive
- 📁 Local save notification (only if `GOOGLE_DRIVE_KEEP_LOCAL_COPY=true`)
- Videos organized in Drive folders by scene

### Example Output

**Cloud-Only Mode:**
```
✅ Generated 5 videos!
☁️ Uploaded 5 videos to Google Drive!
📎 Google Drive Links
Scene 1 Shot 1: Open in Drive
Scene 1 Shot 2: Open in Drive
...
```

**Hybrid Mode:**
```
✅ Generated 5 videos!
☁️ Uploaded 5 videos to Google Drive!
📎 Google Drive Links
Scene 1 Shot 1: Open in Drive
...
📁 Local videos saved to: /path/to/project/videos
```

## Folder Structure in Google Drive

Videos are automatically organized:

```
Your Drive Folder/
├── scene_01/
│   ├── shot_01.mp4
│   ├── shot_02.mp4
│   └── shot_03.mp4
├── scene_02/
│   ├── shot_01.mp4
│   └── shot_02.mp4
└── ...
```

## Troubleshooting

### Authentication Issues

**Problem**: Browser doesn't open for authentication
- **Solution**: Check that you're running the app on a machine with a web browser. For remote servers, you may need to manually copy the authentication URL.

**Problem**: "Access blocked" error
- **Solution**: Make sure your email is added as a test user in the OAuth consent screen.

### Upload Failures

**Problem**: Videos generate but don't upload
- **Solution**: Check the logs for specific errors. Ensure `GOOGLE_DRIVE_ENABLED=true` in your `.env` file.

**Problem**: "Folder not found" error
- **Solution**: Verify the folder ID is correct and the authenticated account has access to the folder.

### Token Expired

If your token expires:
1. Delete `token.json`
2. Generate a video again to re-authenticate
3. Sign in when the browser opens

## Disabling Google Drive Uploads

To disable automatic uploads (videos will only save locally):

1. Edit `.env`:
   ```bash
   GOOGLE_DRIVE_ENABLED=false
   ```

2. Or remove the Google Drive configuration entirely

## Security Notes

- Never commit `credentials.json` or `token.json` to version control
- Add them to `.gitignore`:
  ```
  credentials.json
  token.json
  ```
- The OAuth2 credentials have limited scope (only file creation/management)
- Videos saved locally serve as backups if Drive uploads fail

## Benefits

1. **Cloud Storage**: Videos stored safely in Google Drive
2. **Save Disk Space**: Optional cloud-only mode deletes local files
3. **Easy Sharing**: Get shareable Drive links instantly
4. **Organization**: Automatic folder structure by scene
5. **Accessibility**: Access videos from any device
6. **No Manual Work**: Set it up once, uploads happen automatically
7. **Flexible**: Choose between cloud-only or hybrid mode

## Additional Features

- Optional local backup (Hybrid Mode)
- Automatic cleanup (Cloud-Only Mode)
- Upload errors don't stop video generation
- Drive links are clickable in the UI
- Progress tracking shows Drive upload status
- Failed uploads are reported clearly

## Support

If you encounter issues:
1. Check the application logs for detailed error messages
2. Verify your Google Cloud project settings
3. Ensure all environment variables are correctly set
4. Make sure the Google Drive API is enabled in your project

For more help, check the main project README or open an issue.
