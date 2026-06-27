from assistant.data.db import connect, apply_schema


def seed():
    conn = connect()
    apply_schema(conn)
    for name in ("user_a", "user_b"):
        cur = conn.execute(
            "INSERT INTO users (name) VALUES (%s) RETURNING id", (name,)
        )
        print(name, cur.fetchone()[0])


if __name__ == "__main__":
    seed()
