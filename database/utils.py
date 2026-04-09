import mysql.connector

config = {
    'host': 'localhost',
    'user': 'prrsv_admin',
    'password': 'SecureDBpass456!',
    'database': 'prrsv_genomics'
}

def get_connection():
    return mysql.connector.connect(**config)

def execute_query(query, data=None, fetch=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(query, data or ())
    result = cursor.fetchall() if fetch else None
    conn.commit()
    cursor.close()
    conn.close()
    return result

