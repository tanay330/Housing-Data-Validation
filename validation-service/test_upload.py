import requests
import time

# ── Step 1: Login ─────────────────────────────────────────
login_response = requests.post(
    "http://localhost:8001/auth/login",
    json={
        "email": "tanay@test.com",
        "password": "test123"
    }
)
token = login_response.json()["access_token"]
print("✅ Login successful")

# ── Step 2: Upload CSV ────────────────────────────────────
with open("test_housing.csv", "rb") as f:
    upload_response = requests.post(
        "http://localhost:8000/validate/upload",
        headers={"Authorization": f"Bearer {token}"},
        files={"file": ("test_housing.csv", f, "text/csv")}
    )

upload_data = upload_response.json()
job_id = upload_data["job_id"]
print(f"✅ File uploaded — Job ID: {job_id}")

# ── Step 3: Wait for processing ───────────────────────────
print("⏳ Waiting 5 seconds for processing...")
time.sleep(5)

# ── Step 4: Check status ──────────────────────────────────
status_response = requests.get(
    f"http://localhost:8000/validate/status/{job_id}",
    headers={"Authorization": f"Bearer {token}"}
)
status_data = status_response.json()
print(f"\n📊 Job Status:")
print(f"   Status     : {status_data['status']}")
print(f"   Total rows : {status_data['total_rows']}")
print(f"   Valid rows : {status_data['valid_rows']}")
print(f"   Error rows : {status_data['error_rows']}")

# ── Step 5: Get error report ──────────────────────────────
errors_response = requests.get(
    f"http://localhost:8000/validate/errors/{job_id}",
    headers={"Authorization": f"Bearer {token}"}
)
errors_data = errors_response.json()
print(f"\n❌ Error Report — Total errors: {errors_data['total_errors']}")
for error in errors_data["errors"]:
    print(f"   Row {error['row_number']} | {error['column_name']} | {error['error_message']} | value: {error['raw_value']}")