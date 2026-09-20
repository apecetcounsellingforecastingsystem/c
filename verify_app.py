"""
Programmatic HTTP verification for AP ECET Counselling Forecasting System.
Tests all major routes and reports results.
"""
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json

BASE = "http://127.0.0.1:5000"

# Setup cookie-aware opener
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Mozilla/5.0')]

PASS = "[PASS]"
FAIL = "[FAIL]"

results = []

def get(path):
    try:
        resp = opener.open(BASE + path, timeout=10)
        return resp.getcode(), resp.read().decode('utf-8', errors='replace'), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace'), BASE + path
    except Exception as ex:
        return 0, str(ex), BASE + path

def post(path, data):
    try:
        encoded = urllib.parse.urlencode(data).encode('utf-8')
        resp = opener.open(BASE + path, encoded, timeout=15)
        return resp.getcode(), resp.read().decode('utf-8', errors='replace'), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', errors='replace'), BASE + path
    except Exception as ex:
        return 0, str(ex), BASE + path

def check(label, code, body, url, expect_code=200, expect_text=None, avoid_text=None):
    ok = code == expect_code
    if expect_text and expect_text.lower() not in body.lower():
        ok = False
    if avoid_text and avoid_text.lower() in body.lower():
        ok = False
    status = PASS if ok else FAIL
    note = f"HTTP {code} | URL: {url}"
    if not ok:
        if expect_text and expect_text.lower() not in body.lower():
            note += f" | Missing: '{expect_text}'"
        if avoid_text and avoid_text.lower() in body.lower():
            note += f" | Found unwanted: '{avoid_text}'"
        # Print snippet of body for debugging
        note += f"\n   BODY SNIPPET: {body[:400]}"
    results.append(f"{status} {label}: {note}")
    print(results[-1])
    return ok

print("=" * 70)
print("AP ECET Counselling Forecasting System — Verification Suite")
print("=" * 70)

# 1. Landing page redirect to login
code, body, url = get('/')
check("Root redirect to login", code, body, url, expect_code=200, expect_text="Sign In")

# 2. Login page renders
code, body, url = get('/login')
check("Login page renders", code, body, url, expect_code=200, expect_text="Sign In")

# 3. Student login
code, body, url = post('/login', {'email': 'student@apecet.gov.in', 'password': 'Student@123'})
student_login_ok = check("Student login", code, body, url, expect_code=200, avoid_text="Invalid credentials")
if not student_login_ok:
    # Try alternate password
    code, body, url = post('/login', {'email': 'student@apecet.gov.in', 'password': 'student123'})
    student_login_ok = check("Student login (alt password)", code, body, url, expect_code=200, avoid_text="Invalid credentials")

# 4. Student dashboard
code, body, url = get('/student/dashboard')
check("Student dashboard", code, body, url, expect_code=200, expect_text="dashboard")

# 5. Prediction form
code, body, url = get('/predict')
check("Predict form renders", code, body, url, expect_code=200, expect_text="rank")

# 6. Submit prediction
pred_data = {
    'ecet_rank': '5000',
    'category': 'OC',
    'gender': 'Male',
    'region': 'AU',
    'branch_preference': 'CSE',
    'round_no': '1'
}
code, body, url = post('/predict', pred_data)
pred_ok = check("Prediction results", code, body, url, expect_code=200, avoid_text="500 Internal Server Error")
if 'safe' in body.lower() or 'moderate' in body.lower() or 'ambitious' in body.lower():
    print(f"  -> Probability cards found in results page!")
else:
    print(f"  -> WARNING: Could not find Safe/Moderate/Ambitious cards in results")

# 7. Analytics page
code, body, url = get('/analytics')
check("Analytics page", code, body, url, expect_code=200)

# 8. Colleges listing
code, body, url = get('/colleges')
check("Colleges listing", code, body, url, expect_code=200)

# 9. Preference list
code, body, url = get('/preference-list')
check("Preference list", code, body, url, expect_code=200)

# 10. Logout
code, body, url = get('/logout')
check("Student logout", code, body, url, expect_code=200, expect_text="Sign In")

# 11. Admin login
code, body, url = post('/login', {'email': 'admin@apecet.gov.in', 'password': 'Admin@123'})
admin_login_ok = check("Admin login", code, body, url, expect_code=200, avoid_text="Invalid credentials")
if not admin_login_ok:
    code, body, url = post('/login', {'email': 'admin@apecet.gov.in', 'password': 'admin123'})
    admin_login_ok = check("Admin login (alt password)", code, body, url, expect_code=200, avoid_text="Invalid credentials")

# 12. Admin dashboard
code, body, url = get('/admin')
check("Admin dashboard", code, body, url, expect_code=200)

# 13. Admin colleges
code, body, url = get('/admin/colleges')
check("Admin colleges page", code, body, url, expect_code=200)

# 14. Admin reports
code, body, url = get('/admin/reports')
check("Admin reports page", code, body, url, expect_code=200)

# 15. API endpoints
code, body, url = get('/api/colleges')
try:
    data = json.loads(body)
    print(f"  -> /api/colleges returned {len(data)} records")
    check("API /api/colleges", code, body, url, expect_code=200)
except:
    check("API /api/colleges", code, body, url, expect_code=200)

print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
passes = sum(1 for r in results if r.startswith(PASS))
fails = sum(1 for r in results if r.startswith(FAIL))
print(f"Total: {len(results)} | Passed: {passes} | Failed: {fails}")
print("=" * 70)
