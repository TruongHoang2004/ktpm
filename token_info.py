import os
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Tải file .env
load_dotenv()

# Hàm lấy thông tin rate limit cho một token
def get_rate_limit_info(token):
    url = "https://api.github.com/rate_limit"
    headers = {"Authorization": f"token {token}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Lỗi khi lấy rate limit cho token: {token}")
        return None

    # Lấy thông tin rate limit từ phản hồi JSON
    data = response.json()
    core_limit = data['resources']['core']['limit']
    core_remaining = data['resources']['core']['remaining']
    core_reset_timestamp = data['resources']['core']['reset']

    reset_time = datetime.utcfromtimestamp(core_reset_timestamp).replace(tzinfo=timezone.utc).astimezone(timezone(timedelta(hours=7)))

    return core_limit, core_remaining, reset_time

def main():
    # Lấy danh sách các token từ biến môi trường
    raw_tokens = os.getenv("GITHUB_TOKENS")
    if not raw_tokens:
        print("⚠️ Không tìm thấy GITHUB_TOKENS trong .env file")
        return

    tokens = [token.strip() for token in raw_tokens.split(',') if token.strip()]
    if not tokens:
        print("⚠️ Không có token hợp lệ trong GITHUB_TOKENS")
        return

    # Kiểm tra rate limit cho từng token
    for token in tokens:
        print(f"Đang kiểm tra token: {token}")
        rate_limit_info = get_rate_limit_info(token)
        if rate_limit_info:
            limit, remaining, reset_time = rate_limit_info
            print(f"  - Giới hạn: {limit}")
            print(f"  - Còn lại: {remaining}")
            print(f"  - Thời gian reset: {reset_time}")
        print("")

if __name__ == "__main__":
    main()
