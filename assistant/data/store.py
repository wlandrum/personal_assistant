import numpy as np
import psycopg


class UserStore:
    def __init__(self, conn: psycopg.Connection, owner_id: str):
        if not owner_id:
            raise ValueError("UserStore requires an owner_id")
        self.conn = conn
        self.owner_id = owner_id

    # Facts

    def add_fact(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO facts (owner_id, key, value) VALUES (%s, %s, %s)",
            (self.owner_id, key, value),
        )

    def get_active_facts(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT key, value FROM facts "
            "WHERE owner_id = %s AND status = 'active' "
            "ORDER BY created_at",
            (self.owner_id,),
        )
        return [{"key": k, "value": v} for k, v in cur.fetchall()]

    def supersede_fact(self, key: str, new_value: str) -> None:
        self.conn.execute(
            "UPDATE facts SET status = 'superseded', superseded_at = now() "
            "WHERE owner_id = %s AND key = %s AND status = 'active'",
            (self.owner_id, key),
        )
        self.add_fact(key, new_value)

    # Episodes

    def add_episode(self, summary: str, embedding: list[float]) -> None:
        self.conn.execute(
            "INSERT INTO episodes (owner_id, summary, embedding) VALUES (%s, %s, %s)",
            (self.owner_id, summary, np.array(embedding, dtype=np.float32)),
        )

    def search_episodes(self, query_embedding: list[float], k: int = 5) -> list[dict]:
        cur = self.conn.execute(
            "SELECT summary, created_at FROM episodes "
            "WHERE owner_id = %s "
            "ORDER BY embedding <=> %s "
            "LIMIT %s",
            (self.owner_id, np.array(query_embedding, dtype=np.float32), k),
        )
        return [{"summary": s, "created_at": c} for s, c in cur.fetchall()]
