from flask import Flask, request
import psycopg2
import json

app = Flask(__name__)

# Thay thế DATABASE_URL bằng các tham số kết nối riêng lẻ
DB_HOST = "localhost"
DB_PORT = "5432"  # Mặc định của PostgreSQL
DB_NAME = "github_crawler"
DB_USER = "postgres"  # Thay bằng tên người dùng của bạn
DB_PASSWORD = "truonghoang2004"  # Thay bằng mật khẩu của bạn

def save_data(data):
    # Kết nối đến PostgreSQL sử dụng các tham số kết nối
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO github_data (repo_name, releases, commits)
        VALUES (%s, %s, %s)
    """, (data["repo"], json.dumps(data["releases"]), json.dumps(data["commits"])))

    conn.commit()
    cursor.close()
    conn.close()

@app.route("/save_data", methods=["POST"])
def save_data_route():
    data = request.json
    save_data(data)
    return {"message": "Data saved successfully!"}, 200

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
