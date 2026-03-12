import os

os.environ.setdefault("FLASK_DEBUG", "1")
os.environ.setdefault("SECRET_KEY", "test-secret")

from app import app


def test_home_redirects_to_login():
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.get("/")
    assert resp.status_code in (301, 302)
    assert "/login" in resp.headers.get("Location", "")


def test_login_page_loads():
    app.config["TESTING"] = True
    client = app.test_client()
    resp = client.get("/login")
    assert resp.status_code == 200
    assert b"Login" in resp.data
