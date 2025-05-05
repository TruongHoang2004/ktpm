import requests

url = "https://api.github.com/repos/facebook/react/compare/v19.0.0...v19.1.0"
headers = {"Accept": "application/vnd.github+json"}
proxies = {
    "http": "http://pcjm2Is2mE-res-any:PC_1eqwkDpGtrUwA586o@proxy-us.proxy-cheap.com:5959",
    "https": "http://pcjm2Is2mE-res-any:PC_1eqwkDpGtrUwA586o@proxy-us.proxy-cheap.com:5959"
}

response = requests.get(url, headers=headers, proxies=proxies)
data = response.json()

print(f"Tổng số commit: {len(data['commits'])}")