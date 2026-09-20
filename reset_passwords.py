from database import get_db_connection
from werkzeug.security import generate_password_hash, check_password_hash

conn = get_db_connection()
c = conn.cursor()

# Check current stored hash
c.execute("SELECT id, email, password_hash, role FROM users")
users = c.fetchall()
for u in users:
    print(f"Email: {u['email']} | Role: {u['role']}")
    # Test various passwords
    for pwd in ['Student@12345', 'Admin@12345', 'Student@123', 'Admin@123', 'student123', 'admin123']:
        if check_password_hash(u['password_hash'], pwd):
            print(f"  -> Password matches: {pwd}")
            break
    else:
        print(f"  -> No match found, resetting to known passwords")

# Reset to known passwords
c.execute("UPDATE users SET password_hash = ? WHERE email = ?",
          (generate_password_hash('Student@12345'), 'student@apecet.gov.in'))
c.execute("UPDATE users SET password_hash = ? WHERE email = ?",
          (generate_password_hash('Admin@12345'), 'admin@apecet.gov.in'))
conn.commit()
print("\nPasswords reset successfully.")
print("Student: student@apecet.gov.in / Student@12345")
print("Admin:   admin@apecet.gov.in   / Admin@12345")
conn.close()
