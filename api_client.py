import os
import requests
from itertools import cycle
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class GitHubAPIClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GitHubAPIClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.tokens = [
            os.getenv("GITHUB_TOKEN_1"),
            os.getenv("GITHUB_TOKEN_2"),
            os.getenv("GITHUB_TOKEN_3"),
            os.getenv("GITHUB_TOKEN_4"),
            os.getenv("GITHUB_TOKEN_5"),
            os.getenv("GITHUB_TOKEN_6"),
            os.getenv("GITHUB_TOKEN_7"),
        ]

        missing_tokens = [f"GITHUB_TOKEN_{i+1}" for i, token in enumerate(self.tokens) if not token]
        if missing_tokens:
            raise ValueError(f"Missing GitHub tokens in .env file: {', '.join(missing_tokens)}")

        self.token_cycle = cycle(self.tokens)
        self.current_token = next(self.token_cycle)
        self.max_retries = len(self.tokens)

    def _get_headers(self, token):
        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-crawler"
        }

    def make_request(self, url):
        retries = 0
        proxies = {
            "http": "http://pcjm2Is2mE-res-any:PC_1eqwkDpGtrUwA586o@proxy-us.proxy-cheap.com:5959",
            "https": "http://pcjm2Is2mE-res-any:PC_1eqwkDpGtrUwA586o@proxy-us.proxy-cheap.com:5959"
        }

        while retries < self.max_retries:
            headers = self._get_headers(self.current_token)
            response = requests.get(url, headers=headers, proxies=proxies)

            if response.status_code == 200:
                return response

            elif response.status_code in [401, 403]:
                message = response.json().get("message", "")
                print(f"⚠️ Token error ({response.status_code}): {message}")
                self.current_token = next(self.token_cycle)
                retries += 1
            else:
                print(f"❌ Request failed: {response.status_code} — {response.text}")
                return None

        print("🚫 All tokens exhausted or invalid.")
        return None