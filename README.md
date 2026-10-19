# Hospital Triage & Patient Management System

A Flask web application that manages emergency-room patients using core data structures, with SQLite for permanent storage.

Patients are treated by **severity, not arrival order**. The system finds records instantly, supports undo, keeps a full history for each patient, lists patients alphabetically, and finds the shortest route between hospital wards.

<!-- Add a screenshot: save it as docs/dashboard.png, then remove this line and the arrows around the next line -->
<!-- ![Dashboard](docs/dashboard.png) -->

## Features

- **Admit patients** with a severity from 1 to 10, with input validation
- **Treat next:** the most critical waiting patient is always treated first
- **Undo** the last admit or treatment, even after a server restart
- **Waiting queue** ordered by priority, with first come, first served for equal severity
- **Patient history** timeline with timestamps
- **Patients A to Z** with search by name or ID
- **Ward route finder** that gives the shortest route between wards
- **Dashboard** with live counts: total, waiting, critical and treated
- **Benchmark** page that compares each efficient structure with a naive one
- **Persistent data** in SQLite, plus a Reset button for demos
- Colour-coded severity, dark mode and a mobile-friendly layout

## Data structures used

| Feature | Data structure | Time complexity |
|---|---|---|
| Find a patient by ID | Hash table (`dict`) | O(1) average |
| Pick the next patient | Heap (priority queue) | O(log n) |
| Undo admit / treat | Stack | O(1) |
| Patient history | Linked list with tail pointer | O(1) append |
| Patients sorted by name | Binary search tree | O(n) in-order traversal |
| Ward routes | Graph (adjacency list) + BFS | O(V + E) |

The linked list, binary search tree and graph are implemented from scratch in `ds.py`.

## How it works

The data structures are the fast in-memory working set. SQLite stores the data permanently. When the app starts, it reads the database and rebuilds the hash table, heap, tree, linked lists and undo stack.

```
Browser  ->  Flask routes (app.py)  ->  Hospital logic (hospital.py)
                                          |                    |
                              Data structures (ds.py)      SQLite (hospital.db)
                              fast operations              permanent storage
```

Two design details:
- **Lazy deletion:** when a patient is undone, their old heap entry is skipped when popped, instead of being removed from the middle of the heap.
- **Ticket numbers:** each heap entry carries a ticket, which breaks ties fairly and prevents stale entries from being mistaken for current ones.

## Project structure

```
hospital_triage/
├── app.py            # Flask routes
├── hospital.py       # Core logic: structures + SQLite
├── ds.py             # Linked list, binary search tree, graph
├── benchmark.py      # Efficient vs naive performance comparison
├── requirements.txt
├── templates/        # base, index, patient and 404 pages
└── static/
    └── style.css
```

## Getting started

**Requirements:** Python 3.9 or newer.

```bash
git clone https://github.com/Mahesh20s/hospital-triage-flask.git
cd hospital-triage-flask
python -m pip install -r requirements.txt
python app.py
```

On Mac or Linux, use `python3` instead of `python`.

Open **http://127.0.0.1:5000** in your browser.

The database file `hospital.db` is created automatically on first run, with four sample patients. To start fresh, press **Reset** on the website or delete `hospital.db`.

## Database

SQLite with three tables:

| Table | Stores |
|---|---|
| `patients` | id, name, severity, status, ticket |
| `history` | each event for each patient, with a timestamp |
| `undo_log` | the undo stack, so undo survives restarts |

All queries use parameter placeholders, so the app is safe from SQL injection.

## Limitations and future improvements

- All data is loaded into memory at startup, so it suits thousands of patients, not millions
- The binary search tree is not self-balancing (an AVL tree would fix worst-case behaviour)
- The ward map is fixed, and routes count hops instead of real distances
- Planned: user login with roles, Dijkstra with real corridor distances, a REST API, and online deployment

## About

A data structures mini project built to show how choosing the right structure keeps a system fast, and to justify each choice with a real-world need.

Built by [@Mahesh20s](https://github.com/Mahesh20s)
