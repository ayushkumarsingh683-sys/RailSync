import concurrent.futures
import requests

URL = "http://127.0.0.1:8000/api/book-seat"
payload = {
    "user_id": 1,
    "train_id": 1,
    "coach_id": 1,
    "seat_number": 7
}

def book_seat():
    response = requests.post(URL, json=payload)
    return response.status_code, response.json()

# Simulate 10 users hitting the endpoint at the exact same millisecond
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(book_seat) for _ in range(10)]
    results = [f.result() for f in concurrent.futures.asyncio.futures.as_completed(futures)] if hasattr(concurrent.futures, 'asyncio') else [f.result() for f in futures]

for code, res in results:
    print(f"Status: {code} | Response: {res}")