# Hospital Triage & Patient Management (Flask)

Data structures mini project. Run:

    pip install -r requirements.txt
    python app.py

Open http://127.0.0.1:5000

| Feature | Data structure | Complexity |
|---|---|---|
| Patient lookup by ID | Hash table (dict) | O(1) avg |
| Next patient by severity | Heap (priority queue) | O(log n) |
| Undo admit / treat | Stack | O(1) |
| Patient history | Linked list (tail pointer) | O(1) append |
| Patients sorted by name | Binary search tree | O(log n) insert, O(n) in-order |
| Ward route | Graph + BFS | O(V + E) |

Files: `ds.py` (structures), `hospital.py` (logic), `benchmark.py`, `app.py` (routes), `templates/`, `static/style.css`.

## Persistence (SQLite)

Data is stored in `hospital.db` (created on first run, next to `app.py`). The data
structures are rebuilt from the database at startup, so patients, history and the
undo stack survive restarts. Tables: `patients`, `history`, `undo_log`.
Delete `hospital.db` or press Reset to start fresh.
