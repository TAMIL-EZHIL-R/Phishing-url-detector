import sqlite3

conn = sqlite3.connect("phishing_results.db")
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS results")

conn.commit()
conn.close()

print("🔥 Table deleted completely")