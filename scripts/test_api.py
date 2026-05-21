#!/usr/bin/env python3
"""Quick integration test for TaskPilot API (run with server on localhost:5000)."""
import json
import urllib.request
import http.cookiejar

BASE = "http://127.0.0.1:5000"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def req(method, path, data=None):
    url = BASE + path
    body = json.dumps(data).encode() if data is not None else None
    r = urllib.request.Request(url, data=body, method=method)
    if body:
        r.add_header("Content-Type", "application/json")
    with opener.open(r, timeout=10) as res:
        return json.loads(res.read().decode())


def main():
    print("[1] health", req("GET", "/api/health"))
    # login via form
    login_data = "email=manager@company.com&password=demo".encode()
    r = urllib.request.Request(BASE + "/login/", data=login_data, method="POST")
    r.add_header("Content-Type", "application/x-www-form-urlencoded")
    opener.open(r).read()

    print("[2] seed", req("POST", "/api/seed-demo"))
    chat = req("POST", "/api/chat", {"message": "add task Test API integration urgent due tomorrow"})
    assert "reply" in chat and chat["tasks"], "chat failed"
    print("[3] chat create OK, tasks:", len(chat["tasks"]))
    chat2 = req("POST", "/api/chat", {"message": "top priorities"})
    assert "Top priorities" in chat2["reply"], chat2["reply"]
    print("[4] priorities OK")
    dash = req("GET", "/api/dashboard")
    assert "stats" in dash, dash
    print("[5] dashboard OK", dash["stats"]["completion_pct"], "%")
    print("All tests passed.")


if __name__ == "__main__":
    main()
