import requests
from bs4 import BeautifulSoup
import time

BASE_URL = "https://gitstar-ranking.com/repositories"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

def extract_repos_from_page(html):
    soup = BeautifulSoup(html, "html.parser")
    repo_links = soup.select('a.paginated_item span.name span.hidden-xs.hidden-sm')
    return [repo.get_text(strip=True) for repo in repo_links]

def crawl_top_repos(max_pages=50): 
    all_repos = []
    for page in range(1, max_pages + 1):
        print(f"--- Trang {page} ---")
        try:
            response = requests.get(f"{BASE_URL}?page={page}", headers=HEADERS)
            if response.status_code != 200:
                print(f"⚠️ Không tải được trang {page} (HTTP {response.status_code})")
                break
            repos = extract_repos_from_page(response.text)
            if not repos:
                print("⚠️ Không tìm thấy repository nào trên trang này.")
                break
            all_repos.extend(repos)
            for repo in repos:
                print(repo)
            time.sleep(1) 
        except Exception as e:
            print(f"❌ Lỗi tại trang {page}: {e}")
            break

    print(f"\n✅ Tổng cộng {len(all_repos)} repository đã được thu thập.")
    return all_repos

if __name__ == "__main__":
    crawl_top_repos()
