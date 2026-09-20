from database import get_db_connection

conn = get_db_connection()
c = conn.cursor()

print("=== Distinct rounds ===")
c.execute("SELECT DISTINCT round FROM cutoffs ORDER BY round LIMIT 20")
for r in c.fetchall():
    print(f"  '{r[0]}'")

print("\n=== Distinct categories ===")
c.execute("SELECT DISTINCT category FROM cutoffs ORDER BY category LIMIT 20")
for r in c.fetchall():
    print(f"  '{r[0]}'")

print("\n=== Distinct genders ===")
c.execute("SELECT DISTINCT gender FROM cutoffs ORDER BY gender")
for r in c.fetchall():
    print(f"  '{r[0]}'")

print("\n=== Distinct regions in colleges ===")
c.execute("SELECT DISTINCT region FROM colleges ORDER BY region")
for r in c.fetchall():
    print(f"  '{r[0]}'")

print("\n=== Branch sample matching ECE ===")
c.execute("SELECT DISTINCT branch_name FROM cutoffs WHERE branch_name LIKE '%ELECTRONICS%' LIMIT 10")
for r in c.fetchall():
    print(f"  '{r[0]}'")

print("\n=== Branch sample matching MECH ===")
c.execute("SELECT DISTINCT branch_name FROM cutoffs WHERE branch_name LIKE '%MECHAN%' LIMIT 10")
for r in c.fetchall():
    print(f"  '{r[0]}'")

print("\n=== SVU region count ===")
c.execute("SELECT COUNT(*) FROM cutoffs c JOIN colleges col ON c.college_code = col.college_code WHERE col.region = 'SVU'")
print(f"  SVU cutoffs: {c.fetchone()[0]}")

print("\n=== Cutoff count by ECE branch + BC-B ===")
c.execute("SELECT COUNT(*) FROM cutoffs WHERE branch_name LIKE '%ELECTRONICS%' AND category = 'BC-B'")
print(f"  ECE+BC-B: {c.fetchone()[0]}")

print("\n=== Cutoff count by ECE branch + BC-B + round ===")
c.execute("SELECT COUNT(*), round FROM cutoffs WHERE branch_name LIKE '%ELECTRONICS%' AND category = 'BC-B' GROUP BY round")
for r in c.fetchall():
    print(f"  Count: {r[0]} | Round: '{r[1]}'")

conn.close()
