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

    # Notes

    def add_note(self, raw_text: str, summary: str, category: str, action_items: list[dict]) -> str:
        cur = self.conn.execute(
            "INSERT INTO notes (owner_id, raw_text, summary, category) "
            "VALUES (%s, %s, %s, %s) RETURNING id",
            (self.owner_id, raw_text, summary, category),
        )
        note_id = cur.fetchone()[0]
        for item in action_items:
            self.conn.execute(
                "INSERT INTO note_action_items (owner_id, note_id, text, due_date) "
                "VALUES (%s, %s, %s, %s)",
                (self.owner_id, note_id, item["text"], item.get("due_date")),
            )
        return str(note_id)

    def get_notes(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT id, summary, category, created_at FROM notes "
            "WHERE owner_id = %s ORDER BY created_at DESC",
            (self.owner_id,),
        )
        return [{"id": str(i), "summary": s, "category": c, "created_at": t}
                for i, s, c, t in cur.fetchall()]

    def get_action_items(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT text, due_date, done FROM note_action_items "
            "WHERE owner_id = %s ORDER BY created_at",
            (self.owner_id,),
        )
        return [{"text": t, "due_date": d, "done": dn} for t, d, dn in cur.fetchall()]
