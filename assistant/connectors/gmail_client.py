import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _header(headers, name):
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


class GoogleGmailClient:
    def __init__(self, token_json: str):
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        self.service = build("gmail", "v1", credentials=creds)

    def list_recent(self, max_results: int = 20) -> list[str]:
        resp = self.service.users().messages().list(
            userId="me", labelIds=["INBOX"], maxResults=max_results
        ).execute()
        return [m["id"] for m in resp.get("messages", [])]

    def get_message(self, message_id: str) -> dict:
        msg = self.service.users().messages().get(
            userId="me", id=message_id, format="metadata",
            metadataHeaders=["From", "Subject", "Date"],
        ).execute()
        headers = msg.get("payload", {}).get("headers", [])
        return {
            "id": message_id,
            "from": _header(headers, "From"),
            "subject": _header(headers, "Subject"),
            "date": _header(headers, "Date"),
            "snippet": msg.get("snippet", ""),
        }
