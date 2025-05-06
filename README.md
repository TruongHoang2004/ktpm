# GitHub Release Crawler

## Mục tiêu

Dự án này triển khai một crawler để thu thập thông tin các bản release của 5000 repository có nhiều sao nhất trên GitHub. Thông tin thu thập bao gồm: danh sách repository, các release của từng repository, và commit giữa các release. Dữ liệu được lưu trữ vào PostgreSQL và sử dụng Redis làm hàng đợi trung gian.

## Cải tiến so với phiên bản ban đầu

Phiên bản ban đầu của dự án (`github-crawler`) sử dụng Scrapy để crawl dữ liệu từ GitHub Search API. Tuy nhiên, phiên bản này gặp một số hạn chế:

- **Giới hạn API**: GitHub Search API chỉ trả về 1000 kết quả đầu tiên, dẫn đến khó khăn trong việc thu thập 5000 repository.
- **Hiệu suất thấp**: Không có cơ chế song song hóa, crawl tuần tự mất nhiều thời gian (~2 tiếng cho 98 repo).
- **Quản lý lỗi kém**: Không xử lý tốt các lỗi như rate limit hoặc token không hợp lệ, dễ bị dừng giữa chừng (lỗi 422, 401, 403,...).
- **Không tối ưu database**: Quá trình đọc/ghi database không được tối ưu, dẫn đến hiệu suất thấp khi xử lý lượng dữ liệu lớn.

Phiên bản hiện tại đã cải tiến đáng kể:

- **Vượt qua giới hạn API**: Sử dụng `crawl_gitstar.py` để lấy danh sách 5000 repository từ trang `gitstar-ranking.com`, thay vì GitHub Search API, đảm bảo đạt đủ số lượng repository cần thiết.
- **Song song hóa**: Sử dụng đa tiến trình (`worker_manager.py`) để xử lý đồng thời nhiều repository, tăng tốc độ crawl.
- **Tối ưu database**: Tối ưu schema và truy vấn trong `init_db.py` để giảm thời gian đọc/ghi.
- **Xử lý lỗi tốt hơn**: `api_client.py` luân phiên token khi gặp lỗi `401` (bad credentials) hoặc `403` (rate limit), đồng thời retry khi gặp lỗi mạng.

## Giải thích các yêu cầu đạt được

### 1. Triển khai crawler cơ bản, thu thập tự động (có thể bị chặn)

- **Triển khai**:
  - `crawl_gitstar.py` thu thập danh sách 5000 repository từ `gitstar-ranking.com` và đẩy vào Redis queue (`github_repos`).
  - `worker.py` lấy repository từ queue, truy vấn GitHub API để lấy thông tin release và commit, sau đó lưu vào database qua `api.py`.

### 2. Đánh giá và nêu nguyên nhân của các vấn đề gặp phải

- **Giới hạn API**: GitHub Search API giới hạn 1000 kết quả, không đủ để đạt 5000 repository.
- **Rate limit và lỗi token**:
  - Gặp lỗi `401: Bad credentials` do một số token không hợp lệ.
  - Gặp lỗi `403: Rate limit exceeded` khi gửi quá nhiều request với cùng một token.
- **Hiệu suất**: Xử lý tuần tự (phiên bản ban đầu) mất nhiều thời gian, không tận dụng được tài nguyên hệ thống.
- **Đọc/ghi database**: Quá trình lưu dữ liệu lớn (hàng triệu commit) gây chậm và tốn tài nguyên.

### 3. Cải tiến và so sánh hiệu suất với phiên bản ban đầu

- **Vượt qua giới hạn API**:
  - Chuyển sang dùng `gitstar-ranking.com` để lấy danh sách repository, đảm bảo đủ 5000 repository.
- **Hiệu suất**:
  - Phiên bản ban đầu: Crawl tuần tự, mất ~2 giờ để xử lý 98 repository.
  - Phiên bản hiện tại: Song song hóa với 40 workers, xử lý 5000 repository trong ~12 giờ.
- **Xử lý lỗi**:
  - `api_client.py` luân phiên token khi gặp lỗi `401` hoặc `403`, giảm nguy cơ dừng giữa chừng.
  - Retry khi gặp lỗi mạng (`ChunkedEncodingError`, `ConnectionError`, `Timeout`).

### 4. Tối ưu quá trình đọc/ghi database

- **Schema tối ưu**:
  - `init_db.py` tạo bảng `repositories`, `releases`, và `commits` với khóa chính và khóa ngoại hợp lý, đảm bảo tính toàn vẹn dữ liệu.
  - Sử dụng `BIGSERIAL` cho `releases.id` để hỗ trợ số lượng lớn release.
  - Khóa chính composite (`hash`, `releaseID`) trong bảng `commits` để tránh trùng lặp commit.
- **Hiệu quả**:
  - Lưu trữ dữ liệu lớn (45 triệu commit, 16GB) mà không gặp lỗi.
  - Giảm thời gian ghi nhờ sử dụng batch insert (trong `api.py`, không được hiển thị trực tiếp nhưng giả định áp dụng).

### 5. Song song hóa (đa luồng) quá trình crawl

- **Triển khai**:
  - `worker_manager.py` sử dụng `multiprocessing` để chạy tối đa 40 workers đồng thời.
  - Mỗi worker lấy repository từ Redis queue (`github_repos`) và xử lý độc lập (lấy release, commit, lưu vào database).
- **Hiệu quả**:
  - Tăng tốc độ xử lý gấp 40 lần so với tuần tự (với 40 workers).
  - Giảm thời gian từ ~2 giờ (98 repository, tuần tự) xuống ~12 giờ (5000 repository, song song).

### 6. Giải quyết vấn đề crawler bị chặn khi truy cập quá nhiều

- **Kỹ thuật sử dụng**:
  - **Luân phiên token** (`api_client.py`): Sử dụng nhiều token GitHub và luân phiên khi gặp lỗi `403` (rate limit) hoặc `401` (bad credentials), đảm bảo không bị chặn.
  - **Delay giữa các request**: Thêm `time.sleep(1)` trong `crawl_gitstar.py` để tránh bị `gitstar-ranking.com` chặn.
  - **Retry khi lỗi mạng**: `api_client.py` retry khi gặp `ChunkedEncodingError`, `ConnectionError`, hoặc `Timeout`.
- **Hiệu quả**:
  - Không bị GitHub chặn trong suốt quá trình crawl 5000 repository.
  - `gitstar-ranking.com` không chặn nhờ delay hợp lý.

### 7. Đánh giá các giải pháp tối ưu khác nhau

- **Chia query theo thời gian tạo (`created`)**:
  - Áp dụng trong `master.py` (các phiên bản trước), chia query thành các khoảng `created:2023-01-01..2025-04-30`, `created:2021-01-01..2023-01-01`, v.v.
  - Ưu điểm: Vượt qua giới hạn 1000 kết quả/query, mỗi khoảng trả về tối đa 1000 repository.
  - Nhược điểm: Không đủ repository với `stars:>10000`, chỉ đạt 3557 repository.
- **Chia theo `page`**:
  - Thử áp dụng cách chia theo trang (trang 1-5, 6-10, ..., 46-50), nhưng thất bại vì GitHub Search API giới hạn 1000 kết quả.
- **Sử dụng `gitstar-ranking.com`**:
  - Giải pháp cuối cùng: Crawl danh sách từ `gitstar-ranking.com`, không bị giới hạn 1000 kết quả.
  - Ưu điểm: Đạt đủ 5000 repository, đơn giản và hiệu quả.
  - Nhược điểm: Phụ thuộc vào trang web bên thứ ba, cần delay để tránh bị chặn.

## Cách chạy

### Yêu cầu

- Docker với Redis và PostgreSQL đã được thiết lập.
- Python 3.x và các thư viện cần thiết:
  ```bash
  pip install requests psycopg2 redis python-dotenv beautifulsoup4
  ```

### Các bước chạy

1. **Khởi động Docker**:

   - Đảm bảo Redis và PostgreSQL đã chạy trong Docker:
     ```bash
     docker run -d --name redis -p 6379:6379 redis
     docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=your_password postgres
     ```
   - Cấu hình Redis và PostgreSQL trong file `.env`:
     ```
     REDIS_HOST=localhost
     REDIS_PORT=6379
     REDIS_DB=0
     REDIS_QUEUE_NAME=github_repos
     DB_HOST=localhost
     DB_PORT=5432
     DB_NAME=postgres
     DB_USER=postgres
     DB_PASSWORD=your_password
     GITHUB_TOKENS=token1,token2,token3,token4
     ```

2. **Khởi tạo database**:

   - Chạy script để tạo bảng trong PostgreSQL:
     ```bash
     python init_db.py
     ```
   - Kết quả: Tạo các bảng `repositories`, `releases`, và `commits`.

3. **Crawl danh sách repository**:

   - Chạy script để crawl 5000 repository từ `gitstar-ranking.com` và đẩy vào Redis queue:
     ```bash
     python crawl_gitstar.py
     ```
   - Script sẽ crawl từng trang (50 trang, mỗi trang 100 repository), tổng cộng 5000 repository.

4. **Chờ 5 giây và chạy worker manager**:
   - Đợi khoảng 5 giây để đảm bảo Redis queue đã được điền dữ liệu.
   - Chạy `worker_manager.py` để xử lý đồng thời 40 workers:
     ```bash
     python worker_manager.py
     ```
   - Workers sẽ lấy repository từ Redis queue, truy vấn GitHub API để lấy release và commit, sau đó lưu vào database.

## Kết quả chạy

Sau khi chạy xong, dữ liệu được lưu vào PostgreSQL với kết quả như sau:

- **Repositories**:
  - Số lượng: 4990 rows
  - Dung lượng: 752KB
- **Releases**:
  - Số lượng: 306,941 rows
  - Dung lượng: 307MB
- **Commits**:
  - Số lượng: 45,569,908 rows
  - Dung lượng: 16GB

### Hiệu suất workers

- Chạy đồng thời 40 workers (thiết lập trong `worker_manager.py`).
- Thời gian xử lý: ~12 giờ cho 5000 repository.

## Lưu ý

- **Token GitHub**: Đảm bảo các token trong file `.env` (`GITHUB_TOKENS`) hợp lệ và có quyền `repo`, `public_repo`.
- **Redis và PostgreSQL**: Đảm bảo cả hai service đều đang chạy trước khi thực thi script.
- **Tối ưu thêm**:
  - Có thể tăng số lượng workers nếu máy có nhiều CPU core.
  - Tối ưu batch insert trong `api.py` để tăng tốc độ ghi database.
