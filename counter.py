import requests

url = "https://api.github.com/repos/facebook/react/compare/v19.0.0...v19.1.0"
headers = {"Accept": "application/vnd.github+json"}

response = requests.get(url, headers=headers)
data = response.json()

print(f"Tổng số commit: {len(data['commits'])}")
