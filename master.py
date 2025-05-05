import redis
import time
from api_client import GitHubAPIClient

GITHUB_API_URL = "https://api.github.com/search/repositories"
REDIS_HOST = "localhost"

TOTAL_REPOS = 5000
PER_PAGE = 100  # GitHub cho tối đa 100 repo mỗi trang
MAX_PAGES = TOTAL_REPOS // PER_PAGE

# Khởi tạo singleton client
client = GitHubAPIClient()

def add_repo_to_queue(repo_full_name):
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    r.rpush("github_repos", repo_full_name)  # FIFO
    print(f"📥 Đã thêm vào queue: {repo_full_name}")

def fetch_top_repos():
    repos = set()
    page = 1

    while len(repos) < TOTAL_REPOS and page <= MAX_PAGES:
        url = f"{GITHUB_API_URL}?q=stars:>0&sort=stars&order=desc&per_page={PER_PAGE}&page={page}"
        response = client.make_request(url)

        if not response:
            print("❌ Không thể lấy danh sách repo. Dừng lại.")
            break

        data = response.json()
        items = data.get("items", [])

        if not items:
            print(f"⚠️ Không có item nào ở trang {page}. Dừng.")
            break

        for repo in items:
            full_name = repo["full_name"]
            if full_name not in repos:
                repos.add(full_name)
                add_repo_to_queue(full_name)
                if len(repos) >= TOTAL_REPOS:
                    break

        page += 1
        time.sleep(1)  # tránh rate limit

    return list(repos)

def master():
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    r.delete("github_repos")
    print("🧹 Đã xóa Redis queue 'github_repos'.")

    print("🚀 Bắt đầu lấy 5000 repo GitHub nhiều sao nhất (không lọc ngôn ngữ)...")
    fetched_repos = fetch_top_repos()
    print(f"✅ Hoàn tất. Tổng số repo đã lấy: {len(fetched_repos)}")

if __name__ == "__main__":
    master()