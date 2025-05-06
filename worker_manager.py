import os
import time
import redis
from multiprocessing import Process
from dotenv import load_dotenv
from worker import worker  # Import hàm xử lý chính từ worker.py

# Load biến môi trường từ file .env
load_dotenv()

# Cấu hình từ biến môi trường
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_QUEUE_NAME = os.getenv("REDIS_QUEUE_NAME", "github_repos")

MAX_WORKERS = int(os.getenv("MAX_WORKERS", 25))
WAIT_TIME_IF_EMPTY = int(os.getenv("WAIT_TIME_IF_EMPTY", 10))
CHECK_INTERVAL = int(os.getenv("CHECK_INTERVAL", 30))

def count_pending_repos():
    """Đếm số lượng repo còn lại trong hàng đợi Redis."""
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    return r.llen(REDIS_QUEUE_NAME)

def continuous_worker_loop(worker_id):
    """Hàm worker chính, lặp liên tục và xử lý các repo từ Redis."""
    print(f"👷 Worker-{worker_id} bắt đầu.")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB)
    idle_count = 0

    while True:
        repo = r.lpop(REDIS_QUEUE_NAME)
        if repo:
            idle_count = 0
            repo = repo.decode("utf-8")
            print(f"👷 Worker-{worker_id} đang xử lý: {repo}")
            worker(repo)
        else:
            idle_count += 1
            if idle_count >= WAIT_TIME_IF_EMPTY:
                print(f"🛑 Worker-{worker_id} kết thúc do hàng đợi trống.")
                break
            time.sleep(1)

def run_workers_with_monitoring():
    """Khởi chạy và giám sát tiến trình worker."""
    print(f"🚀 Khởi chạy tối đa {MAX_WORKERS} worker(s).")
    processes = {}

    # Khởi tạo và chạy các tiến trình worker ban đầu
    for i in range(MAX_WORKERS):
        p = Process(target=continuous_worker_loop, args=(i,))
        p.start()
        processes[i] = p

    try:
        while any(p.is_alive() for p in processes.values()):
            time.sleep(CHECK_INTERVAL)
            pending = count_pending_repos()
            print(f"📊 Còn {pending} repo trong hàng đợi.")

            alive_workers = sum(1 for p in processes.values() if p.is_alive())
            print(f"🟢 {alive_workers}/{MAX_WORKERS} worker(s) đang chạy.")
            

            for i, p in processes.items():
                if not p.is_alive():
                    if pending > 0:
                        print(f"🔁 Worker-{i} đã dừng, khởi động lại do vẫn còn repo.")
                        new_p = Process(target=continuous_worker_loop, args=(i,))
                        new_p.start()
                        processes[i] = new_p
                    else:
                        print(f"✅ Worker-{i} đã dừng và không cần khởi động lại.")

        print("🎉 Tất cả tiến trình đã hoàn thành.")
    except KeyboardInterrupt:
        print("🛑 Nhận tín hiệu dừng. Kết thúc toàn bộ tiến trình.")
        for p in processes.values():
            if p.is_alive():
                p.terminate()

if __name__ == "__main__":
    run_workers_with_monitoring()
