import sqlite3

conn = sqlite3.connect('atlas.db')
cursor = conn.cursor()

cursor.execute("SELECT program_name, risk_level, approval_status FROM conversion_audit ORDER BY id DESC LIMIT 5")
rows = cursor.fetchall()

print("\n--- ULTIMOS REGISTROS DE AUDITORIA (atlas.db) ---")
for r in rows:
    print(f"Programa: {r[0]:<10} | Risco: {r[1]:<6} | Status: {r[2]}")
print("--------------------------------------------------")

conn.close()
