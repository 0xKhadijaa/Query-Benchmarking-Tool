# benchmark_tool/connectors/postgres_connector.py
import psycopg2
from psycopg2 import OperationalError, Error

def run_query(query):
    conn = None
    cursor = None
    try:
        conn = psycopg2.connect(user='postgres', password='pass', host='127.0.0.1', dbname='test')
        cursor = conn.cursor()
        print(f"Executing query: {query}")

        cursor.execute(query)

        if query.strip().lower().startswith("select"):
            result = cursor.fetchall() 
        else:
            conn.commit()  
            result = cursor.rowcount 

        return result

    except (OperationalError, Error) as e:
        print(f"PostgreSQL Error: {e}")
        return None

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
