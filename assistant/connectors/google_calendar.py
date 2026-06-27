import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GoogleCalendarClient:
    def __init__(self, token_json: str):
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
        self.service = build("calendar", "v3", credentials=creds)

    def create_event(self, title, start_iso, end_iso, timezone, description=None):
        body = {
            "summary": title,
            "description": description or "",
            "start": {"dateTime": start_iso, "timeZone": timezone},
            "end": {"dateTime": end_iso, "timeZone": timezone},
        }
        created = self.service.events().insert(calendarId="primary", body=body).execute()
        return created.get("htmlLink", "event created")

    def create_all_day(self, title, start_date, end_date, description=None):
        body = {
            "summary": title,
            "description": description or "",
            "start": {"date": start_date},
            "end": {"date": end_date},
        }
        created = self.service.events().insert(calendarId="primary", body=body).execute()
        return created.get("htmlLink", "event created")
