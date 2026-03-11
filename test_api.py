"""Quick test script to verify login API against the database."""
import urllib.request
import json


BASE_URL = "http://localhost:5000"


def post_login(campus_id, password):
    data = json.dumps({"campusID": campus_id, "password": password}).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/api/login",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test(label, campus_id, password, expected_status):
    status, body = post_login(campus_id, password)
    passed = status == expected_status
    icon = "PASS" if passed else "FAIL"
    print(f"[{icon}] {label}")
    print(f"       Status: {status} (expected {expected_status})")
    print(f"       Body:   {body}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("ELEV8 Login API Tests")
    print("=" * 60)
    print()

    test("Invalid campus ID → 401", "nonexistent", "anypassword123", 401)
    test("Valid campus ID bclark11 + wrong password → 401", "bclark11", "wrongpassword123", 401)
    test("Missing password (too short) → 400", "bclark11", "short", 400)
    test("Empty campus ID → 400", "", "anypassword123", 400)
