import mysql.connector

def get_db_connection():
    db = mysql.connector.connect(
    host="127.0.0.1",
    port=3306,
    user="root",
    password="Aman-117!",
    database="project_kashi"
    )
    return db
    