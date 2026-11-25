import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

URL = "http://localhost:8080/api/data"
TOTAL_REQUESTS = 1000
CONCURRENCY = 10


def send_request():
    start = time.perf_counter()

    try:
        with urllib.request.urlopen(URL, timeout=15) as response:
            response.read()
            elapsed = time.perf_counter() - start
            return response.status, elapsed

    except Exception:
        elapsed = time.perf_counter() - start
        return "ERROR", elapsed


start = time.perf_counter()
results = []

with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
    futures = [
        executor.submit(send_request)
        for _ in range(TOTAL_REQUESTS)
    ]

    for future in as_completed(futures):
        results.append(future.result())

total_time = time.perf_counter() - start

successful = [r for r in results if r[0] == 200]
failed = len(results) - len(successful)

if successful:
    avg_response = sum(r[1] for r in successful) / len(successful)
else:
    avg_response = 0

rps = len(successful) / total_time if total_time > 0 else 0

print(f"Total requests: {TOTAL_REQUESTS}")
print(f"Successful: {len(successful)}")
print(f"Failed: {failed}")
print(f"Total time: {total_time:.2f} seconds")
print(f"Average response time: {avg_response:.4f} seconds")
print(f"Throughput: {rps:.2f} requests/second")