import requests
from api_client import create_api_client, make_request
import redis
import json
import time

GITHUB_API_URL = "https://api.github.com/search/repositories"
REDIS_HOST = "localhost"

# Danh sách các query khác nhau
SEARCH_QUERIES = [
    "stars:>1000 language:Python",      # Repository viết bằng Python
    "stars:>1000 language:JavaScript",  # Repository viết bằng JavaScript
    "stars:>1000 language:Java",        # Repository viết bằng Java
    "stars:>1000 language:Ruby",        # Repository viết bằng Ruby
    "stars:>1000 language:Go"           # Repository viết bằng Go
]

# Mỗi query chạy 10 trang (1000 repository)
PAGES_PER_QUERY = 10

def get_top_repos():
    repos = set()  # Dùng set để tránh trùng lặp
    current_query_index = 0
    
    while len(repos) < 5000 and current_query_index < len(SEARCH_QUERIES):
        # Lấy query hiện tại
        query = SEARCH_QUERIES[current_query_index]
        print(f"Fetching repositories with query: {query}")
        
        for page in range(1, PAGES_PER_QUERY + 1):
            # Tạo URL với page hiện tại
            url = f"{GITHUB_API_URL}?q={query}&sort=stars&order=desc&per_page=100&page={page}"
            
            # Tạo headers với token luân phiên
            headers = create_api_client()
            response = make_request(url, headers)
            
            if not response:
                print("Failed to fetch repositories, stopping query.")
                break
                
            data = response.json()
            
            # Nếu không có items, chuyển sang query tiếp theo
            if not data.get("items"):
                print(f"No more repositories in page {page} of query {query}, moving to next query.")
                break
                
            for repo in data["items"]:
                repo_full_name = repo["full_name"]
                if repo_full_name not in repos:  # Chỉ thêm nếu chưa có
                    print(f"Fetched repo: {repo_full_name}")
                    add_repos_to_queue(repo_full_name)
                    repos.add(repo_full_name)
                    if len(repos) >= 5000:
                        break
            
            if len(repos) >= 5000:
                break
        
        current_query_index += 1

    return list(repos)

def add_repos_to_queue(repo):
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    r.lpush("github_repos", repo)
    print(f"Added to queue: {repo}")

if __name__ == "__main__":
    # Xóa queue github_repos trước khi bắt đầu
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    r.delete("github_repos")
    print("Cleared Redis queue 'github_repos'.")
    
    print("Fetching top 5000 GitHub repos...")
    repos = get_top_repos()
    print(f"Total repos fetched: {len(repos)}")
    print("Repos added to queue.")