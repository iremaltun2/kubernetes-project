
import urllib.request
import urllib.error
import subprocess
import json
import time
import threading
import csv

URL = "http://localhost:8080/api/data"

TEST_DURATION = 30
WARMUP_TIME = 3
REQUEST_INTERVAL = 0.02

results = []
delete_started = False
delete_time = None


def get_backend_pod():
    result = subprocess.run(
        ["kubectl", "get", "pods", "-l", "app=backend", "-o", "json"],
        capture_output=True,
        text=True,
        check=True
    )

    pods = json.loads(result.stdout)["items"]

    ready_pods = [
        pod for pod in pods
        if pod["status"].get("phase") == "Running"
        and any(
            c.get("type") == "Ready" and c.get("status") == "True"
            for c in pod["status"].get("conditions", [])
        )
    ]

    if not ready_pods:
        raise RuntimeError("Ready backend Pod bulunamadi.")

    return ready_pods[0]["metadata"]["name"]


def delete_backend_pod(pod_name):
    global delete_started, delete_time

    delete_started = True
    delete_time = time.monotonic()

    print(f"\nPod siliniyor: {pod_name}")

    subprocess.run(
        [
            "kubectl", "delete", "pod", pod_name,
            "--grace-period=0",
            "--force"
        ],
        check=True
    )

pod_name = get_backend_pod()

print("Backend failure testi basliyor...")
print("Silinecek Pod:", pod_name)
print("Test suresi:", TEST_DURATION, "saniye")

start_time = time.monotonic()
next_delete = start_time + WARMUP_TIME
end_time = start_time + TEST_DURATION

delete_thread = None

while time.monotonic() < end_time:

    now = time.monotonic()

    if now >= next_delete and delete_thread is None:
        delete_thread = threading.Thread(
            target=delete_backend_pod,
            args=(pod_name,)
        )
        delete_thread.start()

    request_start = time.monotonic()

    try:
        request = urllib.request.Request(URL)

        with urllib.request.urlopen(request, timeout=2) as response:
            status = response.status

            results.append({
                "time": request_start - start_time,
                "status": status,
                "result": "SUCCESS",
                "response_time": time.monotonic() - request_start
            })

    except urllib.error.HTTPError as error:
        results.append({
            "time": request_start - start_time,
            "status": error.code,
            "result": "FAIL",
            "response_time": time.monotonic() - request_start
        })

    except Exception as error:
        results.append({
            "time": request_start - start_time,
            "status": "",
            "result": "FAIL",
            "response_time": time.monotonic() - request_start
        })

    elapsed = time.monotonic() - request_start
    time.sleep(max(0, REQUEST_INTERVAL - elapsed))

if delete_thread is not None:
    delete_thread.join()

success = sum(1 for r in results if r["result"] == "SUCCESS")
failure = sum(1 for r in results if r["result"] == "FAIL")

failure_times = [
    r["time"] for r in results if r["result"] == "FAIL"
]

success_after_failure = None

if failure_times:
    first_failure = failure_times[0]

    for r in results:
        if r["time"] > first_failure and r["result"] == "SUCCESS":
            success_after_failure = r["time"]
            break

print("\n--- TEST RESULTS ---")
print("Successful requests:", success)
print("Failed requests:", failure)
print("Total requests:", len(results))

if failure_times and success_after_failure is not None:
    print(
        "Observed interruption:",
        f"{success_after_failure - failure_times[0]:.3f} seconds"
    )
elif failure_times:
    print("Observed interruption: Recovery not observed")
else:
    print("Observed interruption: 0 seconds (no failures observed)")

with open("backend_failure_results.csv", "w", newline="") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=["time", "status", "result", "response_time"]
    )
    writer.writeheader()
    writer.writerows(results)

print("\nDetailed results saved to backend_failure_results.csv")
