"""
End-to-end test for Phase 2 Topic Intelligence endpoints.
Registers a user (with DevShah09 CF handle), logs in, then hits all 5 endpoints.
"""
import sys, os, json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import requests

BASE = "http://127.0.0.1:8000"

def main():
    # ── 1. Register ──────────────────────────────────────────────────────────
    print("Registering test user (this triggers Codeforces sync, may take ~30s)...")
    r = requests.post(f"{BASE}/auth/register", json={
        "username": "devshah_test",
        "email": "devshah_test@test.com",
        "codeforces_handle": "DevShah09",
        "password": "Password123"
    }, timeout=90)
    if r.status_code == 201:
        print(f"Registered successfully.")
    elif r.status_code == 400 and "already" in r.text.lower():
        print(f"User already exists, proceeding to login.")
    else:
        print(f"Unexpected register status {r.status_code}: {r.text}")
        sys.exit(1)


    # ── 2. Login ─────────────────────────────────────────────────────────────
    print("Logging in...")
    r = requests.post(f"{BASE}/auth/login", json={
        "username": "devshah_test",
        "password": "Password123"
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    token = r.json()["access_token"]
    handle = r.json()["user"]["codeforces_handle"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"Logged in. Handle={handle}")

    # ── 3. Topic Analytics ────────────────────────────────────────────────────
    print("\n--- GET /topics/{handle} ---")
    r = requests.get(f"{BASE}/topics/{handle}", headers=headers)
    assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
    topics = r.json()["topics"]
    print(f"OK — {len(topics)} topics returned")
    for t in topics[:3]:
        print(f"  {t['topic']:30s} attempted={t['attempted']:3d}  solved={t['solved']:3d}  accuracy={t['accuracy']}%")

    # ── 4. Topic Mastery ──────────────────────────────────────────────────────
    print("\n--- GET /topics/{handle}/mastery ---")
    r = requests.get(f"{BASE}/topics/{handle}/mastery", headers=headers)
    assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
    masteries = r.json()["masteries"]
    print(f"OK — {len(masteries)} mastery entries returned")
    for m in masteries[:3]:
        print(f"  {m['topic']:30s} score={m['score']:3d}  level={m['strength']}")

    # ── 5. Topic Summary ──────────────────────────────────────────────────────
    print("\n--- GET /topics/{handle}/summary ---")
    r = requests.get(f"{BASE}/topics/{handle}/summary", headers=headers)
    assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
    s = r.json()
    print(f"OK — strongest={s['strongest_topic']}  weakest={s['weakest_topic']}")
    print(f"     avg_mastery={s['average_mastery']}  above75={s['topics_above_75']}  below60={s['topics_below_60']}")

    # ── 6. Weaknesses ─────────────────────────────────────────────────────────
    print("\n--- GET /weaknesses/{handle} ---")
    r = requests.get(f"{BASE}/weaknesses/{handle}", headers=headers)
    assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
    weaknesses = r.json()["weaknesses"]
    print(f"OK — {len(weaknesses)} weaknesses returned")
    for w in weaknesses[:3]:
        print(f"  {w['topic']:30s} score={w['score']:3d}  priority={w['priority']}")

    # ── 7. Strengths ──────────────────────────────────────────────────────────
    print("\n--- GET /strengths/{handle} ---")
    r = requests.get(f"{BASE}/strengths/{handle}", headers=headers)
    assert r.status_code == 200, f"FAIL: {r.status_code} {r.text}"
    strengths = r.json()["strengths"]
    print(f"OK — {len(strengths)} strong topics returned")
    for s in strengths[:3]:
        print(f"  {s['topic']:30s} score={s['score']:3d}")

    print("\n✓ All Phase 2 endpoint tests passed!")

if __name__ == "__main__":
    main()
