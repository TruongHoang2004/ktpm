import requests
import json

# GitHub access token
token = ""
headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github+json"
}

# Initialization
page = 1
per_page = 250
all_commits = []

while True:
    print(f"Fetching page {page}...")
    url = f"https://api.github.com/repos/facebook/react/compare/v18.3.1...v19.0.0?page={page}&per_page={per_page}"
    response = requests.get(url, headers=headers)
    data = response.json()

    commits = data.get("commits", [])
    all_commits.extend(commits)

    if len(commits) < per_page:
        break
    page += 1

# Create summary
summary = {
    "total_commits": len(all_commits),
    "commits": [
        {
            "sha": c["sha"],
            "commit": {
                "message": c["commit"]["message"],
                "author": {
                    "name": c["commit"]["author"]["name"],
                    "date": c["commit"]["author"]["date"]
                }
            }
        } for c in all_commits
    ]
}

# Print summary as JSON
print(json.dumps(summary, indent=2))
print(f"Total commits: {len(all_commits)}")
print(f"First commit SHA: {summary['commits'][0]}")
print(f"Last commit SHA: {summary['commits'][-1]}")
