"""
AP ECET Counselling Forecasting System — Master Flask Application
Full-stack implementation providing all 28 features:
- Authentication with OTP simulation & role-based sessions
- Hybrid Forecasting Engine (Linear Regression, Decision Tree, Random Forest)
- Explainable AI Recommendations (Safe, Moderate, Ambitious, Dream)
- Cutoff Analytics with Chart.js
- Smart Preference List Generator with PDF / CSV export
- Full Admin back-office & Viva Model Evaluation Reports
"""

import os
import io
import csv
import json
import sqlite3
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    session, jsonify, send_file, make_response
)
from werkzeug.security import generate_password_hash, check_password_hash
from database import get_db_connection, init_db
from forecasting_engine import forecasting_engine
from pdf_generator import generate_prediction_report_pdf, generate_preference_list_pdf

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'apecet_forecasting_secret_key_2026_x7z')

# Custom Jinja2 Filters
@app.template_filter('intcomma')
def intcomma_filter(value):
    """Format an integer with thousands-separator commas. {{ 12345 | intcomma }} → 12,345"""
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return value

@app.template_filter('inr')
def inr_filter(value):
    """Format as Indian Rupees with comma separator. {{ 75000 | inr }} → ₹ 75,000"""
    try:
        return f"₹ {int(value):,}"
    except (TypeError, ValueError):
        return f"₹ {value}"

# ---------------------------------------------------------------------------
# Auth Helper Decorators
# ---------------------------------------------------------------------------
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please sign in with administrator credentials.', 'warning')
            return redirect(url_for('admin_login'))
        if session.get('role') != 'admin':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('student_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ---------------------------------------------------------------------------
# Authentication Routes (Feature 1)
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as cnt FROM colleges WHERE is_active = 1")
        row = cursor.fetchone()
        total_colleges = row['cnt'] if row and row['cnt'] else 25
        conn.close()
    except Exception:
        total_colleges = 25
    return render_template('index.html', total_colleges=total_colleges)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return render_template('auth/login.html')

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['role'] = user['role']
            flash(f'Welcome back, {user["username"]}!', 'success')

            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('profile_page'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('This administrator account has been deactivated.', 'danger')
                return render_template('auth/login_admin.html')

            if user['role'] != 'admin':
                flash('Candidate accounts cannot access the Administrator Portal. Please use the Student Login portal.', 'warning')
                return redirect(url_for('login'))

            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['role'] = user['role']
            flash(f'Welcome back, Administrator {user["username"]}!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid administrator email or password. Please try again.', 'danger')

    return render_template('auth/login_admin.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Password must be at least 8 characters long.', 'danger')
            return render_template('auth/register.html')

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, username))
        existing = cursor.fetchone()

        if existing:
            conn.close()
            flash('Email or username is already registered. Please login.', 'warning')
            return redirect(url_for('login'))

        # Create user
        cursor.execute("""
        INSERT INTO users (username, email, phone, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, 'student', 1)
        """, (username, email, phone, generate_password_hash(password)))
        
        user_id = cursor.lastrowid
        
        # Initialize empty student profile
        cursor.execute("""
        INSERT INTO student_profiles (user_id, rank, category, gender, region, preferred_branch)
        VALUES (?, 850, 'OC', 'BOYS', 'AU', 'COMPUTER SCIENCE AND ENGINEERING')
        """, (user_id,))

        conn.commit()
        conn.close()

        flash('Registration successful! Please login with your credentials.', 'success')
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        flash(f'If {email} is registered, password recovery instructions have been sent.', 'info')
        return redirect(url_for('login'))
    return render_template('auth/forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been signed out successfully.', 'info')
    return redirect(url_for('login'))

# ---------------------------------------------------------------------------
# Student Dashboard & Profile Routes (Features 2, 15, 16, 17, 18)
# ---------------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def student_dashboard():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get student profile
    cursor.execute("""
    SELECT p.*, u.username, u.email, u.phone 
    FROM student_profiles p
    JOIN users u ON p.user_id = u.id
    WHERE p.user_id = ?
    """, (user_id,))
    profile = cursor.fetchone() or {}

    # Total predictions
    cursor.execute("SELECT count(*) FROM predictions WHERE user_id = ?", (user_id,))
    total_predictions = cursor.fetchone()[0]

    # Saved colleges count
    cursor.execute("SELECT count(*) FROM saved_colleges WHERE user_id = ?", (user_id,))
    saved_count = cursor.fetchone()[0]

    # Preference list count
    cursor.execute("SELECT count(*) FROM preference_lists WHERE user_id = ?", (user_id,))
    pref_count = cursor.fetchone()[0]

    # Active notifications
    cursor.execute("SELECT * FROM notifications WHERE is_active = 1 ORDER BY publish_date DESC LIMIT 4")
    notifications = cursor.fetchall()

    # Recent predictions
    cursor.execute("""
    SELECT * FROM predictions 
    WHERE user_id = ? 
    ORDER BY created_at DESC LIMIT 3
    """, (user_id,))
    recent_predictions = cursor.fetchall()

    conn.close()

    return render_template(
        'student/dashboard.html',
        profile=profile,
        total_predictions=total_predictions,
        saved_count=saved_count,
        pref_count=pref_count,
        notifications=notifications,
        recent_predictions=recent_predictions
    )

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        phone = request.form.get('phone', '') or request.form.get('mobile', '')
        try:
            rank = int(request.form.get('rank') or 850)
        except (ValueError, TypeError):
            rank = 850
        category = request.form.get('category', 'OC')
        gender = request.form.get('gender', 'Boys')
        region = request.form.get('region') or request.form.get('local_area', 'AU')
        diploma_branch = request.form.get('diploma_branch', 'Computer Engineering')
        preferred_branch = request.form.get('preferred_branch', 'Computer Science & Engineering')
        alternative_branch = request.form.get('alternative_branch', 'None')
        district = request.form.get('district') or request.form.get('preferred_district', 'Any')
        college_type = request.form.get('college_type', 'Any')

        if username:
            try:
                cursor.execute("UPDATE users SET username = ?, phone = ? WHERE id = ?", (username, phone, user_id))
                session['username'] = username
            except Exception:
                cursor.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user_id))
        else:
            cursor.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user_id))

        cursor.execute("""
        INSERT OR REPLACE INTO student_profiles 
        (user_id, rank, category, gender, region, district, preferred_branch, college_type, diploma_branch, alternative_branch, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, rank, category, gender, region, district, preferred_branch, college_type, diploma_branch, alternative_branch))
        conn.commit()
        conn.close()

        flash('Candidate profile updated successfully.', 'success')
        return redirect(url_for('student_dashboard'))

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone() or {}

    cursor.execute("SELECT DISTINCT branch_code, branch_name FROM branches ORDER BY branch_name")
    branches = cursor.fetchall()

    conn.close()
    return render_template('student/profile.html', user=user, profile=profile, branches=branches)

# ---------------------------------------------------------------------------
# AP ECET Admission Prediction & Recommendations (Features 3, 4, 5, 6, 7, 14)
# ---------------------------------------------------------------------------
@app.route('/predict', methods=['GET'])
@login_required
def predict_page():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone() or {}

    cursor.execute("SELECT DISTINCT branch_code, branch_name FROM branches ORDER BY branch_name")
    branches = cursor.fetchall()

    cursor.execute("SELECT DISTINCT district FROM colleges WHERE district IS NOT NULL AND district != '' ORDER BY district")
    districts = [r[0] for r in cursor.fetchall()]

    conn.close()
    return render_template('student/predict.html', profile=profile, branches=branches, districts=districts)

@app.route('/run-prediction', methods=['POST'])
@login_required
def run_prediction():
    user_id = session['user_id']
    
    student_rank = int(request.form.get('student_rank', 850))
    branch = request.form.get('branch', 'COMPUTER SCIENCE AND ENGINEERING')
    category = request.form.get('category', 'OC')
    gender = request.form.get('gender', 'BOYS')
    region = request.form.get('region', 'AU')
    counselling_round = request.form.get('counselling_round', 'Phase 1')
    district = request.form.get('district', 'ALL')
    college_type = request.form.get('college_type', 'ALL')
    max_budget = int(request.form.get('max_budget') or 150000)
    save_to_profile = request.form.get('save_to_profile') == '1'

    # Save to profile if requested
    if save_to_profile:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT OR REPLACE INTO student_profiles
        (user_id, rank, category, gender, region, district, preferred_branch, counselling_round, college_type, max_budget, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, student_rank, category, gender, region, district, branch, counselling_round, college_type, max_budget))
        conn.commit()
        conn.close()

    # Run forecasting engine
    recommendations = forecasting_engine.predict_and_recommend(
        rank=student_rank,
        category=category,
        gender=gender,
        branch=branch,
        counselling_round=counselling_round,
        region=region,
        district=district,
        college_type=college_type,
        max_budget=max_budget
    )

    # Log prediction into database
    conn = get_db_connection()
    cursor = conn.cursor()
    top_col = recommendations[0]['college_name'] if recommendations else 'N/A'
    top_prob = recommendations[0]['admission_probability'] if recommendations else 0.0
    top_cls = recommendations[0]['classification'] if recommendations else 'Safe'

    # Clean recs for json storage
    clean_recs = []
    for r in recommendations[:50]:
        fee = r.get('annual_fee', 45000)
        clean_recs.append({
            'college_code': r['college_code'],
            'college_name': r['college_name'],
            'branch_name': r.get('branch_name', branch),
            'place': r.get('place', 'AP'),
            'district': r.get('district', 'ALL'),
            'region': r.get('region', 'AU'),
            'affiliated_to': r.get('affiliated_to', 'AP State University'),
            'annual_fee': fee,
            'total_course_cost': r.get('total_course_cost', fee * 3),
            'total_intake_seats': r.get('total_intake_seats', 60),
            'expected_cutoff': r['expected_cutoff'],
            'admission_probability': r['admission_probability'],
            'classification': r['classification'],
            'reasons': r['reasons'],
            'cutoffs_by_year': r['cutoffs_by_year']
        })

    cursor.execute("""
    INSERT INTO predictions 
    (user_id, student_rank, category, gender, region, branch, counselling_round, district, college_type, max_budget,
     total_recommended, top_college_name, top_probability, top_classification, results_json)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, student_rank, category, gender, region, branch, counselling_round, district, college_type, max_budget,
        len(recommendations), top_col, top_prob, top_cls, json.dumps(clean_recs)
    ))
    pred_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return redirect(url_for('view_prediction_results', pred_id=pred_id))

@app.route('/results/<int:pred_id>')
@login_required
def view_prediction_results(pred_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
    pred_row = cursor.fetchone()
    conn.close()

    if not pred_row:
        flash('Prediction record not found.', 'danger')
        return redirect(url_for('predict_page'))

    student_data = {
        'student_rank': pred_row['student_rank'],
        'branch': pred_row['branch'],
        'category': pred_row['category'],
        'gender': pred_row['gender'],
        'region': pred_row['region'],
        'counselling_round': pred_row['counselling_round'],
        'district': pred_row['district'],
        'college_type': pred_row['college_type'],
        'max_budget': pred_row['max_budget']
    }

    recommendations = json.loads(pred_row['results_json'] or '[]')

    return render_template(
        'student/results.html',
        pred_id=pred_id,
        student_data=student_data,
        recommendations=recommendations
    )

# ---------------------------------------------------------------------------
# What-If Simulator (Feature 9)
# ---------------------------------------------------------------------------
@app.route('/what-if')
@login_required
def what_if_page():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM student_profiles WHERE user_id = ?", (user_id,))
    prof_row = cursor.fetchone()
    prof = dict(prof_row) if prof_row else {}

    cursor.execute("SELECT DISTINCT branch_code, branch_name FROM branches ORDER BY branch_name")
    branches = cursor.fetchall()
    conn.close()

    # Simulator parameters
    rank_a = int(request.args.get('rank_a', prof.get('rank', 850)))
    branch_a = request.args.get('branch_a', prof.get('preferred_branch', 'COMPUTER SCIENCE AND ENGINEERING'))
    round_a = request.args.get('round_a', 'Phase 1')

    rank_b = int(request.args.get('rank_b', rank_a - 150 if rank_a > 200 else rank_a + 300))
    branch_b = request.args.get('branch_b', 'ELECTRONICS AND COMMUNICATION ENGINEERING')
    round_b = request.args.get('round_b', 'Final Phase')

    category = request.args.get('category', prof.get('category', 'BC-B'))
    gender = request.args.get('gender', prof.get('gender', 'BOYS'))
    region = prof.get('region', 'AU')

    sim = {
        'rank_a': rank_a,
        'branch_a': branch_a,
        'round_a': round_a,
        'rank_b': rank_b,
        'branch_b': branch_b,
        'round_b': round_b,
        'category': category,
        'gender': gender
    }

    # Run predictions for Scenario A and Scenario B
    res_a = forecasting_engine.predict_and_recommend(
        rank=rank_a, category=category, gender=gender, branch=branch_a, counselling_round=round_a, region=region
    )
    res_b = forecasting_engine.predict_and_recommend(
        rank=rank_b, category=category, gender=gender, branch=branch_b, counselling_round=round_b, region=region
    )

    return render_template(
        'student/what_if.html',
        branches=branches,
        sim=sim,
        res_a=res_a,
        res_b=res_b
    )

# ---------------------------------------------------------------------------
# Smart Preference List Generator (Feature 8, 28)
# ---------------------------------------------------------------------------
@app.route('/preferences')
@login_required
def preferences_page():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT * FROM preference_lists 
    WHERE user_id = ? 
    ORDER BY preference_order ASC
    """, (user_id,))
    preferences = cursor.fetchall()
    conn.close()

    return render_template('student/preference_list.html', preferences=preferences)

@app.route('/api/preference-list/add', methods=['POST'])
@login_required
def api_add_preference():
    user_id = session['user_id']
    data = request.get_json() or {}

    college_code = data.get('college_code')
    college_name = data.get('college_name')
    branch_name = data.get('branch_name')
    district = data.get('district')
    classification = data.get('classification', 'Safe')
    probability = float(data.get('probability', 85.0))
    closing_rank = int(data.get('closing_rank', 1200))
    fees = int(data.get('fees', 45000))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine next preference order
    cursor.execute("SELECT max(preference_order) FROM preference_lists WHERE user_id = ?", (user_id,))
    max_order = cursor.fetchone()[0] or 0
    new_order = max_order + 1

    cursor.execute("""
    INSERT INTO preference_lists 
    (user_id, preference_order, college_code, college_name, branch_name, district, classification, probability, closing_rank, fees)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, new_order, college_code, college_name, branch_name, district, classification, probability, closing_rank, fees))

    conn.commit()
    conn.close()

    return jsonify({'success': True, 'order': new_order})

@app.route('/api/preference-list/reorder', methods=['POST'])
@login_required
def api_reorder_preferences():
    user_id = session['user_id']
    payload = request.get_json() or {}
    items = payload.get('items', [])

    conn = get_db_connection()
    cursor = conn.cursor()
    for itm in items:
        cursor.execute("""
        UPDATE preference_lists 
        SET preference_order = ? 
        WHERE id = ? AND user_id = ?
        """, (int(itm['order']), int(itm['id']), user_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/preference-list/delete/<int:pref_id>', methods=['POST'])
@login_required
def api_delete_preference(pref_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM preference_lists WHERE id = ? AND user_id = ?", (pref_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/preference-list/clear', methods=['POST'])
@login_required
def clear_preferences():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM preference_lists WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('Preference list has been cleared.', 'info')
    return redirect(url_for('preferences_page'))

# ---------------------------------------------------------------------------
# College Search, Details & Comparison (Features 10, 11, 12, 19)
# ---------------------------------------------------------------------------
@app.route('/colleges')
@login_required
def colleges_page():
    q = request.args.get('q', '').strip()
    district = request.args.get('district', '').strip()
    region = request.args.get('region', '').strip()
    col_type = request.args.get('type', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM colleges WHERE is_active = 1"
    params = []

    if q:
        query += " AND (college_name LIKE ? OR college_code LIKE ? OR place LIKE ?)"
        pattern = f"%{q}%"
        params.extend([pattern, pattern, pattern])
    if district:
        query += " AND district = ?"
        params.append(district)
    if region:
        query += " AND region = ?"
        params.append(region)
    if col_type:
        query += " AND type LIKE ?"
        params.append(f"%{col_type}%")

    query += " ORDER BY college_name ASC"
    cursor.execute(query, params)
    colleges = cursor.fetchall()

    cursor.execute("SELECT DISTINCT district FROM colleges WHERE district IS NOT NULL AND district != '' ORDER BY district")
    districts = [r[0] for r in cursor.fetchall()]

    conn.close()

    filters = {'q': q, 'district': district, 'region': region, 'type': col_type}
    return render_template('student/colleges.html', colleges=colleges, districts=districts, filters=filters)

@app.route('/college/<college_code>')
@login_required
def college_detail(college_code):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM colleges WHERE college_code = ?", (college_code,))
    college = cursor.fetchone()
    if not college:
        conn.close()
        flash('College not found.', 'danger')
        return redirect(url_for('colleges_page'))

    # Fetch branch intake and fees
    cursor.execute("SELECT * FROM college_branches WHERE college_code = ? ORDER BY branch_code", (college_code,))
    branches = cursor.fetchall()

    # Fetch cutoffs for chart (across all years)
    cursor.execute("""
    SELECT year, is_forecasted, avg(closing_rank) as avg_closing
    FROM cutoffs 
    WHERE college_code = ? AND closing_rank IS NOT NULL AND closing_rank > 0
    GROUP BY year, is_forecasted
    ORDER BY year ASC
    """, (college_code,))
    cutoff_rows = cursor.fetchall()

    chart_data = {
        'historical': {},
        'forecasted': {}
    }
    for row in cutoff_rows:
        yr = str(row['year'])
        val = int(row['avg_closing'])
        if row['is_forecasted']:
            chart_data['forecasted'][yr] = val
        else:
            chart_data['historical'][yr] = val

    conn.close()
    return render_template(
        'student/college_detail.html',
        college=college,
        branches=branches,
        chart_json=json.dumps(chart_data)
    )

@app.route('/compare')
@login_required
def compare_page():
    codes = request.args.getlist('colleges')
    add_code = request.args.get('add')
    remove_code = request.args.get('remove')

    if add_code and add_code not in codes and len(codes) < 4:
        codes.append(add_code)
    if remove_code and remove_code in codes:
        codes.remove(remove_code)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT college_code, college_name FROM colleges WHERE is_active = 1 ORDER BY college_name")
    all_colleges = cursor.fetchall()

    comparison_data = []
    for code in codes:
        cursor.execute("SELECT * FROM colleges WHERE college_code = ?", (code,))
        col = cursor.fetchone()
        if col:
            cursor.execute("SELECT avg(fees) FROM college_branches WHERE college_code = ?", (code,))
            avg_fees = int(cursor.fetchone()[0] or 45000)

            cursor.execute("SELECT avg(closing_rank) FROM cutoffs WHERE college_code = ? AND closing_rank > 0", (code,))
            avg_cutoff = int(cursor.fetchone()[0] or 1500)

            comparison_data.append({
                'college_code': col['college_code'],
                'college_name': col['college_name'],
                'place': col['place'],
                'district': col['district'],
                'region': col['region'],
                'type': col['type'],
                'college_type': col['college_type'],
                'affiliated_to': col['affiliated_to'],
                'year_of_establishment': col['year_of_establishment'],
                'hostel_availability': col['hostel_availability'],
                'website': col['website'],
                'avg_fees': avg_fees,
                'avg_cutoff': avg_cutoff
            })

    conn.close()

    # Rebuild query for remove links
    query_parts = [f"colleges={c}" for c in codes]
    current_query = "&".join(query_parts)

    return render_template(
        'student/compare.html',
        all_colleges=all_colleges,
        selected_codes=codes,
        comparison_data=comparison_data,
        current_query=current_query
    )

# ---------------------------------------------------------------------------
# Cutoff Analytics (Feature 13)
# ---------------------------------------------------------------------------
@app.route('/analytics')
@login_required
def analytics_page():
    branch = request.args.get('branch', 'COMPUTER SCIENCE AND ENGINEERING')
    category = request.args.get('category', 'OC')
    gender = request.args.get('gender', 'BOYS')
    c_round = request.args.get('round', 'Phase 1')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT branch_code, branch_name FROM branches ORDER BY branch_name")
    branches = cursor.fetchall()

    # 1. Yearly Median Cutoff Trend
    cursor.execute("""
    SELECT year, avg(closing_rank) as avg_closing
    FROM cutoffs
    WHERE (branch_name LIKE ? OR branch_name = ?)
      AND category = ? AND gender = ? AND round = ?
      AND closing_rank IS NOT NULL AND closing_rank > 0
    GROUP BY year ORDER BY year ASC
    """, (f"%{branch}%", branch, category, gender, c_round))
    yearly_rows = cursor.fetchall()
    yearly_trend = {r['year']: int(r['avg_closing']) for r in yearly_rows}

    # 2. Opening vs Closing Rank Spread for Top 5 Colleges
    cursor.execute("""
    SELECT college_code, avg(opening_rank) as avg_open, avg(closing_rank) as avg_close
    FROM cutoffs
    WHERE (branch_name LIKE ? OR branch_name = ?)
      AND category = ? AND gender = ? AND round = ?
      AND closing_rank > 0
    GROUP BY college_code
    ORDER BY avg_close ASC
    LIMIT 6
    """, (f"%{branch}%", branch, category, gender, c_round))
    spread_rows = cursor.fetchall()
    spread_colleges = [r['college_code'] for r in spread_rows]
    opening_ranks = [int(r['avg_open'] or r['avg_close'] * 0.7) for r in spread_rows]
    closing_ranks = [int(r['avg_close']) for r in spread_rows]

    # 3. Category Quota Comparison (Optimized Single Query)
    cat_list = ['OC', 'OC-EWS', 'BC-A', 'BC-B', 'BC-C', 'BC-D', 'BC-E', 'SC - I', 'ST']
    cursor.execute("""
    SELECT category, avg(closing_rank) as avg_close
    FROM cutoffs
    WHERE (branch_name LIKE ? OR branch_name = ?)
      AND gender = ? AND round = ? AND closing_rank > 0
    GROUP BY category
    """, (f"%{branch}%", branch, gender, c_round))
    cat_map = {r['category']: int(r['avg_close']) for r in cursor.fetchall()}
    cat_ranks = [cat_map.get(c, 1800) for c in cat_list]

    conn.close()

    analytics_json = {
        'yearly_trend': yearly_trend,
        'spread_colleges': spread_colleges,
        'opening_ranks': opening_ranks,
        'closing_ranks': closing_ranks,
        'cat_labels': cat_list,
        'cat_ranks': cat_ranks
    }

    return render_template(
        'student/analytics.html',
        branches=branches,
        current_branch=branch,
        current_cat=category,
        current_gender=gender,
        current_round=c_round,
        analytics_json=json.dumps(analytics_json)
    )

# ---------------------------------------------------------------------------
# Saved Colleges & History & Calendar (Features 15, 16, 18)
# ---------------------------------------------------------------------------
@app.route('/saved')
@login_required
def saved_colleges_page():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT s.id, s.college_code, s.branch_name, s.created_at,
           c.college_name, c.place, c.district, c.region, c.type
    FROM saved_colleges s
    JOIN colleges c ON s.college_code = c.college_code
    WHERE s.user_id = ?
    ORDER BY s.created_at DESC
    """, (user_id,))
    saved_colleges = cursor.fetchall()
    conn.close()
    return render_template('student/saved.html', saved_colleges=saved_colleges)

@app.route('/api/save-college', methods=['POST'])
@login_required
def api_save_college():
    user_id = session['user_id']
    data = request.get_json() or {}
    college_code = data.get('college_code')
    branch_name = data.get('branch_name', 'ALL')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM saved_colleges WHERE user_id = ? AND college_code = ?", (user_id, college_code))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("DELETE FROM saved_colleges WHERE id = ?", (existing['id'],))
        action = 'removed'
    else:
        cursor.execute("""
        INSERT OR IGNORE INTO saved_colleges (user_id, college_code, branch_name)
        VALUES (?, ?, ?)
        """, (user_id, college_code, branch_name))
        action = 'saved'

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'action': action})

@app.route('/saved/remove/<int:save_id>', methods=['POST'])
@login_required
def remove_saved_college(save_id):
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM saved_colleges WHERE id = ? AND user_id = ?", (save_id, user_id))
    conn.commit()
    conn.close()
    flash('College removed from bookmarks.', 'info')
    return redirect(url_for('saved_colleges_page'))

@app.route('/history')
@login_required
def history_page():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    history = cursor.fetchall()
    conn.close()
    return render_template('student/history.html', history=history)

@app.route('/calendar')
@login_required
def calendar_page():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM counselling_calendar ORDER BY stage_order ASC")
    calendar_items = cursor.fetchall()
    conn.close()
    return render_template('student/calendar.html', calendar_items=calendar_items)

# ---------------------------------------------------------------------------
# Admin Back-Office Routes (Features 20 to 27)
# ---------------------------------------------------------------------------
@app.route('/admin')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM colleges")
    colleges_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM branches")
    branches_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM cutoffs")
    cutoffs_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM users WHERE role = 'student'")
    users_count = cursor.fetchone()[0]

    cursor.execute("SELECT count(*) FROM predictions")
    predictions_count = cursor.fetchone()[0]

    conn.close()

    stats = {
        'colleges_count': colleges_count,
        'branches_count': branches_count,
        'cutoffs_count': cutoffs_count,
        'users_count': users_count,
        'predictions_count': predictions_count
    }
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/colleges')
@admin_required
def admin_colleges():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM colleges ORDER BY college_name ASC")
    colleges = cursor.fetchall()
    conn.close()
    return render_template('admin/colleges.html', colleges=colleges)

@app.route('/admin/colleges/add', methods=['POST'])
@admin_required
def admin_add_college():
    code = request.form.get('college_code', '').strip().upper()
    name = request.form.get('college_name', '').strip()
    district = request.form.get('district', '').strip().upper()
    region = request.form.get('region', 'AU').strip().upper()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO colleges (college_code, college_name, district, region, is_active)
    VALUES (?, ?, ?, ?, 1)
    """, (code, name, district, region))
    conn.commit()
    conn.close()
    flash(f'College {code} added successfully.', 'success')
    return redirect(url_for('admin_colleges'))

@app.route('/admin/colleges/toggle/<college_code>', methods=['POST'])
@admin_required
def admin_toggle_college(college_code):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE colleges SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE college_code = ?", (college_code,))
    conn.commit()
    conn.close()
    flash(f'College status toggled.', 'info')
    return redirect(url_for('admin_colleges'))

@app.route('/admin/branches')
@admin_required
def admin_branches():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM branches ORDER BY branch_name ASC")
    branches = cursor.fetchall()
    conn.close()
    return render_template('admin/branches.html', branches=branches)

@app.route('/admin/branches/add', methods=['POST'])
@admin_required
def admin_add_branch():
    code = request.form.get('branch_code', '').strip().upper()
    name = request.form.get('branch_name', '').strip()
    department = request.form.get('department', 'Engineering').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO branches (branch_code, branch_name, department) VALUES (?, ?, ?)", (code, name, department))
    conn.commit()
    conn.close()
    flash(f'Branch {code} added successfully.', 'success')
    return redirect(url_for('admin_branches'))

@app.route('/admin/cutoffs')
@admin_required
def admin_cutoffs():
    year = int(request.args.get('year', 2024))
    round_name = request.args.get('round', 'Phase 1')
    cat = request.args.get('category', 'OC')
    gender = request.args.get('gender', 'BOYS')
    q = request.args.get('q', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT * FROM cutoffs 
    WHERE year = ? AND round = ? AND category = ? AND gender = ?
    """
    params = [year, round_name, cat, gender]

    if q:
        query += " AND (college_code LIKE ? OR college_name LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])

    query += " ORDER BY closing_rank ASC LIMIT 100"
    cursor.execute(query, params)
    cutoffs = cursor.fetchall()
    conn.close()

    return render_template(
        'admin/cutoffs.html',
        cutoffs=cutoffs,
        selected_year=year,
        selected_round=round_name,
        selected_cat=cat,
        selected_gender=gender,
        query_q=q
    )

@app.route('/admin/seat-matrix')
@admin_required
def admin_seat_matrix():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM college_branches ORDER BY college_code ASC LIMIT 100")
    matrix = cursor.fetchall()
    conn.close()
    return render_template('admin/seat_matrix.html', matrix=matrix)

@app.route('/admin/upload-csv', methods=['GET', 'POST'])
@admin_required
def admin_upload_csv():
    upload_result = None

    if request.method == 'POST':
        year = int(request.form.get('year', 2026))
        round_name = request.form.get('round', 'Phase 1')
        file = request.files.get('csv_file')

        if not file or not file.filename.endswith('.csv'):
            flash('Please upload a valid .csv file.', 'danger')
            return render_template('admin/upload_csv.html')

        # Feature 25: CSV Validation & Cleaning Pipeline
        # Workflow: Upload -> File Validation -> Column Validation -> Missing Data Check -> Duplicate Check -> Invalid Data Check -> Database
        content = file.read().decode('utf-8', errors='ignore')
        reader = csv.reader(io.StringIO(content))
        
        headers = next(reader, None)
        if not headers:
            flash('Empty CSV file provided.', 'danger')
            return render_template('admin/upload_csv.html')

        clean_headers = [h.strip().upper() for h in headers]
        
        # Check required columns
        req_cols = ['COLLEGE CODE', 'BRANCH', 'GENDER', 'CATEGORY', 'CLOSING RANK']
        missing_cols = [col for col in req_cols if not any(col in h for h in clean_headers)]
        
        if missing_cols:
            flash(f'CSV Missing required columns: {", ".join(missing_cols)}', 'danger')
            return render_template('admin/upload_csv.html')

        col_indices = {}
        for req in ['COLLEGE CODE', 'BRANCH', 'GENDER', 'CATEGORY', 'OPENING RANK', 'CLOSING RANK', 'COLLEGE NAME', 'PLACE']:
            for idx, h in enumerate(clean_headers):
                if req in h and req not in col_indices:
                    col_indices[req] = idx

        total_rows = 0
        valid_rows = 0
        duplicates = 0
        invalid_rows = []
        batch = []

        conn = get_db_connection()
        cursor = conn.cursor()

        # Query existing keys for duplicate check
        cursor.execute("SELECT college_code, branch_name, category, gender FROM cutoffs WHERE year = ? AND round = ?", (year, round_name))
        existing_keys = set((r[0], r[1], r[2], r[3]) for r in cursor.fetchall())

        is_forecasted = 1 if year >= 2025 else 0

        for r_idx, row in enumerate(reader, start=2):
            if not row or len(row) < 3:
                continue
            total_rows += 1

            code = row[col_indices['COLLEGE CODE']].strip().upper() if 'COLLEGE CODE' in col_indices and col_indices['COLLEGE CODE'] < len(row) else ''
            branch_str = row[col_indices['BRANCH']].strip() if 'BRANCH' in col_indices and col_indices['BRANCH'] < len(row) else ''
            gender_str = row[col_indices['GENDER']].strip().upper() if 'GENDER' in col_indices and col_indices['GENDER'] < len(row) else 'BOYS'
            cat_str = row[col_indices['CATEGORY']].strip().upper() if 'CATEGORY' in col_indices and col_indices['CATEGORY'] < len(row) else 'OC'
            c_name = row[col_indices['COLLEGE NAME']].strip() if 'COLLEGE NAME' in col_indices and col_indices['COLLEGE NAME'] < len(row) else code
            place_str = row[col_indices['PLACE']].strip() if 'PLACE' in col_indices and col_indices['PLACE'] < len(row) else ''

            open_val = row[col_indices['OPENING RANK']].strip() if 'OPENING RANK' in col_indices and col_indices['OPENING RANK'] < len(row) else ''
            close_val = row[col_indices['CLOSING RANK']].strip() if 'CLOSING RANK' in col_indices and col_indices['CLOSING RANK'] < len(row) else ''

            # Validation checks
            if not code:
                invalid_rows.append({'row_idx': r_idx, 'college_code': 'N/A', 'branch': branch_str, 'category': cat_str, 'closing_rank': close_val, 'reason': 'Missing College Code'})
                continue
            if not branch_str:
                invalid_rows.append({'row_idx': r_idx, 'college_code': code, 'branch': 'N/A', 'category': cat_str, 'closing_rank': close_val, 'reason': 'Missing Branch Name'})
                continue

            try:
                c_rank = int(close_val.replace(',', ''))
                o_rank = int(open_val.replace(',', '')) if open_val else c_rank
            except ValueError:
                invalid_rows.append({'row_idx': r_idx, 'college_code': code, 'branch': branch_str, 'category': cat_str, 'closing_rank': close_val, 'reason': 'Non-numeric rank value'})
                continue

            # Duplicate check
            key = (code, branch_str, cat_str, gender_str)
            if key in existing_keys:
                duplicates += 1
                continue

            existing_keys.add(key)
            batch.append((year, round_name, code, c_name, place_str, branch_str, None, gender_str, cat_str, o_rank, c_rank, is_forecasted))
            valid_rows += 1

        if batch:
            cursor.executemany("""
            INSERT INTO cutoffs 
            (year, round, college_code, college_name, place, branch_name, branch_code, gender, category, opening_rank, closing_rank, is_forecasted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, batch)
            conn.commit()

        conn.close()

        upload_result = {
            'status': 'success' if valid_rows > 0 else 'warning',
            'total_rows': total_rows,
            'valid_rows': valid_rows,
            'duplicates': duplicates,
            'invalid_rows': invalid_rows
        }
        flash(f'CSV Processed: {valid_rows} records added, {duplicates} duplicates ignored, {len(invalid_rows)} rejected.', 'success' if valid_rows > 0 else 'warning')

    return render_template('admin/upload_csv.html', upload_result=upload_result)

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT u.*, p.rank, p.category, p.gender, p.preferred_branch 
    FROM users u
    LEFT JOIN student_profiles p ON u.id = p.user_id
    ORDER BY u.created_at DESC
    """)
    users = cursor.fetchall()
    conn.close()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/toggle/<int:user_id>', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_active = CASE WHEN is_active = 1 THEN 0 ELSE 1 END WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    flash('User account status toggled.', 'info')
    return redirect(url_for('admin_users'))

@app.route('/admin/reports')
@admin_required
def admin_reports():
    # Feature 27: Admin Reports & Model Evaluation (Viva Presentation)
    eval_data = forecasting_engine.get_evaluation_metrics()
    return render_template(
        'admin/reports.html',
        eval_data=eval_data,
        eval_json=json.dumps(eval_data)
    )

# ---------------------------------------------------------------------------
# Export & Reports Endpoints (Feature 28)
# ---------------------------------------------------------------------------
@app.route('/export/prediction-pdf/<int:pred_id>')
@login_required
def export_prediction_pdf(pred_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions WHERE id = ?", (pred_id,))
    pred = cursor.fetchone()
    conn.close()

    if not pred:
        flash('Prediction record not found.', 'danger')
        return redirect(url_for('history_page'))

    student_data = {
        'student_rank': pred['student_rank'],
        'branch': pred['branch'],
        'category': pred['category'],
        'gender': pred['gender'],
        'region': pred['region'],
        'counselling_round': pred['counselling_round'],
        'district': pred['district'],
        'college_type': pred['college_type']
    }
    recommendations = json.loads(pred['results_json'] or '[]')

    pdf_bytes = generate_prediction_report_pdf(student_data, recommendations)
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"AP_ECET_Forecast_Report_{student_data['student_rank']}_{student_data['category']}.pdf"
    )

@app.route('/export/preference-pdf')
@login_required
def export_preference_pdf():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    cursor.execute("SELECT * FROM preference_lists WHERE user_id = ? ORDER BY preference_order ASC", (user_id,))
    prefs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    user_info = {'username': user['username'], 'email': user['email']}
    pdf_bytes = generate_preference_list_pdf(user_info, prefs)

    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"AP_ECET_Web_Options_Preferences_{user['username']}.pdf"
    )

@app.route('/export/preference-csv')
@login_required
def export_preference_csv():
    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM preference_lists WHERE user_id = ? ORDER BY preference_order ASC", (user_id,))
    prefs = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Preference Order', 'College Code', 'College Name', 'Branch Name', 'District', 'Classification', 'Admission Probability (%)', 'Expected Cutoff', 'Annual Fee (INR)'])
    for p in prefs:
        writer.writerow([
            p['preference_order'], p['college_code'], p['college_name'], p['branch_name'],
            p['district'], p['classification'], p['probability'], p['closing_rank'], p['fees']
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f"attachment; filename=AP_ECET_Web_Options_{session.get('username')}.csv"
    response.headers['Content-type'] = 'text/csv'
    return response

if __name__ == '__main__':
    # Initialize database if not already done
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
