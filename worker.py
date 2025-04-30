import redis
import requests
import json
from api_client import create_api_client, make_request

# Cấu hình GitHub API & Redis
REDIS_HOST = "localhost"
GITHUB_API_URL = "https://api.github.com/repos"

def get_repo_from_queue():
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    repo = r.lpop("github_repos")  # Lấy và loại bỏ repo đầu tiên trong queue
    if repo:
        return repo.decode("utf-8")  # Giải mã từ byte thành string
    return None

def get_releases(repo):
    releases_url = f"{GITHUB_API_URL}/{repo}/releases"
    headers = create_api_client()
    response = make_request(releases_url, headers)
    if response and response.status_code == 200:
        return response.json()
    elif response and response.status_code == 403:
        print("❌ Bị giới hạn bởi GitHub API (403).")
    return []

def get_commits(repo, release_tag):
    commits_url = f"{GITHUB_API_URL}/{repo}/commits?sha={release_tag}"
    headers = create_api_client()
    response = make_request(commits_url, headers)
    if response and response.status_code == 200:
        return response.json()
    return []

def worker():
    repo = get_repo_from_queue()
    if repo:
        print(f"🚀 Đang xử lý: {repo}")
        
        releases = get_releases(repo)
        result = {
            "repo": repo,
            "releases": []
        }

        for release in releases:
            tag = release.get("tag_name")
            if not tag:
                continue
            commits = get_commits(repo, tag)
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

        # Hiển thị kết quả
        print(json.dumps(result, indent=2))
        return result
    else:
        print("📭 Queue trống.")
        return None

if __name__ == "__main__":
    worker()