from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "github_crawler"
DB_USER = "postgres"
DB_PASSWORD = "truonghoang2004"

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

    # Tạo hoặc lấy repository
    cur.execute("""
        INSERT INTO repositories ("user", name)
        VALUES (%s, %s)
        ON CONFLICT ("user", name) DO NOTHING
        RETURNING id
    """, (user, repo_name))

    repo_row = cur.fetchone()
    if repo_row:
        repo_id = repo_row[0]
    else:
        cur.execute("""
            SELECT id FROM repositories
            WHERE "user" = %s AND name = %s
        """, (user, repo_name))
        repo_id = cur.fetchone()[0]

    for rel in payload.get("releases", []):
        tag = rel.get("tag_name", "")
        name = rel.get("release_name", "")
        created_at = rel.get("created_at", "")
        content = f"{name} | {tag} | {created_at}"

        # Thêm release mới
        cur.execute("""
            INSERT INTO releases (content, repoID)
            VALUES (%s, %s)
            RETURNING id
        """, (content, repo_id))
        release_id = cur.fetchone()[0]

        # Thêm commits nếu có
        commits_data = rel.get("commits", {}).get("commits", [])
        for cm in commits_data:
            hash_val = cm["sha"]
            message = cm["message"]

            cur.execute("""
                INSERT INTO commits (hash, message, releaseID)
                VALUES (%s, %s, %s)
                ON CONFLICT (hash, releaseID) DO UPDATE SET
                    message = EXCLUDED.message
            """, (hash_val, message, release_id))

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
