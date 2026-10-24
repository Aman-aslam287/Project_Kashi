from db import get_db_connection

try:
    db = get_db_connection()

    print("Connection successful!")

    cursor = db.cursor()
    cursor.execute("SELECT DATABASE()")

    print("Database:", cursor.fetchone()[0])

    cursor.close()
    db.close()

except Exception as e:
    print("Connection failed:", e)