"""
ETL Ingestion Script for AP ECET Counselling Forecasting System.
Parses master college details and 2023-2026 cutoff datasets into SQLite ap_ecet.db.
"""

import os
import re
import pandas as pd
from werkzeug.security import generate_password_hash
from database import get_db_connection, init_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CATEGORY_MAPPING = [
    # (boys_open_col, boys_close_col, girls_open_col, girls_close_col, category_code)
    (5, 6, 33, 34, 'OC'),
    (7, 8, 35, 36, 'OC-EWS'),
    (9, 10, 37, 38, 'BC-A'),
    (11, 12, 39, 40, 'BC-B'),
    (13, 14, 41, 42, 'BC-C'),
    (15, 16, 43, 44, 'BC-D'),
    (17, 18, 45, 46, 'BC-E'),
    (19, 20, 47, 48, 'SC - I'),
    (21, 22, 49, 50, 'SC - II'),
    (23, 24, 51, 52, 'SC - III'),
    (25, 26, 53, 54, 'ST'),
    (27, 28, 55, 56, 'NCC'),
    (29, 30, 57, 58, 'PH'),
    (31, 32, 59, 60, 'CAP'),
]

def clean_int(val):
    if pd.isna(val):
        return None
    try:
        # Handle cases where value might be string or float
        cleaned = re.sub(r'[^\d]', '', str(val))
        if cleaned:
            return int(cleaned)
    except Exception:
        pass
    return None

def clean_str(val):
    if pd.isna(val):
        return ''
    return str(val).strip()

def seed_users_and_meta(conn):
    cursor = conn.cursor()
    print("Seeding default users, notifications, and calendar...")
    
    # 1. Admin user
    cursor.execute("""
    INSERT OR IGNORE INTO users (username, email, phone, password_hash, role, is_active)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ('admin', 'admin@apecet.gov.in', '9876543210', generate_password_hash('Admin@12345'), 'admin', 1))

    # 2. Demo student user
    cursor.execute("""
    INSERT OR IGNORE INTO users (username, email, phone, password_hash, role, is_active)
    VALUES (?, ?, ?, ?, ?, ?)
    """, ('student', 'student@apecet.gov.in', '9123456780', generate_password_hash('Student@12345'), 'student', 1))

    # Fetch student ID
    cursor.execute("SELECT id FROM users WHERE username = 'student'")
    student_row = cursor.fetchone()
    if student_row:
        student_id = student_row['id']
        cursor.execute("""
        INSERT OR REPLACE INTO student_profiles 
        (user_id, rank, category, gender, region, district, preferred_branch, counselling_round, college_type, max_budget)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (student_id, 850, 'BC-B', 'BOYS', 'AU', 'PKS', 'COMPUTER SCIENCE AND ENGINEERING', 'Phase 1', 'ALL', 60000))

    # 3. Counselling Notifications
    notifications = [
        ("AP ECET 2026 Web Options Schedule Released", "The Department of Technical Education has officially notified that Web Options entry for Phase 1 starts from October 1st. Verify your certificate status.", "important", "2026-09-15"),
        ("Reporting at Allotted Colleges Guideline", "Candidates securing seats must report with original documents and allotment order within 4 working days of result announcement.", "normal", "2026-09-10"),
        ("Fee Reimbursement (JVD Scheme) Eligibility", "Full fee reimbursement is applicable for eligible students having White Ration Card / Income Certificate below 2.5 LPA.", "normal", "2026-09-05")
    ]
    for n in notifications:
        cursor.execute("""
        INSERT OR IGNORE INTO notifications (title, description, alert_type, publish_date)
        VALUES (?, ?, ?, ?)
        """, n)

    # 4. Counselling Calendar
    calendar_stages = [
        (1, "Candidate Registration & Fee Payment", "2026-09-20", "2026-09-25", "completed", "Online portal registration and non-refundable processing fee payment."),
        (2, "Certificate Verification (HLCs)", "2026-09-26", "2026-09-30", "completed", "Online and designated Help Line Centre verification of original diploma certificates & caste status."),
        (3, "Web Options Entry — Phase 1", "2026-10-01", "2026-10-06", "ongoing", "Freezing preferred choices of colleges and branches in order of priority."),
        (4, "Phase 1 Seat Allotment Results", "2026-10-09", "2026-10-09", "upcoming", "Provisional seat allotment based on ECET merit, category, region, and web options."),
        (5, "Self-Reporting & College Joining", "2026-10-10", "2026-10-14", "upcoming", "Reporting online and at the allotted institute with fee challan and verification slip."),
        (6, "Final Phase Web Options & Allotment", "2026-10-18", "2026-10-24", "upcoming", "Second and final counselling phase for vacant seats.")
    ]
    cursor.execute("DELETE FROM counselling_calendar")
    for stage in calendar_stages:
        cursor.execute("""
        INSERT INTO counselling_calendar (stage_order, stage_name, start_date, end_date, status, description)
        VALUES (?, ?, ?, ?, ?, ?)
        """, stage)

    conn.commit()

def ingest_colleges_and_branches(conn):
    cursor = conn.cursor()
    excel_path = os.path.join(BASE_DIR, 'AP ECET ALL COLLEGES DETAILS (2).xlsx')
    if not os.path.exists(excel_path):
        print(f"Error: {excel_path} not found!")
        return

    print("Ingesting Colleges Information Details...")
    df_info = pd.read_excel(excel_path, sheet_name='COLLEGE_INFORMATION_DETAILS')
    
    colleges_data = []
    for _, row in df_info.iterrows():
        code = clean_str(row.get('COLLEGE CODE'))
        name = clean_str(row.get('COLLEGE NAME'))
        if not code or not name:
            continue
        
        district = clean_str(row.get('DISTRICT'))
        place = clean_str(row.get('PLACE'))
        region = clean_str(row.get('REGION'))
        affil = clean_str(row.get('AFFILIATED TO'))
        ctype = clean_str(row.get('Type'))
        year_est = clean_int(row.get('YEAR OF ESTABLISHMENT'))
        website = clean_str(row.get('WEBSITE'))
        college_type = clean_str(row.get('COLLEGE TYPE'))
        minority = clean_str(row.get('MINORITY STATUS'))
        hostel = clean_str(row.get('HOSTEL AVAILABILITY'))
        phone = clean_str(row.get('PHONE'))
        email = clean_str(row.get('EMAIL'))
        address = clean_str(row.get('ADDRESS'))

        colleges_data.append((
            code, name, district, place, region, affil, ctype,
            year_est, website, college_type, minority, hostel,
            phone, email, address, 1
        ))

    cursor.executemany("""
    INSERT OR REPLACE INTO colleges (
        college_code, college_name, district, place, region, affiliated_to,
        type, year_of_establishment, website, college_type, minority_status,
        hostel_availability, phone, email, address, is_active
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, colleges_data)
    print(f"Inserted {len(colleges_data)} colleges.")

    print("Ingesting College Branch Details & Master Branches...")
    df_branch = pd.read_excel(excel_path, sheet_name='COLLEGE_BRANCH_DETAILS')
    
    branch_master = {}
    college_branches = []

    for _, row in df_branch.iterrows():
        college_code = clean_str(row.get('COLLEGE CODE'))
        branch_code = clean_str(row.get('BRANCH CODE'))
        branch_name = clean_str(row.get('BRANCH NAME '))
        if not branch_code or not branch_name:
            continue
        
        branch_master[branch_code] = branch_name
        
        if college_code:
            intake = clean_int(row.get('TOTAL INTAKEN SEATS ')) or 0
            fees = clean_int(row.get('FEES')) or 0
            college_branches.append((college_code, branch_code, branch_name, intake, fees))

    # Insert branches master
    branch_rows = [(bcode, bname, 'Engineering') for bcode, bname in branch_master.items()]
    cursor.executemany("""
    INSERT OR REPLACE INTO branches (branch_code, branch_name, department)
    VALUES (?, ?, ?)
    """, branch_rows)
    print(f"Inserted {len(branch_rows)} master branches.")

    # Insert college branches
    cursor.executemany("""
    INSERT INTO college_branches (college_code, branch_code, branch_name, total_intake_seats, fees)
    VALUES (?, ?, ?, ?, ?)
    """, college_branches)
    print(f"Inserted {len(college_branches)} college branch fee/intake records.")
    conn.commit()

def ingest_cutoffs(conn):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cutoffs")
    
    # Mapping of files to years and forecasting status
    cutoff_files = [
        (2023, 'ECET CUTOFF RANK 2023 FOR ALL PHASES(EXPECTED).xlsx', 0),
        (2024, 'ECET CUTOFF RANK 2024 FOR ALL PHASES (EXPECTED).xlsx', 0),
        (2025, 'ECET CUTOFF RANK 2025 FOR ALL PHASES(EXPECTED).xlsx', 1),
        (2026, 'ECET CUTOFF RANK 2026 FOR ALL PHASES(EXPECTED).xlsx', 1),
    ]

    total_cutoffs = 0

    for year, filename, is_forecasted in cutoff_files:
        filepath = os.path.join(BASE_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: {filename} not found!")
            continue

        print(f"\nProcessing Cutoff File: {filename} (Year={year}, Forecasted={is_forecasted})...")
        xl = pd.ExcelFile(filepath)
        
        for sheet_name in xl.sheet_names:
            round_name = 'Phase 1' if 'Phase 1' in sheet_name or 'Phase1' in sheet_name else 'Final Phase'
            print(f"  Reading sheet '{sheet_name}' as round '{round_name}'...")
            
            # Read all rows without header
            df = pd.read_excel(filepath, sheet_name=sheet_name, header=None)
            
            batch_data = []
            
            # Data starts at row 4
            for r_idx in range(4, len(df)):
                row = df.iloc[r_idx]
                
                college_code = clean_str(row[1])
                college_name = clean_str(row[2])
                place = clean_str(row[3])
                branch_name = clean_str(row[4])
                
                # Check for empty or invalid separator rows
                if not college_code or not branch_name or college_code == 'COLLEGE CODE':
                    continue

                for boys_open, boys_close, girls_open, girls_close, cat_code in CATEGORY_MAPPING:
                    # Boys
                    b_open = clean_int(row[boys_open])
                    b_close = clean_int(row[boys_close])
                    if b_open is not None or b_close is not None:
                        batch_data.append((
                            year, round_name, college_code, college_name, place,
                            branch_name, None, 'BOYS', cat_code, b_open, b_close, is_forecasted
                        ))

                    # Girls
                    g_open = clean_int(row[girls_open])
                    g_close = clean_int(row[girls_close])
                    if g_open is not None or g_close is not None:
                        batch_data.append((
                            year, round_name, college_code, college_name, place,
                            branch_name, None, 'GIRLS', cat_code, g_open, g_close, is_forecasted
                        ))

            if batch_data:
                cursor.executemany("""
                INSERT INTO cutoffs (
                    year, round, college_code, college_name, place,
                    branch_name, branch_code, gender, category,
                    opening_rank, closing_rank, is_forecasted
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, batch_data)
                total_cutoffs += len(batch_data)
                print(f"    Inserted {len(batch_data)} records for {year} {round_name}.")

        conn.commit()

    print(f"\nSuccessfully ingested {total_cutoffs} total cutoff records into database.")

def run_etl():
    init_db()
    conn = get_db_connection()
    try:
        seed_users_and_meta(conn)
        ingest_colleges_and_branches(conn)
        ingest_cutoffs(conn)
        print("\n=== ALL ETL INGESTION COMPLETED SUCCESSFULLY ===")
    finally:
        conn.close()

if __name__ == '__main__':
    run_etl()
