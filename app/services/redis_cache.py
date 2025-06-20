import redis
import os
import json

redis_client = redis.Redis.from_url(os.getenv("REDIS_URL"), decode_responses=True)

def get_chat_memory(chat_id):
    key = f"chat_memory:{chat_id}"
    memory = redis_client.lrange(key, 0, -1)
    return [json.loads(msg) for msg in memory]

def store_chat_memory(chat_id, msg, res):
    key = f"chat_memory:{chat_id}"
    entry = json.dumps({"msg": msg, "res": res})
    redis_client.rpush(key, entry)
    redis_client.ltrim(key, -20, -1)  
