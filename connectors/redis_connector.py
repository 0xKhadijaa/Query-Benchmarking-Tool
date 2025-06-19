import redis
import json

client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

def run_query(query):
    try:
        if not isinstance(query, str):
            raise TypeError(f"Redis query must be a string (key), got {type(query)}")
        value = client.get(query)

        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        else:
            return None 

    except redis.RedisError as e:
        # Print and log the Redis error
        print(f"Redis Error: {e}")
        return None
