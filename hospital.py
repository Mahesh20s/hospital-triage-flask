"""Core hospital logic.

Data structures are the fast in-memory working set; SQLite is the persistence
layer. On startup the structures are rebuilt from the database.
"""
import heapq
import sqlite3
from contextlib import contextmanager
from datetime import datetime

from ds import LinkedList, BST, Graph

SCHEMA = """
CREATE TABLE IF NOT EXISTS patients(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL, severity INTEGER NOT NULL,
    status TEXT NOT NULL, ticket INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS history(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL, event TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS undo_log(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    op TEXT NOT NULL, patient_id INTEGER NOT NULL);
"""


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Hospital:
    def __init__(self, db_path):
        self.db_path = db_path
        self.graph = Graph()
        for a, b in [("ER", "Radiology"), ("ER", "ICU"), ("Radiology", "Surgery"),
                     ("ICU", "Surgery"), ("Surgery", "Ward-A"), ("ICU", "Ward-B")]:
            self.graph.add_edge(a, b)
        with self._tx() as con:
            con.executescript(SCHEMA)
            # patient IDs start at 101
            if not con.execute("SELECT 1 FROM sqlite_sequence WHERE name='patients'").fetchone():
                con.execute("INSERT INTO sqlite_sequence(name, seq) VALUES('patients', 100)")
        self._load()

    # ----- database helpers -----
    @contextmanager
    def _tx(self):
        con = sqlite3.connect(self.db_path)
        try:
            yield con
            con.commit()
        finally:
            con.close()

    def _load(self):
        """Rebuild every in-memory structure from the database."""
        self.patients = {}        # hash table: id -> record (O(1) lookup)
        self.heap = []            # priority queue: (-severity, ticket, id)
        self.undo_stack = []      # stack of (operation, id, heap_entry)
        self.by_name = BST()      # tree: patients sorted by name
        with self._tx() as con:
            prows = con.execute("SELECT id, name, severity, status, ticket FROM patients ORDER BY id").fetchall()
            hrows = con.execute("SELECT patient_id, event, created_at FROM history ORDER BY id").fetchall()
            urows = con.execute("SELECT op, patient_id FROM undo_log ORDER BY id").fetchall()
        for pid, name, sev, status, ticket in prows:
            self.patients[pid] = {"name": name, "severity": sev, "status": status,
                                  "ticket": ticket, "history": LinkedList()}
            self.by_name.insert((name.lower(), pid), pid)
            if status == "waiting":
                self.heap.append((-sev, ticket, pid))
        heapq.heapify(self.heap)
        for pid, event, ts in hrows:
            if pid in self.patients:
                self.patients[pid]["history"].append({"event": event, "time": ts})
        for op, pid in urows:
            p = self.patients.get(pid)
            if p:
                self.undo_stack.append((op, pid, (-p["severity"], p["ticket"], pid)))
        self._next_ticket = max((p["ticket"] for p in self.patients.values()), default=-1) + 1

    def _log(self, con, pid, event):
        ts = _now()
        con.execute("INSERT INTO history(patient_id, event, created_at) VALUES(?,?,?)", (pid, event, ts))
        self.patients[pid]["history"].append({"event": event, "time": ts})

    # ----- operations -----
    def admit(self, name, severity):
        ticket = self._next_ticket
        self._next_ticket += 1
        with self._tx() as con:
            pid = con.execute(
                "INSERT INTO patients(name, severity, status, ticket) VALUES(?,?,?,?)",
                (name, severity, "waiting", ticket)).lastrowid
            self.patients[pid] = {"name": name, "severity": severity, "status": "waiting",
                                  "ticket": ticket, "history": LinkedList()}
            self._log(con, pid, f"Admitted with severity {severity}")
            con.execute("INSERT INTO undo_log(op, patient_id) VALUES('admit', ?)", (pid,))
        entry = (-severity, ticket, pid)
        heapq.heappush(self.heap, entry)
        self.by_name.insert((name.lower(), pid), pid)
        self.undo_stack.append(("admit", pid, entry))
        return pid

    def treat_next(self):
        while self.heap:
            entry = heapq.heappop(self.heap)
            _, ticket, pid = entry
            p = self.patients.get(pid)
            # lazy deletion: skip entries of undone / already-treated patients
            if p and p["status"] == "waiting" and p["ticket"] == ticket:
                with self._tx() as con:
                    con.execute("UPDATE patients SET status='treated' WHERE id=?", (pid,))
                    p["status"] = "treated"
                    self._log(con, pid, "Treated")
                    con.execute("INSERT INTO undo_log(op, patient_id) VALUES('treat', ?)", (pid,))
                self.undo_stack.append(("treat", pid, entry))
                return pid
        return None

    def undo(self):
        if not self.undo_stack:
            return None
        op, pid, entry = self.undo_stack.pop()
        with self._tx() as con:
            con.execute("DELETE FROM undo_log WHERE id = (SELECT MAX(id) FROM undo_log)")
            if op == "admit":
                con.execute("DELETE FROM history WHERE patient_id=?", (pid,))
                con.execute("DELETE FROM patients WHERE id=?", (pid,))
                del self.patients[pid]
            else:
                con.execute("UPDATE patients SET status='waiting' WHERE id=?", (pid,))
                self.patients[pid]["status"] = "waiting"
                self._log(con, pid, "Treatment undone")
                heapq.heappush(self.heap, entry)
        return op

    def clear_undo(self):
        with self._tx() as con:
            con.execute("DELETE FROM undo_log")
        self.undo_stack.clear()

    def reset(self):
        with self._tx() as con:
            for table in ("undo_log", "history", "patients"):
                con.execute(f"DELETE FROM {table}")
            con.execute("UPDATE sqlite_sequence SET seq=100 WHERE name='patients'")
        self._load()

    # ----- views -----
    def waiting(self):
        live = [e for e in self.heap
                if e[2] in self.patients
                and self.patients[e[2]]["status"] == "waiting"
                and self.patients[e[2]]["ticket"] == e[1]]
        return [(e[2], self.patients[e[2]]) for e in sorted(live)]

    def sorted_patients(self, query=""):
        rows = [(pid, self.patients[pid]) for pid in self.by_name.in_order()
                if pid in self.patients]
        q = query.lower()
        if q:
            rows = [(pid, p) for pid, p in rows if q in p["name"].lower() or q == str(pid)]
        return rows

    def stats(self):
        vals = self.patients.values()
        return {"total": len(self.patients),
                "waiting": sum(p["status"] == "waiting" for p in vals),
                "treated": sum(p["status"] == "treated" for p in vals),
                "critical": sum(p["status"] == "waiting" and p["severity"] >= 8 for p in vals)}
