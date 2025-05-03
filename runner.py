import redis
import time
from multiprocessing import Pool, current_process
from worker import worker  # import hàm xử lý từ worker.py

REDIS_HOST = "localhost"
REDIS_PORT = 6379
REDIS_DB = 0
MAX_WORKERS = 100
WAIT_TIME_IF_EMPTY = 10  # thời gian chờ khi Redis trống

def count_pending_repos():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    return r.llen("github_repos")

def continuous_worker_loop(worker_id):
    print(f"👷 Worker-{worker_id} bắt đầu.")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    idle_count = 0

    while True:
        repo = r.lpop("github_repos")
        if repo:
            idle_count = 0
            repo = repo.decode("utf-8")
            print(f"👷 Worker-{worker_id} đang xử lý: {repo}")
            worker(repo)  # Truyền repo trực tiếp
        else:
            idle_count += 1
            if idle_count >= WAIT_TIME_IF_EMPTY:
                print(f"🛑 Worker-{worker_id} kết thúc do hàng đợi trống.")
                break
            time.sleep(1)

def run_workers_with_loop():
    print(f"🚀 Khởi chạy tối đa {MAX_WORKERS} worker(s).")
    with Pool(processes=MAX_WORKERS) as pool:
        pool.map(continuous_worker_loop, range(MAX_WORKERS))
    print("🎉 Tất cả worker đã hoàn thành và chương trình đã kết thúc.")


if __name__ == "__main__":
    run_workers_with_loop()
