import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Read DB info from environment
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

create_tables_sql = """
CREATE TABLE IF NOT EXISTS repositories (
    id SERIAL PRIMARY KEY,
    "user" TEXT NOT NULL,
    name TEXT NOT NULL,
    UNIQUE ("user", name)
);

CREATE TABLE IF NOT EXISTS releases (
    id BIGSERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    repoID INTEGER NOT NULL,
    FOREIGN KEY (repoID) REFERENCES repositories(id)
);

CREATE TABLE IF NOT EXISTS commits (
    hash TEXT NOT NULL,
    message TEXT NOT NULL,
    releaseID BIGINT NOT NULL,
    PRIMARY KEY (hash, releaseID),
    FOREIGN KEY (releaseID) REFERENCES releases(id)
);
"""

def init_db():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        cursor = conn.cursor()
        cursor.execute(create_tables_sql)
        conn.commit()
        cursor.close()
        conn.close()
        print("✅ Database initialized successfully!")
    except Exception as e:
        print("❌ Error initializing DB:", e)

if __name__ == "__main__":
    init_db()
