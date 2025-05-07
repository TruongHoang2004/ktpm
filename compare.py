import requests
from bs4 import BeautifulSoup
import time
import redis
import psycopg2
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Redis config
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# PostgreSQL config
DB_HOST = os.getenv("DB_HOST")
DB_PORT = int(os.getenv("DB_PORT", 5432))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

# Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)

# PostgreSQL
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)
cursor = conn.cursor()

BASE_URL = "https://gitstar-ranking.com/repositories"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def extract_repos_from_page(html):
    soup = BeautifulSoup(html, "html.parser")
    repo_links = soup.select('a.paginated_item span.name span.hidden-xs.hidden-sm')
    return [repo.get_text(strip=True) for repo in repo_links]

def get_existing_repos_from_db():
    cursor.execute("SELECT \"user\", name FROM repositories")
    return set(f"{user}/{name}" for user, name in cursor.fetchall())

def crawl_top_repos_and_compare(max_pages=50):
    all_repos = []
    missing_repos = []

    existing_repos = get_existing_repos_from_db()

    for page in range(1, max_pages + 1):
        print(f"--- Trang {page} ---")
        try:
            response = requests.get(f"{BASE_URL}?page={page}", headers=HEADERS)
            if response.status_code != 200:
                print(f"⚠️ Không tải được trang {page} (HTTP {response.status_code})")
                break
            repos = extract_repos_from_page(response.text)
            if not repos:
                print("⚠️ Không tìm thấy repository nào trên trang này.")
                break
            for full_repo in repos:
                all_repos.append(full_repo)
                if full_repo not in existing_repos:
                    print(f"➕ Thiếu: {full_repo}")
                    redis_client.rpush("github_repos", full_repo)
                    missing_repos.append(full_repo)
            time.sleep(1)
        except Exception as e:
            print(f"❌ Lỗi tại trang {page}: {e}")
            break

    print(f"\n✅ Tổng cộng {len(all_repos)} repo được crawl.")
    print(f"❗ {len(missing_repos)} repo chưa có trong database.")
    return missing_repos

if __name__ == "__main__":
    crawl_top_repos_and_compare()
