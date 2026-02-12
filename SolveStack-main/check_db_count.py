
import sqlite3

try:
    conn = sqlite3.connect('solvestack.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM problems")
    count = cursor.fetchone()[0]
    print(f"Total problems in DB: {count}")
    
    if count > 0:
        cursor.execute("SELECT ps_id, title, source FROM problems LIMIT 3")
        rows = cursor.fetchall()
        print("\nSample Data:")
        for row in rows:
            print(row)
    conn.close()
except Exception as e:
    print(f"Error checking DB: {e}")
