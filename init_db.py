import psycopg2

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "github_crawler"
DB_USER = "postgres"
DB_PASSWORD = "huy123456789"

create_tables_sql = """
CREATE TABLE IF NOT EXISTS repo (
    id SERIAL PRIMARY KEY,
    "user" TEXT NOT NULL,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS release (
    id BIGINT PRIMARY KEY,
    content TEXT NOT NULL,
    repoID INTEGER NOT NULL,
    FOREIGN KEY (repoID) REFERENES repo(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS commits (
    hash TEXT NOT NULL,
    message TEXT NOT NULL,
    releaseID BIGINT NOT NULL,
    PRIMARY KEY (hash, releaseID),
    FOREIGN KEY (releaseID) REFERENCES release(id) ON DELETE CASCADE
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
