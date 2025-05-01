from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "github_crawler"
DB_USER = "postgres"
DB_PASSWORD = "huy123456789"

def get_conn():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def save_data(payload):
    conn = get_conn()
    cur = conn.cursor()

    user = payload["user"]
    repo_name = payload["repo"]

    cur.execute("""
        INSERT INTO repo ("user", name)
        VALUES (%s, %s)
        ON CONFLICT ("user", name) DO NOTHING
        RETURNING id
    """, (user, repo_name))

    repo_row = cur.fetchone()
    if repo_row:
        repo_id = repo_row[0]
    else:
        cur.execute("""
            SELECT id FROM repo
            WHERE "user" = %s AND name = %s
        """, (user, repo_name))
        repo_id = cur.fetchone()[0]

    for rel in payload.get("releases", []):
        release_id = rel["id"]
        content = rel["content"]

        cur.execute("""
            INSERT INTO "release" (id, content, repoID)
            VALUES (%s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                content = EXCLUDED.content,
                repoID = EXCLUDED.repoID
        """, (release_id, content, repo_id))

        for cm in rel.get("commits", []):
            cur.execute("""
                INSERT INTO commits (hash, message, releaseID)
                VALUES (%s, %s, %s)
                ON CONFLICT (hash, releaseID) DO UPDATE SET
                    message = EXCLUDED.message
            """, (cm["hash"], cm["message"], release_id))

    conn.commit()
    cur.close()
    conn.close()

@app.route("/save_data", methods=["POST"])
def save_data_route():
    data = request.get_json(force=True)

    if not data.get("user") or not data.get("repo") or not isinstance(data.get("releases"), list):
        return jsonify({
            "error": "Payload phải có 'user', 'repo', và danh sách 'releases'"
        }), 400

    try:
        save_data(data)
        return jsonify({"message": "✅ Dữ liệu đã được lưu thành công!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
