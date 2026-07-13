import sqlite3

# Connect to your newly minted Silver layer
conn = sqlite3.connect("unified_layer.db")
cursor = conn.cursor()

print("--- UNIFIED EVENTS (Structured Timeline Data) ---")
cursor.execute("SELECT dataset_id, event_timestamp, title FROM unified_events LIMIT 5;")
rows = cursor.fetchall()
for row in rows:
    print(f"[{row[0]}] {row[1]} | {row[2]}")

print("\n--- UNIFIED KNOWLEDGE (Unstructured Text Data) ---")
cursor.execute(
    "SELECT dataset_id, title, substr(content, 1, 60) || '...' as content_preview FROM unified_knowledge LIMIT 5;"
)
rows = cursor.fetchall()
for row in rows:
    print(f"[{row[0]}] {row[1]} | {row[2]}")

conn.close()
