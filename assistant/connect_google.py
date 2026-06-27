import sys
from google_auth_oauthlib.flow import InstalledAppFlow
from assistant.data.db import connect
from assistant.data.store import UserStore

SERVICES = {
    "calendar": {
        "scopes": ["https://www.googleapis.com/auth/calendar.events"],
        "key": "google_calendar",
    },
    "gmail": {
        "scopes": ["https://www.googleapis.com/auth/gmail.readonly"],
        "key": "gmail",
    },
}


def main():
    owner_id = sys.argv[1] if len(sys.argv) > 1 else None
    service = sys.argv[2] if len(sys.argv) > 2 else "calendar"
    if not owner_id or service not in SERVICES:
        print("usage: python -m assistant.connect_google <owner_id> [calendar|gmail]")
        return
    cfg = SERVICES[service]
    flow = InstalledAppFlow.from_client_secrets_file("credentials.json", cfg["scopes"])
    creds = flow.run_local_server(port=0)
    conn = connect()
    UserStore(conn, owner_id).save_credential(cfg["key"], creds.to_json())
    print(f"Stored {service} credentials for owner {owner_id}.")


if __name__ == "__main__":
    main()
