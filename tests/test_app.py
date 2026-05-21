"""pytest suite for TaskPilot API."""
import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app()
    app.config["TESTING"] = True
    app.config["DATABASE"] = str(tmp_path / "test.db")
    with app.app_context():
        from app.database import init_db
        init_db(app)
    with app.test_client() as c:
        with c.session_transaction() as sess:
            sess["user"] = "test@example.com"
        yield c


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_create_and_list_tasks(client):
    r = client.post("/api/tasks", json={"title": "pytest task", "status": "todo"})
    assert r.status_code == 201
    tid = r.get_json()["task"]["id"]
    r2 = client.get("/api/tasks")
    assert any(t["id"] == tid for t in r2.get_json()["tasks"])


def test_export_json(client):
    client.post("/api/tasks", json={"title": "export me"})
    r = client.get("/api/tasks/export?format=json")
    assert r.status_code == 200
    assert "tasks" in r.get_json()


def test_activity_log(client):
    client.post("/api/tasks", json={"title": "logged task"})
    r = client.get("/api/activity")
    assert r.status_code == 200
    assert len(r.get_json()["activity"]) >= 1


def test_team_messages(client):
    client.post("/api/team", json={"name": "Alex", "role": "lead"})
    r = client.post("/api/team/messages", json={"content": "Hello @team"})
    assert r.status_code == 201
    r2 = client.get("/api/team/messages")
    assert len(r2.get_json()["messages"]) >= 1


def test_openapi(client):
    r = client.get("/api/openapi.json")
    assert r.status_code == 200
    assert "openapi" in r.get_json()
