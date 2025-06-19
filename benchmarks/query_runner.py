import time
import threading
import psutil
import json
import re

from connectors.mysql_connector import run_query as mysql_run_query
from connectors.mongo_connector import run_query as mongo_run_query
from connectors.postgres_connector import run_query as postgres_run_query
from connectors.redis_connector import run_query as redis_run_query

def translate_query(source_db, raw_query):
    if raw_query is None:
        raise ValueError(f"Raw query for {source_db} is None")

    if source_db == 'mongodb':
        try:
            query = json.loads(raw_query)
            if not isinstance(query, dict) or not query:
                raise ValueError("MongoDB query must be a non-empty JSON object.")
            
            key = next(iter(query.keys())) 
            value = query[key]
        except json.JSONDecodeError:
            raise ValueError("Invalid MongoDB query format. Must be valid JSON.")
        
        sql_query = f"SELECT * FROM sample WHERE {key} = '{value}';"
        redis_query = value

        return {
            'mysql': sql_query,
            'postgresql': sql_query,
            'mongodb': query,
            'redis': redis_query
        }
    elif source_db in ['mysql', 'postgresql']:
        match = re.search(r"WHERE\s+(\w+)\s*=\s*'([^']+)'", raw_query, re.IGNORECASE)
        if match:
            key, value = match.groups()
            mongo_query = {key: value}
            redis_query = value
        else:
            mongo_query = {}
            redis_query = ""

        return {
            'mysql': raw_query,
            'postgresql': raw_query,
            'mongodb': mongo_query,
            'redis': redis_query
        }

    elif source_db == 'redis':
        key_value = raw_query.strip()
        sql_query = f"SELECT * FROM sample WHERE name = '{key_value}';"
        mongo_query = {'name': key_value}

        return {
            'mysql': sql_query,
            'postgresql': sql_query,
            'mongodb': mongo_query,
            'redis': key_value
        }

    else:
        raise NotImplementedError(f"Query translation not supported for database: {source_db}")

def run_query_with_metrics(connector, query):
    process = psutil.Process()  # Get current process
    
    cpu_before = psutil.cpu_percent(interval=None)
    mem_before = process.memory_info().rss 
    
    start = time.time()
    connector(query)
    end = time.time()
    
    cpu_after = psutil.cpu_percent(interval=None)
    mem_after = process.memory_info().rss
    
    return {
        'execution_time': round(end - start, 4),
        'cpu_usage': round(cpu_after - cpu_before, 2),
        'memory_usage': max(0, mem_after - mem_before) 
    }

def run_parallel(connector, query, concurrency):
    if query is None:
        raise ValueError("Query cannot be None")
    
    threads = []
    results = []
    lock = threading.Lock()

    def thread_func():
        try:
            result = run_query_with_metrics(connector, query)
        except Exception as e:
            result = {'error': str(e)}
        with lock:
            results.append(result)

    for _ in range(concurrency):
        t = threading.Thread(target=thread_func)
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results

def run_benchmark(data):
    try:
        results = {}

        db_connectors = {
            'mysql': mysql_run_query,
            'mongodb': mongo_run_query,
            'postgresql': postgres_run_query,
            'redis': redis_run_query
        }

        raw_query = data.get('query')
        if not raw_query:
            raise ValueError("No query provided in the request")

        source_db = data.get('database') 
        if not source_db:
            raise ValueError("No source database specified")

        parallel = data.get('parallel', False)
        concurrency = data.get('concurrency', 1)

        translated_queries = translate_query(source_db, raw_query)

        # Benchmark each database
        for db_name, query in translated_queries.items():
            connector = db_connectors.get(db_name.lower())
            if not connector:
                results[db_name] = {'error': f'Unsupported database: {db_name}'}
                continue

            if parallel:
                thread_results = run_parallel(connector, query, concurrency)
                avg_time = round(sum(r.get('execution_time', 0) for r in thread_results) / len(thread_results), 4)
                avg_cpu = round(sum(r.get('cpu_usage', 0) for r in thread_results) / len(thread_results), 2)
                avg_mem = sum(r.get('memory_usage', 0) for r in thread_results) // len(thread_results)

                results[db_name] = {
                    'execution_time': avg_time,
                    'cpu_usage': avg_cpu,
                    'memory_usage': avg_mem
                }
            else:
                result = run_query_with_metrics(connector, query)
                results[db_name] = result

        return results

    except Exception as e:
        return {'error': f'Benchmark failed: {str(e)}'}