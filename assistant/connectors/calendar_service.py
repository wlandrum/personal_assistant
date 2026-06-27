from datetime import date, timedelta
from assistant.data.store import UserStore
from assistant.connectors.google_calendar import GoogleCalendarClient


def _client_for(conn, owner_id):
    token = UserStore(conn, owner_id).get_credential("google_calendar")
    if not token:
        return None
    return GoogleCalendarClient(token)


def create_timed_event(conn, settings, owner_id, title, start_iso, end_iso, description=""):
    client = _client_for(conn, owner_id)
    if client is None:
        return None
    return client.create_event(title, start_iso, end_iso, settings.timezone, description)


def create_all_day_event(conn, settings, owner_id, title, day_iso, description=""):
    client = _client_for(conn, owner_id)
    if client is None:
        return None
    end_day = (date.fromisoformat(day_iso) + timedelta(days=1)).isoformat()
    return client.create_all_day(title, day_iso, end_day, description)
