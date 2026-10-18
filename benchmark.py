"""Compare the chosen data structures with naive alternatives."""
import heapq
import random
import time


def run_benchmark(n=20000):
    ids = list(range(n))
    table = {i: i for i in ids}
    pairs = [(i, i) for i in ids]
    target = n - 1

    t = time.perf_counter()
    for _ in range(200):
        table[target]
    hash_t = time.perf_counter() - t

    t = time.perf_counter()
    for _ in range(200):
        next(v for k, v in pairs if k == target)
    scan_t = time.perf_counter() - t

    sev = [random.randint(1, 10) for _ in ids]
    heap = [(-s, i) for i, s in enumerate(sev)]
    heapq.heapify(heap)
    t = time.perf_counter()
    for _ in range(200):
        heapq.heappop(heap)
    heap_t = time.perf_counter() - t

    arr = list(enumerate(sev))
    t = time.perf_counter()
    for _ in range(200):
        best = max(arr, key=lambda x: x[1])
        arr.remove(best)
    max_t = time.perf_counter() - t

    ms = lambda x: f"{x * 1000:.3f} ms"
    return {"n": n, "rows": [
        {"task": "Patient lookup x200", "good": "Hash table", "good_t": ms(hash_t),
         "naive": "List scan", "naive_t": ms(scan_t), "speedup": f"{scan_t / max(hash_t, 1e-9):,.0f}x"},
        {"task": "Pick next patient x200", "good": "Heap", "good_t": ms(heap_t),
         "naive": "Linear max()", "naive_t": ms(max_t), "speedup": f"{max_t / max(heap_t, 1e-9):,.0f}x"},
    ]}
