import redis
import requests
import json
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get GitHub token from environment variable
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
if not GITHUB_TOKEN:
    raise ValueError("GitHub token not found. Please set GITHUB_TOKEN in your .env file.")

# Cấu hình GitHub API & Redis
REDIS_HOST = "localhost"
GITHUB_API_URL = "https://api.github.com/repos"

HEADERS = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": "github-crawler"
}

def get_repo_from_queue():
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    repo = r.lpop("github_repos")  # Lấy và loại bỏ repo đầu tiên trong queue
    if repo:
        return repo.decode("utf-8")  # Giải mã từ byte thành string
    return None

def get_releases(repo):
    releases = []
    page = 1
    per_page = 100  # GitHub cho phép tối đa 100 item mỗi trang

    while True:
        url = f"{GITHUB_API_URL}/{repo}/releases?page={page}&per_page={per_page}"
        response = requests.get(url, headers=HEADERS)

        if response.status_code == 200:
            page_data = response.json()
            if not page_data:
                break  # Không còn dữ liệu, thoát vòng lặp
            releases.extend(page_data)
            page += 1
        elif response.status_code == 403:
            print("❌ Bị giới hạn bởi GitHub API (403).")
            break
        else:
            print(f"⚠️ Lỗi khi lấy release từ {repo}: {response.status_code}")
            break

    return releases


def get_commits(repo, release_tag, previous_tag=None):
    commits = []
    page = 1
    per_page = 100  # Tối đa 100

    # Nếu có tag trước đó, lấy commit chỉ từ tag đó
    if previous_tag:
        commits_url = f"{GITHUB_API_URL}/{repo}/compare/{previous_tag}...{release_tag}?page={page}&per_page={per_page}"
    else:
        commits_url = f"{GITHUB_API_URL}/{repo}/commits?sha={release_tag}&page={page}&per_page={per_page}"

    while True:
        response = requests.get(commits_url, headers=HEADERS)
        print(f"Fetching commits from URL: {commits_url}")

        if response.status_code == 200:
            page_commits = response.json()
            if not page_commits:
                break
            commits.extend(page_commits)
            page += 1
            print(f"  - Đã lấy {len(page_commits)} commits từ tag {release_tag} của {repo} ở trang {page}.")
        elif response.status_code == 403:
            print("❌ Bị giới hạn bởi GitHub API (403) khi lấy commits.")
            break
        else:
            print(f"⚠️ Lỗi khi lấy commits của tag {release_tag} từ {repo}: {response.status_code}")
            break

    return commits

def worker(repo):
    print(f"🚀 Đang xử lý: {repo}")
    
    releases = get_releases(repo)
    print(f"Số lượng releases được tìm thấy: {len(releases)}")
    
    result = {
        "repo": repo,
        "releases": []
    }

    previous_tag = None  # Không có release trước đó để so sánh ở lần đầu tiên

    # Sắp xếp releases theo thứ tự thời gian (từ cũ đến mới)
    releases = sorted(releases, key=lambda r: r.get("created_at", ""))

    for release in releases:
        tag = release.get("tag_name")
        if not tag:
            continue

        print(f"  - Release: {release.get('name', '')} (Tag: {tag})")
        
        # Lấy commits có thay đổi so với release trước đó
        commits = get_commits(repo, tag, previous_tag)
        print(f"    Số lượng commits: {len(commits)}")
        
        release_data = {
            "release_name": release.get("name", ""),
            "tag_name": tag,
            "commits": []
        }

        for commit in commits:
            release_data["commits"].append({
                "hash": commit.get("sha"),
                "message": commit.get("commit", {}).get("message", "")
            })

        result["releases"].append(release_data)

        # Cập nhật previous_tag cho release tiếp theo
        previous_tag = tag

    print(f"✅ Hoàn thành: {repo} — {len(result['releases'])} releases được xử lý.")
    return result

if __name__ == "__main__":
    worker("facebook/react")  # Thay thế bằng repo bạn muốn xử lý
