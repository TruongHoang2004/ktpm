import os
import requests
import time
from itertools import cycle
from dotenv import load_dotenv
from requests.exceptions import ChunkedEncodingError, ConnectionError, Timeout, RequestException

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
        raw_tokens = os.getenv("GITHUB_TOKENS")
        if not raw_tokens:
            raise ValueError("Missing GITHUB_TOKENS in .env file")

        self.tokens = [token.strip() for token in raw_tokens.split(',') if token.strip()]

        if not self.tokens:
            raise ValueError("No valid GitHub tokens provided in GITHUB_TOKENS")

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

        while retries < self.max_retries:
            headers = self._get_headers(self.current_token)
            try:
                response = requests.get(url, headers=headers, timeout=15)

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

            except (ChunkedEncodingError, ConnectionError, Timeout) as e:
                print(f"🔁 Lỗi mạng ({type(e).__name__}): {e}. Đang thử lại với token khác...")
                self.current_token = next(self.token_cycle)
                retries += 1
                time.sleep(2)

            except RequestException as e:
                print(f"❌ RequestException nghiêm trọng: {e}")
                return None

        print("🚫 Tất cả token đều lỗi hoặc không thể kết nối. Chờ 10 phút rồi thử lại...")
        time.sleep(600)
        return self.make_request(url)
