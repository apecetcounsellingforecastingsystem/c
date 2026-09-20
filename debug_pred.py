from database import get_db_connection
import numpy as np

conn = get_db_connection()
cursor = conn.cursor()

branch = "ELECTRONICS AND COMMUNICATION ENGINEERING"
category = "BC-B"
gender = "GIRLS"
counselling_round = "Phase 2"
region = "SVU"

branch_pattern = f"%{branch.strip()}%"

cutoff_query = """
SELECT 
    c.college_code, c.college_name, c.place, c.branch_name,
    c.year, c.round, c.closing_rank, c.opening_rank, c.is_forecasted,
    col.district, col.region, col.type as college_type_desc
FROM cutoffs c
LEFT JOIN colleges col ON c.college_code = col.college_code
WHERE (c.branch_name LIKE ? OR c.branch_name = ?)
  AND c.category = ?
  AND c.gender = ?
  AND c.round = ?
  AND c.closing_rank IS NOT NULL AND c.closing_rank > 0
"""
params = [branch_pattern, branch, category, gender, counselling_round]

cursor.execute(cutoff_query, params)
rows = cursor.fetchall()

print(f"Total raw rows with round='Phase 2': {len(rows)}")

# Try 'Phase 1' instead
params2 = [branch_pattern, branch, category, gender, 'Phase 1']
cursor.execute(cutoff_query, params2)
rows2 = cursor.fetchall()
print(f"Total raw rows with round='Phase 1': {len(rows2)}")

# Check regions in rows2
regions = set(r['region'] for r in rows2 if r['region'])
print(f"Distinct regions found: {regions}")

svus = [r for r in rows2 if r['region'] == 'SVU']
print(f"SVU rows: {len(svus)}")
if svus:
    print("Sample:", svus[0]['college_name'], svus[0]['region'])

conn.close()
print("\nConclusion:")
print("Round 'Phase 2' does not exist in DB — only 'Phase 1' and 'Final Phase'")
print("The UI must map 'Round 1' -> 'Phase 1' and 'Round 2'/'Final' -> 'Final Phase'")
