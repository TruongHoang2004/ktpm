import requests
import os
from itertools import cycle
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Lấy danh sách token từ file .env
TOKENS = [
    os.getenv("GITHUB_TOKEN_1"),
    os.getenv("GITHUB_TOKEN_2"),
    os.getenv("GITHUB_TOKEN_3"),
    os.getenv("GITHUB_TOKEN_4"),
]

# Kiểm tra và in thông tin chi tiết nếu thiếu token
missing_tokens = [f"GITHUB_TOKEN_{i+1}" for i, token in enumerate(TOKENS) if token is None]
if missing_tokens:
    raise ValueError(f"Missing GitHub tokens in .env file: {', '.join(missing_tokens)}")

# Tạo iterator để luân phiên token
token_iterator = cycle(TOKENS)

def create_api_client():
    """
    Tạo một API client với cơ chế round-robin token.
    Returns: Một dictionary chứa headers với token hiện tại.
    """
    # Lấy token tiếp theo từ iterator
    current_token = next(token_iterator)
    
    # Tạo headers với token hiện tại
    headers = {
        "Authorization": f"Bearer {current_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "github-crawler"
    }
    
    return headers

def make_request(url, headers):
    """
    Gửi request với retry khi gặp rate limit hoặc bad credentials.
    Args:
        url (str): URL của GitHub API.
        headers (dict): Headers chứa token hiện tại.
    Returns:
        Response object hoặc None nếu thất bại.
    """
    for _ in range(len(TOKENS)):  # Thử lại với tất cả token nếu gặp rate limit hoặc bad credentials
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response
        elif response.status_code in [403, 401]:  # Xử lý cả 403 (rate limit) và 401 (bad credentials)
            print(f"Error {response.status_code} with token: {response.json().get('message')}, switching to next token.")
            headers = create_api_client()  # Lấy token mới
        else:
            print(f"Request failed with status {response.status_code}: {response.text}")
            return None
    print("All tokens exhausted due to rate limit or bad credentials.")
    return None