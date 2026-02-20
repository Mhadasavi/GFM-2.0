import os
import json
import logging
from typing import Generator, Dict, Any, Optional
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive.metadata.readonly"]

logger = logging.getLogger(__name__)


class DriveClient:
    def __init__(self, credentials_path: str, token_path: str):
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._authenticate()

    def _authenticate(self):
        creds = None

        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Ensure credentials directory exists
            os.makedirs(os.path.dirname(self.token_path), exist_ok=True)
            with open(self.token_path, "w") as token:
                token.write(creds.to_json())

        logger.info(json.dumps({"event": "drive_auth_success"}))
        return build("drive", "v3", credentials=creds)

    def list_files(
        self,
        query: str,
        fields: Optional[str] = None,
        page_size: int = 1000,
    ) -> Generator[Dict[str, Any], None, None]:

        fields = fields or "nextPageToken, files(id,name,mimeType,md5Checksum,size,modifiedTime,parents)"

        page_token = None

        while True:
            try:
                response = (
                    self.service.files()
                    .list(
                        q=query,
                        spaces="drive",
                        fields=fields,
                        pageSize=page_size,
                        pageToken=page_token,
                    )
                    .execute()
                )

                for file in response.get("files", []):
                    yield file

                page_token = response.get("nextPageToken")
                if not page_token:
                    break

            except HttpError as error:
                logger.error(json.dumps({
                    "event": "drive_api_error",
                    "error": str(error)
                }))
                raise
