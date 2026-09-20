"""
Full authenticated end-to-end HTTP verification for AP ECET System.
Tests login → prediction → results → preference-list → export → admin flows.
"""
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import json

BASE = "http://127.0.0.1:5000"
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', 'Python-Test/1.0')]

passed = []
failed = []

def get(path, label=None, expect_code=200, expect_text=None):
    try:
        resp = opener.open(BASE + path, timeout=30)
        code = resp.getcode()
        body = resp.read().decode('utf-8', errors='replace')
        url = resp.geturl()
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode('utf-8', errors='replace')
        url = BASE + path

    ok = (code == expect_code)
    if expect_text and expect_text.lower() not in body.lower():
        ok = False
    
    info = f"HTTP {code} @ {url}"
    if label:
        status = "[PASS]" if ok else "[FAIL]"
        msg = f"{status} | {label} | {info}"
        if not ok:
            print(msg)
            snippet = body[:300].replace('\n', ' ')
            print(f"       BODY: {snippet}")
            failed.append(label)
        else:
            print(msg)
            passed.append(label)
    return code, body, url

def post(path, data, label=None, expect_code=200, expect_text=None, avoid_text=None):
    try:
        encoded = urllib.parse.urlencode(data).encode('utf-8')
        resp = opener.open(BASE + path, encoded, timeout=30)
        code = resp.getcode()
        body = resp.read().decode('utf-8', errors='replace')
        url = resp.geturl()
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode('utf-8', errors='replace')
        url = BASE + path

    ok = (code == expect_code)
    if expect_text and expect_text.lower() not in body.lower():
        ok = False
    if avoid_text and avoid_text.lower() in body.lower():
        ok = False
    
    if label:
        status = "[PASS]" if ok else "[FAIL]"
        msg = f"{status} | {label} | HTTP {code} @ {url}"
        if not ok:
            print(msg)
            snippet = body[:400].replace('\n', ' ')
            print(f"       BODY: {snippet}")
            failed.append(label)
        else:
            print(msg)
            passed.append(label)
    return code, body, url

print("=" * 70)
print("AP ECET Counselling Forecasting System — Full E2E Verification")
print("=" * 70)

# ---- AUTH FLOWS ----
print("\n[AUTH FLOWS]")
get('/login', 'Login page loads', expect_code=200, expect_text='Sign In')

# Student Login
code, body, url = post('/login', 
    {'email': 'student@apecet.gov.in', 'password': 'Student@12345'},
    'Student login', expect_code=200, avoid_text='Invalid email')
student_logged_in = 'dashboard' in url.lower() or 'dashboard' in body.lower()

# Student Dashboard
get('/dashboard', 'Student dashboard', expect_code=200, expect_text='Dashboard')

# ---- STUDENT FEATURES ----
print("\n[STUDENT FEATURES]")
get('/profile', 'Student profile page', expect_code=200)
get('/predict', 'Prediction form renders', expect_code=200, expect_text='rank')

# Run Prediction
code, body, url = post('/run-prediction', {
    'student_rank': '3500',
    'branch': 'COMPUTER SCIENCE AND ENGINEERING',
    'category': 'OC',
    'gender': 'BOYS',
    'region': 'AU',
    'counselling_round': 'Phase 1',
    'district': 'ALL',
    'college_type': 'ALL',
    'max_budget': '100000',
    'save_to_profile': '1'
}, 'Run prediction (CSE/OC/AU)', expect_code=200)

pred_ok = 'prediction' in url.lower() or 'results' in url.lower() or 'admission' in body.lower()
status = "[PASS]" if pred_ok else "[FAIL]"
print(f"{status} | Run prediction -> Results | Final URL: {url}")
if pred_ok:
    passed.append('Run prediction')
    # Check classification cards
    for tier in ['Safe', 'Moderate', 'Ambitious', 'Dream']:
        if tier.lower() in body.lower():
            print(f"  [PASS] {tier} classification cards found")
else:
    failed.append('Run prediction')
    print(f"       BODY snippet: {body[:300]}")

# Extract pred_id from URL for further tests
pred_id = None
if '/results/' in url:
    try:
        pred_id = int(url.split('/results/')[-1].rstrip('/'))
        print(f"  Prediction ID: {pred_id}")
    except:
        pass

# What-If Simulator
get('/what-if', 'What-If Simulator', expect_code=200)

# Colleges 
get('/colleges', 'College search page', expect_code=200)
get('/compare', 'College comparison page', expect_code=200)

# Analytics
get('/analytics', 'Cutoff analytics', expect_code=200)

# Calendar
get('/calendar', 'Counselling calendar', expect_code=200)

# Preferences
get('/preferences', 'Preference list page', expect_code=200)

# History
get('/history', 'Prediction history', expect_code=200)

# Saved Colleges
get('/saved', 'Saved colleges page', expect_code=200)

# ---- EXPORT FLOWS ----
print("\n[EXPORT FLOWS]")
if pred_id:
    get(f'/export/prediction-pdf/{pred_id}', 'PDF report download', expect_code=200)
get('/export/preference-csv', 'CSV preference export', expect_code=200)
get('/export/preference-pdf', 'PDF preference export', expect_code=200)

# ---- LOGOUT & ADMIN ----
print("\n[ADMIN FLOWS]")
get('/logout', 'Logout', expect_code=200)

code, body, url = post('/login',
    {'email': 'admin@apecet.gov.in', 'password': 'Admin@12345'},
    'Admin login', expect_code=200, avoid_text='Invalid email')

get('/admin', 'Admin dashboard', expect_code=200)
get('/admin/colleges', 'Admin colleges management', expect_code=200)
get('/admin/branches', 'Admin branches management', expect_code=200)
get('/admin/cutoffs', 'Admin cutoffs viewer', expect_code=200)
get('/admin/seat-matrix', 'Admin seat matrix', expect_code=200)
get('/admin/upload-csv', 'Admin CSV upload page', expect_code=200)
get('/admin/users', 'Admin users management', expect_code=200)
get('/admin/reports', 'Admin viva model evaluation report', expect_code=200)

# ---- SUMMARY ----
print("\n" + "=" * 70)
print("VERIFICATION SUMMARY")
print("=" * 70)
print(f"Total Tests: {len(passed) + len(failed)}")
print(f"Passed: {len(passed)}")
print(f"Failed: {len(failed)}")
if failed:
    print(f"\nFailed Tests: {', '.join(failed)}")
print("=" * 70)
