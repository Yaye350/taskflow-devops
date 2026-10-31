"""API de gestion de tâches (Flask) avec persistance dans un fichier JSON."""
import json
import os
import threading

from flask import Flask, jsonify, request

DATA_FILE = os.environ.get("DATA_FILE", "data/tasks.json")
_lock = threading.Lock()


def _load(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(path, tasks):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(tasks, f, ensure_ascii=False, indent=2)


def create_app(data_file=None):
    app = Flask(__name__)
    path = data_file or DATA_FILE

    @app.get("/health")
    def health():
        return jsonify(status="ok"), 200

    @app.get("/tasks")
    def list_tasks():
        with _lock:
            return jsonify(_load(path)), 200

    @app.post("/tasks")
    def create_task():
        body = request.get_json(silent=True) or {}
        title = (body.get("title") or "").strip()
        if not title:
            return jsonify(error="Le champ 'title' est obligatoire"), 400
        with _lock:
            tasks = _load(path)
            new_id = max((t["id"] for t in tasks), default=0) + 1
            task = {"id": new_id, "title": title, "done": False}
            tasks.append(task)
            _save(path, tasks)
        return jsonify(task), 201

    @app.get("/tasks/<int:task_id>")
    def get_task(task_id):
        with _lock:
            for t in _load(path):
                if t["id"] == task_id:
                    return jsonify(t), 200
        return jsonify(error="Tâche introuvable"), 404

    @app.put("/tasks/<int:task_id>")
    def update_task(task_id):
        body = request.get_json(silent=True) or {}
        with _lock:
            tasks = _load(path)
            for t in tasks:
                if t["id"] == task_id:
                    if "title" in body:
                        title = (body["title"] or "").strip()
                        if not title:
                            return jsonify(error="Titre invalide"), 400
                        t["title"] = title
                    if "done" in body:
                        t["done"] = bool(body["done"])
                    _save(path, tasks)
                    return jsonify(t), 200
        return jsonify(error="Tâche introuvable"), 404

    @app.delete("/tasks/<int:task_id>")
    def delete_task(task_id):
        with _lock:
            tasks = _load(path)
            remaining = [t for t in tasks if t["id"] != task_id]
            if len(remaining) == len(tasks):
                return jsonify(error="Tâche introuvable"), 404
            _save(path, remaining)
        return "", 204

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
