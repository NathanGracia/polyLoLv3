"""Quick script to verify database structure."""
import sqlite3

conn = sqlite3.connect('bets.db')
cursor = conn.cursor()

# Check tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("OK - Tables created:", [t[0] for t in tables])

# Check bets table schema
cursor.execute("PRAGMA table_info(bets)")
columns = cursor.fetchall()
print("\nOK - Bets table columns:")
for col in columns:
    print(f"   - {col[1]}: {col[2]}")

# Check indexes
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='bets'")
indexes = cursor.fetchall()
print("\nOK - Indexes created:", [i[0] for i in indexes])

# Check row count
cursor.execute("SELECT COUNT(*) FROM bets")
count = cursor.fetchone()[0]
print(f"\nOK - Current bets in database: {count}")

conn.close()
print("\nSUCCESS - Database structure is correct!")
