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

    # Third-party credentials

    def save_credential(self, provider: str, token_plaintext: str) -> None:
        from assistant.secrets_box import encrypt
        enc = encrypt(token_plaintext)
        self.conn.execute(
            "INSERT INTO credentials (owner_id, provider, token) VALUES (%s, %s, %s) "
            "ON CONFLICT (owner_id, provider) DO UPDATE SET token = EXCLUDED.token",
            (self.owner_id, provider, enc),
        )

    def get_credential(self, provider: str) -> str | None:
        from assistant.secrets_box import decrypt
        cur = self.conn.execute(
            "SELECT token FROM credentials WHERE owner_id = %s AND provider = %s",
            (self.owner_id, provider),
        )
        row = cur.fetchone()
        if not row:
            return None
        return decrypt(bytes(row[0]))

    # Transactions

    def add_transactions(self, source: str, txns: list[dict]) -> int:
        added = 0
        for t in txns:
            cur = self.conn.execute(
                "INSERT INTO transactions (owner_id, source, external_id, date, name, amount) "
                "VALUES (%s, %s, %s, %s, %s, %s) "
                "ON CONFLICT (owner_id, external_id) DO NOTHING RETURNING id",
                (self.owner_id, source, t["external_id"], t["date"], t["name"], t["amount"]),
            )
            if cur.fetchone():
                added += 1
        return added

    def get_uncategorized(self) -> list[dict]:
        cur = self.conn.execute(
            "SELECT id, name FROM transactions WHERE owner_id = %s AND category IS NULL",
            (self.owner_id,),
        )
        return [{"id": str(i), "name": n} for i, n in cur.fetchall()]

    def set_category(self, txn_id: str, category: str) -> None:
        self.conn.execute(
            "UPDATE transactions SET category = %s WHERE owner_id = %s AND id = %s",
            (category, self.owner_id, txn_id),
        )

    # Merchant rules

    def get_merchant_rule(self, merchant_key: str) -> str | None:
        cur = self.conn.execute(
            "SELECT category FROM merchant_rules WHERE owner_id = %s AND merchant_key = %s",
            (self.owner_id, merchant_key),
        )
        row = cur.fetchone()
        return row[0] if row else None

    def add_merchant_rule(self, merchant_key: str, category: str) -> None:
        self.conn.execute(
            "INSERT INTO merchant_rules (owner_id, merchant_key, category) VALUES (%s, %s, %s) "
            "ON CONFLICT (owner_id, merchant_key) DO NOTHING",
            (self.owner_id, merchant_key, category),
        )

    # Finance aggregations

    def spending_by_category(self, start=None, end=None) -> list[dict]:
        sql = ("SELECT COALESCE(category, 'uncategorized'), SUM(amount) "
               "FROM transactions WHERE owner_id = %s AND amount > 0")
        params = [self.owner_id]
        if start:
            sql += " AND date >= %s"; params.append(start)
        if end:
            sql += " AND date <= %s"; params.append(end)
        sql += " GROUP BY 1 ORDER BY 2 DESC"
        cur = self.conn.execute(sql, tuple(params))
        return [{"category": c, "total": float(t)} for c, t in cur.fetchall()]

    def spending_by_month(self, months: int = 6) -> list[dict]:
        cur = self.conn.execute(
            "SELECT to_char(date, 'YYYY-MM') AS m, SUM(amount) "
            "FROM transactions WHERE owner_id = %s AND amount > 0 "
            "GROUP BY m ORDER BY m DESC LIMIT %s",
            (self.owner_id, months),
        )
        rows = [{"month": m, "total": float(t)} for m, t in cur.fetchall()]
        return list(reversed(rows))

    # Decisions

    def add_decision(self, idea: str, verdict: str, reasoning: str) -> None:
        self.conn.execute(
            "INSERT INTO decisions (owner_id, idea, verdict, reasoning) VALUES (%s, %s, %s, %s)",
            (self.owner_id, idea, verdict, reasoning),
        )

    def get_decisions(self, limit: int = 50) -> list[dict]:
        cur = self.conn.execute(
            "SELECT idea, verdict, reasoning, created_at FROM decisions "
            "WHERE owner_id = %s ORDER BY created_at DESC LIMIT %s",
            (self.owner_id, limit),
        )
        return [{"idea": i, "verdict": v, "reasoning": r, "created_at": t}
                for i, v, r, t in cur.fetchall()]

    # Audit log

    def add_audit(self, action: str, detail: str = "") -> None:
        self.conn.execute(
            "INSERT INTO audit_log (owner_id, action, detail) VALUES (%s, %s, %s)",
            (self.owner_id, action, detail),
        )

    def get_audit(self, limit: int = 50) -> list[dict]:
        cur = self.conn.execute(
            "SELECT action, detail, created_at FROM audit_log "
            "WHERE owner_id = %s ORDER BY created_at DESC LIMIT %s",
            (self.owner_id, limit),
        )
        return [{"action": a, "detail": d, "created_at": t} for a, d, t in cur.fetchall()]
