# benchmark_tool/connectors/mongo_connector.py
import json
from pymongo import MongoClient

client = MongoClient('localhost', 27017)
db = client['test']
collection = db['test_collection']

def run_query(query):
    try:
        if isinstance(query, str):
            query = json.loads(query)

        if not isinstance(query, dict):
            raise TypeError(f"Query must be a dict, got {type(query)}")

        return list(collection.find(query))

    except Exception as e:
        raise Exception(f"MongoDB Query Error: {e}")
