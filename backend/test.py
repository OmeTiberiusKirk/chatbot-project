import queue
import threading
import concurrent.futures
import urllib.request

URLS = ["https://python.org",
        "https://docs.python.org",
        "https://peps.python.org",]

q = queue.Queue()

content = []


def worker():
    while True:
        url = q.get()
        with urllib.request.urlopen(url, timeout=60) as conn:
            content.append(conn.read()[:10])
        q.task_done()


# Turn-on the worker thread.
threading.Thread(target=worker, daemon=True).start()

# Send thirty task requests to the worker.
for url in URLS:
    q.put(url)

# Block until all tasks are done.
q.join()
print('All work completed')
print(content)
