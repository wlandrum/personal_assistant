import sys
import secrets
import hashlib
from assistant.data.db import connect, apply_schema


def main():
    owner_id = sys.argv[1] if len(sys.argv) > 1 else None
    if not owner_id:
        print("usage: python -m assistant.mint_token <owner_id>")
        return
    conn = connect()
    apply_schema(conn)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    conn.execute(
        "INSERT INTO api_tokens (owner_id, token_hash) VALUES (%s, %s)",
        (owner_id, token_hash),
    )
    print("Token for owner", owner_id)
    print("Save this now, it will not be shown again:")
    print(token)


if __name__ == "__main__":
    main()
