import requests
import redis
import json
import time

GITHUB_API_URL = "https://api.github.com/search/repositories"
GITHUB_TOKEN = "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"
REDIS_HOST = "localhost"

def get_top_repos():
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    params = {"q": "stars:>10000", "sort": "stars", "order": "desc", "per_page": 100}
    repos = []
    
    while len(repos) < 5000:
        response = requests.get(GITHUB_API_URL, headers=headers, params=params)
        data = response.json()
        
        for repo in data["items"]:
            print(f"Fetched repo: {repo['full_name']}")
            # Add to Redis queue as soon as it is fetched
            add_repos_to_queue(repo["full_name"])
            repos.append(repo["full_name"])
        
        if "next" not in response.links:
            break
        
        params["page"] = response.links["next"]["url"].split("page=")[1]

    return repos

def add_repos_to_queue(repo):
    r = redis.Redis(host=REDIS_HOST, port=6379, db=0)
    r.lpush("github_repos", repo)
    print(f"Added to queue: {repo}")

if __name__ == "__main__":
    print("Fetching top 5000 GitHub repos...")
    repos = get_top_repos()
    print("Repos added to queue.")
