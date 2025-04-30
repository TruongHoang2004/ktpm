import redis
import requests
import json
from api_client import create_api_client, make_request

# Cấu hình GitHub API & Redis
REDIS_HOST = "localhost"
GITHUB_API_URL = "https://api.github.com/repos"

# Khởi tạo headers ban đầu
HEADERS = create_api_client()

def get_repo_from_queue():
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    repo = r.lpop("github_repos")  # Lấy và loại bỏ repo đầu tiên trong queue
    if repo:
        return repo.decode("utf-8")
    return None

def get_releases(repo):
    global HEADERS
    releases = []
    page = 1
    per_page = 100

    while True:
        url = f"{GITHUB_API_URL}/{repo}/releases?page={page}&per_page={per_page}"
        response = make_request(url, HEADERS)

        if response is None:
            print(f"❌ Không thể lấy releases từ {repo}")
            break

        if response.status_code == 200:
            page_data = response.json()
            if not page_data:
                break
            releases.extend(page_data)
            page += 1
        else:
            print(f"⚠️ Lỗi khi lấy release từ {repo}: {response.status_code}")
            break

    return releases

def worker(repo):
    print(f"🚀 Đang xử lý: {repo}")

    global HEADERS
    HEADERS = create_api_client()

    releases = get_releases(repo)
    print(f"Số lượng releases được tìm thấy: {len(releases)}")

    result = {
        "repo": repo,
        "releases": []
    }

    for release in releases:
        tag = release.get("tag_name")
        if not tag:
            continue

        print(f"  - Release: {release.get('name', '')} (Tag: {tag})")

        release_data = {
            "release_name": release.get("name", ""),
            "tag_name": tag
        }

        result["releases"].append(release_data)

    print(f"✅ Hoàn thành: {repo} — {len(result['releases'])} releases được xử lý.")
    return result

if __name__ == "__main__":
    worker("facebook/react")  # Thay repo ở đây nếu cần
