import mysql.connector
from mysql.connector import Error

def run_query(query):
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='test')
        cursor = conn.cursor()

        cursor.execute(query)

        if query.strip().lower().startswith("select"):
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount

        return result

    except Error as e:
        raise Exception(f"MySQL Error: {e}")

    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
