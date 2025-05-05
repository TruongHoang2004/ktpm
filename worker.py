import redis
from api_client import GitHubAPIClient
from api import save_data  # Giả sử bạn có một hàm lưu dữ liệu vào DB

# Cấu hình GitHub API & Redis
REDIS_HOST = "localhost"
GITHUB_API_URL = "https://api.github.com/repos"

# Tạo client singleton
client = GitHubAPIClient()

def get_repo_from_queue():
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    repo = r.lpop("github_repos")  # Lấy và loại bỏ repo đầu tiên trong queue
    if repo:
        return repo.decode("utf-8")
    return None

def get_commits_between_tags(repo, tag1, tag2):
    page = 1
    per_page = 250
    all_commits = []

    print(f"🔍 So sánh commits từ {tag1} đến {tag2}")

    while True:
        url = f"{GITHUB_API_URL}/{repo}/compare/{tag1}...{tag2}?page={page}&per_page={per_page}"
        response = client.make_request(url)

        if response is None:
            print(f"❌ Không thể lấy commits từ {repo} giữa {tag1} và {tag2}")
            break

        if response.status_code != 200:
            print(f"⚠️ Lỗi khi lấy commits: {response.status_code} — {response.text}")
            break

        data = response.json()
        commits = data.get("commits", [])
        all_commits.extend(commits)

        if len(commits) < per_page:
            break

        page += 1

    print(f"📦 Tổng số commits từ {tag1} đến {tag2}: {len(all_commits)}")
    return all_commits

def get_releases(repo):
    releases = []
    page = 1
    per_page = 100

    while True:
        url = f"{GITHUB_API_URL}/{repo}/releases?page={page}&per_page={per_page}"
        response = client.make_request(url)

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

    releases = get_releases(repo)
    print(f"Số lượng releases được tìm thấy: {len(releases)}")

    result = {
        "user": repo.split("/")[0],
        "repo": repo.split("/")[1],
        "releases": []
    }

    for release in releases:
        tag = release.get("tag_name")
        if not tag:
            continue

        print(f"  - Release: {release.get('name', '')} (Tag: {tag})")

        release_data = {
            "release_name": release.get("name", ""),
            "tag_name": tag,
            "created_at": release.get("created_at")
        }

        result["releases"].append(release_data)

    # Sắp xếp theo thời gian tạo
    result["releases"].sort(key=lambda r: r.get("created_at", ""), reverse=True)

    # Lấy commit giữa các cặp release liên tiếp
    for i in range(len(result["releases"]) - 1):
        newer_tag = result["releases"][i]["tag_name"]
        older_tag = result["releases"][i + 1]["tag_name"]

        if newer_tag and older_tag:
            commits = get_commits_between_tags(repo, older_tag, newer_tag)

            result["releases"][i]["commits"] = {
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

    print(f"✅ Hoàn thành: {repo} — {len(result['releases'])} releases được xử lý.")

    save_data(result)  # Gọi hàm lưu dữ liệu vào DB

if __name__ == "__main__":
    worker("facebook/react")  # Thay repo ở đây nếu cần