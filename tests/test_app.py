import pytest

from app.main import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "tasks.json"))
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.get_json() == {"status": "ok"}


def test_list_empty(client):
    assert client.get("/tasks").get_json() == []


def test_create_task(client):
    r = client.post("/tasks", json={"title": "Écrire le rapport"})
    assert r.status_code == 201
    assert r.get_json() == {"id": 1, "title": "Écrire le rapport", "done": False}


def test_create_task_without_title(client):
    assert client.post("/tasks", json={}).status_code == 400
    assert client.post("/tasks", json={"title": "   "}).status_code == 400


def test_get_task_and_404(client):
    client.post("/tasks", json={"title": "A"})
    assert client.get("/tasks/1").status_code == 200
    assert client.get("/tasks/99").status_code == 404


def test_update_task(client):
    client.post("/tasks", json={"title": "A"})
    r = client.put("/tasks/1", json={"done": True, "title": "B"})
    assert r.status_code == 200
    assert r.get_json()["done"] is True
    assert r.get_json()["title"] == "B"
    assert client.put("/tasks/42", json={"done": True}).status_code == 404


def test_delete_task(client):
    client.post("/tasks", json={"title": "A"})
    assert client.delete("/tasks/1").status_code == 204
    assert client.get("/tasks").get_json() == []
    assert client.delete("/tasks/1").status_code == 404


def test_persistence(tmp_path):
    f = str(tmp_path / "t.json")
    create_app(f).test_client().post("/tasks", json={"title": "Persistée"})
    assert len(create_app(f).test_client().get("/tasks").get_json()) == 1
