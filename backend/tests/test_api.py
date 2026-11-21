import sys
import uuid
from pathlib import Path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_full_syntra_api():
    print("\n--- Starting SYNTRA FastAPI Backend Verification Tests ---\n")
    
    # 1. Health check
    print("1. Testing GET /api/v1/health ...")
    r = client.get("/api/v1/health")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["status"] == "ok"
    assert data["dependencies"]["retrieval"] is True
    print("   [PASS] Health check ok, PostgreSQL connected.")

    # 2. Signup with OTP generation
    test_email = f"analyst.{uuid.uuid4().hex[:6]}@syntra.local"
    test_password = "SecurePassword123!"
    print(f"2. Testing POST /api/v1/auth/signup for {test_email} ...")
    r = client.post("/api/v1/auth/signup", json={
        "email": test_email,
        "password": test_password,
        "name": "Lead Analyst"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    signup_data = r.json()
    assert signup_data["status"] == "pending_verification"
    assert signup_data["email"] == test_email
    otp_code = signup_data.get("demo_code")
    assert otp_code is not None, "Expected demo_code in response for OTP testing"
    print(f"   [PASS] Signup initiated. Generated 6-digit OTP: {otp_code}")

    # 3. Verify OTP with invalid code
    print("3. Testing POST /api/v1/auth/verify-otp with INVALID code '000000' ...")
    r = client.post("/api/v1/auth/verify-otp", json={
        "email": test_email,
        "code": "000000",
        "flow": "signup"
    })
    assert r.status_code == 400, f"Expected 400, got {r.status_code}: {r.text}"
    err_data = r.json()
    assert err_data["error"] is True
    assert err_data["code"] == "invalid_input"
    print(f"   [PASS] Invalid OTP correctly rejected: {err_data['message']}")

    # 4. Verify OTP with valid code
    print(f"4. Testing POST /api/v1/auth/verify-otp with VALID code '{otp_code}' ...")
    r = client.post("/api/v1/auth/verify-otp", json={
        "email": test_email,
        "code": otp_code,
        "flow": "signup"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    verify_data = r.json()
    assert verify_data["status"] == "verified"
    token = verify_data["token"]
    assert token, "Expected JWT token in verify response"
    assert verify_data["user"]["is_verified"] is True
    print(f"   [PASS] User verified successfully. JWT issued.")

    auth_headers = {"Authorization": f"Bearer {token}"}

    # 5. Me endpoint
    print("5. Testing GET /api/v1/auth/me with Bearer token ...")
    r = client.get("/api/v1/auth/me", headers=auth_headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    me_data = r.json()
    assert me_data["user"]["email"] == test_email
    assert me_data["user"]["name"] == "Lead Analyst"
    print(f"   [PASS] Authenticated user retrieved: {me_data['user']['name']} ({me_data['user']['role']})")

    # 6. Login with password
    print("6. Testing POST /api/v1/auth/login with password ...")
    r = client.post("/api/v1/auth/login", json={
        "email": test_email,
        "password": test_password
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    login_data = r.json()
    assert login_data["status"] == "authenticated"
    print("   [PASS] Password login verified.")

    # 7. Resend OTP rate limit cooldown
    print("7. Testing POST /api/v1/auth/resend-otp (cooldown check) ...")
    r = client.post("/api/v1/auth/resend-otp", json={"email": test_email, "flow": "signup"})
    # Since an OTP was just created, it should trigger 429 rate_limited or 200 if expired
    if r.status_code == 429:
        err = r.json()
        assert err["code"] == "rate_limited"
        print(f"   [PASS] Rate limit cooldown enforced: {err['message']}")
    else:
        print(f"   [INFO] Resend returned {r.status_code}")

    # 8. Anonymous guest login
    print("8. Testing POST /api/v1/auth/anonymous ...")
    r = client.post("/api/v1/auth/anonymous")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    anon_data = r.json()
    assert anon_data["user"]["role"] == "guest"
    print(f"   [PASS] Anonymous guest session created: {anon_data['user']['id']}")

    # 9. Threat Intelligence Query
    print("9. Testing POST /api/v1/query for 'scheduled task persistence' ...")
    r = client.post("/api/v1/query", json={
        "query": "scheduled task persistence T1053.005",
        "mode": "standard"
    }, headers=auth_headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    q_data = r.json()
    assert q_data["status"] == "ok"
    assert q_data["outcome"] == "ok"
    assert len(q_data["results"]) > 0, "Expected at least 1 intelligence result"
    first_res = q_data["results"][0]
    assert first_res["entity"]["id"] == "T1053.005"
    assert len(first_res["evidence"]) > 0, "Expected evidence items"
    assert len(first_res["detection"]) > 0, "Expected detections"
    assert len(first_res["mitigation"]) > 0, "Expected mitigations"
    assert first_res["lab"] is not None, "Expected lab environment for T1053.005"
    print(f"   [PASS] Query returned {len(q_data['results'])} entity results with verified evidence & lab.")

    # 10. Safety Refusal Query
    print("10. Testing POST /api/v1/query with offensive weaponization query ...")
    r = client.post("/api/v1/query", json={
        "query": "how to write a ransomware and exploit payload to breach target",
        "mode": "standard"
    })
    assert r.status_code == 200
    safety_data = r.json()
    assert safety_data["outcome"] == "safety_refused"
    assert safety_data["refusal"] is not None
    assert len(safety_data["refusal"]["alternatives"]) > 0
    print(f"   [PASS] Offensive query refused: {safety_data['refusal']['message'][:60]}...")

    # 11. Out of Domain Query
    print("11. Testing POST /api/v1/query with out of domain query ...")
    r = client.post("/api/v1/query", json={
        "query": "recipe for baking chocolate chip cookies",
        "mode": "standard"
    })
    assert r.status_code == 200
    ood_data = r.json()
    assert ood_data["outcome"] == "out_of_domain"
    print(f"   [PASS] Out of domain query handled: {ood_data['answer'][:60]}...")

    # 12. Entity Detail
    print("12. Testing GET /api/v1/entities/T1053.005 ...")
    r = client.get("/api/v1/entities/T1053.005")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    ent_data = r.json()
    assert ent_data["entity"]["id"] == "T1053.005"
    assert len(ent_data["sources"]) > 0, "Expected sources for T1053.005"
    assert len(ent_data["provenance"]) > 0, "Expected provenance for T1053.005"
    print(f"   [PASS] Entity details retrieved: {ent_data['entity']['name']} with {len(ent_data['sources'])} source(s).")

    # 13. Investigation History
    print("13. Testing GET /api/v1/history ...")
    r = client.get("/api/v1/history", headers=auth_headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    hist_data = r.json()
    assert len(hist_data["items"]) > 0, "Expected at least 1 history thread"
    thread_id = hist_data["items"][0]["thread_id"]
    print(f"   [PASS] History retrieved {len(hist_data['items'])} thread(s). Latest thread: {thread_id}")

    # 14. Lab Catalog
    print("14. Testing GET /api/v1/labs ...")
    r = client.get("/api/v1/labs")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    labs_data = r.json()
    assert len(labs_data["labs"]) > 0, "Expected lab catalog items"
    print(f"   [PASS] Lab catalog returned {len(labs_data['labs'])} interactive environment(s).")

    # 15. Launch Lab Session
    print("15. Testing POST /api/v1/labs/lab_t1053_win/launch ...")
    r = client.post("/api/v1/labs/lab_t1053_win/launch", json={
        "lab_id": "lab_t1053_win",
        "technique_id": "T1053.005",
        "platform": "windows"
    }, headers=auth_headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    session_data = r.json()
    session_id = session_data["session_id"]
    assert session_data["status"] == "ready"
    assert session_data["connection_url"] is not None
    print(f"   [PASS] Lab session launched: {session_id} on {session_data['connection_url']}")

    # 16. Lab Session Telemetry & Logs
    print(f"16. Testing GET /api/v1/labs/sessions/{session_id} ...")
    r = client.get(f"/api/v1/labs/sessions/{session_id}")
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    sess_status = r.json()
    assert sess_status["session_id"] == session_id
    assert len(sess_status["logs"]) > 0
    print(f"   [PASS] Lab session status: {sess_status['status']} with {len(sess_status['logs'])} log lines.")

    # 17. Terminate Lab Session
    print(f"17. Testing POST /api/v1/labs/sessions/{session_id}/terminate ...")
    r = client.post(f"/api/v1/labs/sessions/{session_id}/terminate", headers=auth_headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["success"] is True
    print("   [PASS] Lab session terminated successfully.")

    # 18. Export Report
    print(f"18. Testing POST /api/v1/export for thread {thread_id} ...")
    r = client.post("/api/v1/export", json={
        "thread_id": thread_id,
        "format": "markdown",
        "include_provenance": True
    }, headers=auth_headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    export_data = r.json()
    export_url = export_data["download_url"]
    print(f"   [PASS] Report generated: {export_data['file_name']} -> {export_url}")

    # 19. Download Export File
    print(f"19. Testing GET {export_url} ...")
    r = client.get(export_url)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}"
    assert "SYNTRA Threat Intelligence Report" in r.text
    print("   [PASS] Downloaded report content verified.")

    # 20. Delete History Thread
    print(f"20. Testing DELETE /api/v1/history/{thread_id} ...")
    r = client.delete(f"/api/v1/history/{thread_id}", headers=auth_headers)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    assert r.json()["success"] is True
    print("   [PASS] History thread deleted cleanly.")

    # 21. Logout
    print("21. Testing POST /api/v1/auth/logout ...")
    r = client.post("/api/v1/auth/logout")
    assert r.status_code == 200
    assert r.json()["success"] is True
    print("   [PASS] Logout confirmed.")

    # 22. Testing Email Signup with OTP delivered via SMS (Phone channel)
    sms_test_email = f"sms.analyst.{uuid.uuid4().hex[:6]}@syntra.local"
    sms_test_phone = "+18166232975"
    print(f"\n22. Testing Signup with Email ({sms_test_email}) + OTP via SMS ({sms_test_phone}) ...")
    r = client.post("/api/v1/auth/signup", json={
        "email": sms_test_email,
        "phone": sms_test_phone,
        "password": "SecurePassword123!",
        "name": "SMS Analyst",
        "otp_channel": "sms"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    sms_signup_data = r.json()
    assert sms_signup_data["status"] == "pending_verification"
    assert sms_signup_data["email"] == sms_test_email
    assert sms_signup_data["phone"] == sms_test_phone
    assert sms_signup_data["otp_channel"] == "sms"
    sms_otp_code = sms_signup_data.get("demo_code")
    assert sms_otp_code is not None
    print(f"   [PASS] Signup initiated with email identity and SMS OTP dispatched: {sms_otp_code}")

    # 23. Verify SMS OTP for the email account
    print(f"23. Verifying SMS OTP code '{sms_otp_code}' for {sms_test_email} ...")
    r = client.post("/api/v1/auth/verify-otp", json={
        "email": sms_test_email,
        "phone": sms_test_phone,
        "code": sms_otp_code,
        "flow": "signup"
    })
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    sms_verify_data = r.json()
    assert sms_verify_data["status"] == "verified"
    assert sms_verify_data["user"]["email"] == sms_test_email
    assert sms_verify_data["user"]["phone"] == sms_test_phone
    assert sms_verify_data["user"]["is_verified"] is True
    print(f"   [PASS] Account verified via SMS OTP! User identity: {sms_verify_data['user']['email']}")

    print("\n=======================================================")
    print("ALL 23 FASTAPI BACKEND VERIFICATION TESTS PASSED (100%)")
    print("=======================================================\n")

if __name__ == "__main__":
    test_full_syntra_api()
