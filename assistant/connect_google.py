import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from assistant.data.db import connect
from assistant.data.store import UserStore

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def main():
    owner_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not owner_id:
        print("usage: python -m assistant.connect_google <owner_id>")
        return
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
    creds = flow.run_local_server(port=0)
    conn = connect()
    UserStore(conn, owner_id).save_credential("google_calendar", creds.to_json())
    print(f"Stored Google Calendar credentials for owner {owner_id}.")


if __name__ == "__main__":
    main()
