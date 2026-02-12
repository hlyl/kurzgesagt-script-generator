"""Google Drive uploader for video files."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from ..utils import get_logger

logger = get_logger("google_drive")

# If modifying these scopes, delete the token file.
SCOPES = ['https://www.googleapis.com/auth/drive.file']


class GoogleDriveUploadError(RuntimeError):
    """Raised when Google Drive upload fails."""


class GoogleDriveUploader:
    """Upload videos to Google Drive.

    Handles authentication and uploading of video files to a specified
    Google Drive folder.
    """

    def __init__(
        self,
        credentials_path: Optional[Path] = None,
        token_path: Optional[Path] = None,
        folder_id: Optional[str] = None
    ):
        """Initialize Google Drive uploader.

        Args:
            credentials_path: Path to OAuth2 credentials JSON file
            token_path: Path to store/load token (default: token.json)
            folder_id: Google Drive folder ID to upload to

        Raises:
            GoogleDriveUploadError: If credentials are not provided or invalid
        """
        self.credentials_path = credentials_path
        self.token_path = token_path or Path("token.json")
        self.folder_id = folder_id
        self.service = None

        if not self.credentials_path or not Path(self.credentials_path).exists():
            logger.warning(
                "Google Drive credentials not found. "
                "Videos will be saved locally only."
            )
        else:
            self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google Drive API.

        Uses OAuth2 flow to get credentials. Will open browser for first-time
        authentication and save token for future use.

        Raises:
            GoogleDriveUploadError: If authentication fails
        """
        creds = None

        # Load existing token if available
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path), SCOPES
                )
            except Exception as e:
                logger.warning(f"Failed to load existing token: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Failed to refresh token: {e}")
                    creds = None

            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    raise GoogleDriveUploadError(
                        f"Failed to authenticate with Google Drive: {e}"
                    ) from e

            # Save credentials for next run
            try:
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
            except Exception as e:
                logger.warning(f"Failed to save token: {e}")

        # Build Drive service
        try:
            self.service = build('drive', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Drive")
        except Exception as e:
            raise GoogleDriveUploadError(
                f"Failed to build Drive service: {e}"
            ) from e

    def upload_video(
        self,
        video_path: Path,
        folder_name: Optional[str] = None,
        file_name: Optional[str] = None
    ) -> str:
        """Upload video file to Google Drive.

        Args:
            video_path: Path to local video file
            folder_name: Optional subfolder name within the configured folder
            file_name: Optional custom filename (defaults to original filename)

        Returns:
            Google Drive file ID of uploaded video

        Raises:
            GoogleDriveUploadError: If upload fails
        """
        if not self.service:
            raise GoogleDriveUploadError(
                "Google Drive not authenticated. Check credentials configuration."
            )

        if not video_path.exists():
            raise GoogleDriveUploadError(f"Video file not found: {video_path}")

        try:
            # Determine target folder
            parent_folder_id = self.folder_id

            # Create subfolder if specified
            if folder_name:
                parent_folder_id = self._get_or_create_folder(
                    folder_name, parent_folder_id
                )

            # Prepare file metadata
            file_metadata = {
                'name': file_name or video_path.name,
                'mimeType': 'video/mp4'
            }

            if parent_folder_id:
                file_metadata['parents'] = [parent_folder_id]

            # Upload file
            media = MediaFileUpload(
                str(video_path),
                mimetype='video/mp4',
                resumable=True
            )

            logger.info(f"Uploading {video_path.name} to Google Drive...")

            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,name,webViewLink'
            ).execute()

            file_id = file.get('id')
            web_link = file.get('webViewLink', 'N/A')

            logger.info(
                f"Successfully uploaded {video_path.name} "
                f"(ID: {file_id}, Link: {web_link})"
            )

            return file_id

        except Exception as e:
            raise GoogleDriveUploadError(
                f"Failed to upload {video_path.name}: {e}"
            ) from e

    def _get_or_create_folder(
        self,
        folder_name: str,
        parent_id: Optional[str] = None
    ) -> str:
        """Get or create a folder in Google Drive.

        Args:
            folder_name: Name of folder to get or create
            parent_id: Parent folder ID (None for root)

        Returns:
            Folder ID

        Raises:
            GoogleDriveUploadError: If folder creation fails
        """
        try:
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if parent_id:
                query += f" and '{parent_id}' in parents"

            results = self.service.files().list(
                q=query,
                spaces='drive',
                fields='files(id, name)'
            ).execute()

            folders = results.get('files', [])

            if folders:
                folder_id = folders[0]['id']
                logger.debug(f"Found existing folder: {folder_name} (ID: {folder_id})")
                return folder_id

            # Create new folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }

            if parent_id:
                file_metadata['parents'] = [parent_id]

            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()

            folder_id = folder.get('id')
            logger.info(f"Created folder: {folder_name} (ID: {folder_id})")
            return folder_id

        except Exception as e:
            raise GoogleDriveUploadError(
                f"Failed to get or create folder {folder_name}: {e}"
            ) from e

    def get_file_link(self, file_id: str) -> str:
        """Get shareable link for a file.

        Args:
            file_id: Google Drive file ID

        Returns:
            Shareable web link URL

        Raises:
            GoogleDriveUploadError: If retrieval fails
        """
        if not self.service:
            raise GoogleDriveUploadError("Google Drive not authenticated")

        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='webViewLink'
            ).execute()

            return file.get('webViewLink', '')

        except Exception as e:
            raise GoogleDriveUploadError(
                f"Failed to get file link for {file_id}: {e}"
            ) from e

    def is_configured(self) -> bool:
        """Check if Google Drive is properly configured.

        Returns:
            True if authenticated and ready to upload
        """
        return self.service is not None
