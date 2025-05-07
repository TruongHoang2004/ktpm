import os
import redis
from dotenv import load_dotenv
from api_client import GitHubAPIClient
from api import save_data

load_dotenv()

# Cấu hình từ .env
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "github_repos")
GITHUB_API_URL = os.getenv("GITHUB_API_URL", "https://api.github.com/repos")

client = GitHubAPIClient()

def get_repo_from_queue():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    repo = r.lpop(REDIS_QUEUE_NAME)
    return repo.decode("utf-8") if repo else None

def get_releases(repo):
    releases = []
    page = 1
    per_page = 100

    while True:
        url = f"{GITHUB_API_URL}/{repo}/releases?page={page}&per_page={per_page}"
        response = client.make_request(url)

        if not response:
            print(f"[{repo}] ❌ Không nhận được phản hồi từ GitHub API khi lấy releases.")
            break

        if response.status_code != 200:
            print(f"[{repo}] ⚠️ Lỗi {response.status_code} khi lấy releases: {response.text}")
            break

        page_data = response.json()
        if not page_data:
            break

        print(f"[{repo}] 📄 Đã lấy {len(page_data)} releases ở trang {page}")
        releases.extend(page_data)
        page += 1

    return releases

def get_commits_between_tags(repo, tag1, tag2):
    page = 1
    per_page = 250
    all_commits = []

    print(f"[{repo}] 🔍 So sánh commits từ {tag1} → {tag2}")

    while True:
        url = f"{GITHUB_API_URL}/{repo}/compare/{tag1}...{tag2}?page={page}&per_page={per_page}"
        response = client.make_request(url)

        if not response:
            print(f"[{repo}] ❌ Không lấy được commits giữa {tag1} và {tag2}")
            break

        if response.status_code != 200:
            print(f"[{repo}] ⚠️ Lỗi {response.status_code} khi compare tags: {response.text}")
            break

        data = response.json()
        commits = data.get("commits", [])
        print(f"[{repo}] 📦 Trang {page}: {len(commits)} commits")

        all_commits.extend(commits)

        if len(commits) < per_page:
            break
        page += 1

    print(f"[{repo}] ✅ Tổng số commits từ {tag1} → {tag2}: {len(all_commits)}")
    return all_commits

def process_repo(repo):
    print(f"\n[{repo}] 🚀 Bắt đầu xử lý repository")

    releases_raw = get_releases(repo)
    print(f"[{repo}] 📊 Tổng số releases: {len(releases_raw)}")

    result = {
        "user": repo.split("/")[0],
        "repo": repo.split("/")[1],
        "releases": []
    }

    for release in releases_raw:
        tag = release.get("tag_name")
        if not tag:
            print(f"[{repo}] ⚠️ Bỏ qua release không có tag")
            continue

        print(f"[{repo}] 📌 Release: {release.get('name', '(no name)')} (Tag: {tag})")
        release_data = {
            "release_name": release.get("name", ""),
            "tag_name": tag,
            "body": release.get("body", ""),
            "created_at": release.get("created_at")
        }
        result["releases"].append(release_data)

    result["releases"].sort(key=lambda r: r.get("created_at", ""), reverse=True)

    for i in range(len(result["releases"]) - 1):
        newer = result["releases"][i]
        older = result["releases"][i + 1]
        newer_tag = newer["tag_name"]
        older_tag = older["tag_name"]

        print(f"\n[{repo}] ➡️ So sánh commit: {older_tag} → {newer_tag}")
        commits = get_commits_between_tags(repo, older_tag, newer_tag)

        newer["commits"] = {
            "from": older_tag,
            "to": newer_tag,
            "total_commits": len(commits),
            "commits": [
                {
                    "sha": c["sha"],
                    "message": c["commit"]["message"],
                    "author": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"]
                } for c in commits
            ]
        }

    print(f"\n[{repo}] 🎉 Hoàn thành xử lý với {len(result['releases'])} releases")
    save_data(result)

def worker(repo):
    try:
        process_repo(repo)
    except Exception as e:
        print(f"[{repo}] 🔥 Lỗi trong quá trình xử lý: {e}")

if __name__ == "__main__":
    worker("aaamoon/copilot-gpt4-service")  # Hoặc bất kỳ repo nào bạn muốn test
