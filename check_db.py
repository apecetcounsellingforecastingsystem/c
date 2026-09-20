from database import get_db_connection
conn = get_db_connection()
c = conn.cursor()
c.execute("SELECT COUNT(*) FROM users")
print('Users:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM colleges")
print('Colleges:', c.fetchone()[0])
c.execute("SELECT COUNT(*) FROM cutoffs")
print('Cutoffs:', c.fetchone()[0])
c.execute("SELECT email, role FROM users LIMIT 5")
for row in c.fetchall():
    print(f"  User: {row['email']} | Role: {row['role']}")
conn.close()
print("DB check complete.")
