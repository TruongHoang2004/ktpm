import time
import redis
from master import enqueue_repos
from worker import get_repo_from_queue, worker

QUEUE_NAME = "github_repos"
REDIS_HOST = "localhost"
r = redis.Redis(host=REDIS_HOST, port=6379, db=0)

def run():
    if r.llen(QUEUE_NAME) == 0:
        print("📦 Queue trống. Nạp dữ liệu...")
        enqueue_repos()

    while True:
        repo = get_repo_from_queue()
        if repo:
            worker(repo)
        else:
            print("📭 Không còn repo nào để xử lý.")
            break

if __name__ == "__main__":
    run()
