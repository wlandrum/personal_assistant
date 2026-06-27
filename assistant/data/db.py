import os
import psycopg
from pgvector.psycopg import register_vector
from dotenv import load_dotenv

load_dotenv()


def connect() -> psycopg.Connection:
    url = os.environ["DATABASE_URL"]
    conn = psycopg.connect(url, autocommit=True)
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def apply_schema(conn: psycopg.Connection, schema_path: str = "assistant/data/schema.sql") -> None:
    with open(schema_path) as f:
        conn.execute(f.read())
