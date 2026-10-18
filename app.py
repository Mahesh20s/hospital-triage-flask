import os

from flask import Flask, render_template, request, redirect, url_for, flash, abort

from hospital import Hospital
from benchmark import run_benchmark

app = Flask(__name__)
app.secret_key = "change-this-secret-in-production"


DB_PATH = os.environ.get("HOSPITAL_DB", os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db"))


def seed(h):
    for name, sev in [("Asha", 3), ("Ravi", 9), ("Meena", 5), ("Karan", 9)]:
        h.admit(name, sev)
    h.clear_undo()


hospital = Hospital(DB_PATH)
if not hospital.patients:  # first run only: add sample patients
    seed(hospital)
last_benchmark = None


@app.route("/")
def index():
    q = request.args.get("q", "").strip()
    src, dst = request.args.get("src", ""), request.args.get("dst", "")
    path = hospital.graph.route(src, dst) if src and dst else None
    return render_template(
        "index.html", stats=hospital.stats(), waiting=hospital.waiting(),
        patients=hospital.sorted_patients(q), q=q, wards=hospital.graph.nodes(),
        src=src, dst=dst or "Ward-A", path=path, routed=bool(src and dst),
        undo_count=len(hospital.undo_stack), bench=last_benchmark)


@app.post("/admit")
def admit():
    name = request.form.get("name", "").strip()
    try:
        severity = int(request.form.get("severity", ""))
    except ValueError:
        severity = 0
    if not name or not 1 <= severity <= 10:
        flash("Enter a name and a severity from 1 to 10.", "error")
    else:
        pid = hospital.admit(name[:40], severity)
        flash(f"Admitted {name} as patient #{pid}.", "ok")
    return redirect(url_for("index"))


@app.post("/treat")
def treat():
    pid = hospital.treat_next()
    if pid:
        flash(f"Treating {hospital.patients[pid]['name']} (#{pid}).", "ok")
    else:
        flash("No patients are waiting.", "error")
    return redirect(url_for("index"))


@app.post("/undo")
def undo():
    op = hospital.undo()
    flash(f"Undid the last {op}." if op else "Nothing to undo.", "ok" if op else "error")
    return redirect(url_for("index"))


@app.post("/reset")
def reset():
    hospital.reset()
    seed(hospital)
    flash("System reset with sample patients.", "ok")
    return redirect(url_for("index"))


@app.post("/benchmark")
def benchmark():
    global last_benchmark
    last_benchmark = run_benchmark()
    return redirect(url_for("index") + "#performance")


@app.route("/patient/<int:pid>")
def patient(pid):
    p = hospital.patients.get(pid)
    if not p:
        abort(404)
    return render_template("patient.html", pid=pid, p=p, events=p["history"].to_list())


@app.errorhandler(404)
def not_found(_):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
