# src/redis_cache.py
import redis
import json
import hashlib
from logging_config import logger
from vars import REDIS_HOST, REDIS_CACHE_TTL
import time

# Retry logic and singleton instance
MAX_RETRIES = 3
RETRY_DELAY = 30  # seconds

_redis_client = None  # Singleton placeholder

def get_redis_client():
    """Get or create the singleton Redis client."""
    global _redis_client
    if not _redis_client:
        _redis_client = connect_to_redis(REDIS_HOST, 6379, 0)
    return _redis_client

def connect_to_redis(host, port, db):
    retries = 0
    while retries < MAX_RETRIES:
        try:
            client = redis.Redis(host=host, port=port, db=db)
            client.ping()
            logger.info("Connected to Redis")
            return client
        except redis.ConnectionError as e:
            retries += 1
            logger.warning(f"Failed to connect to Redis (attempt {retries}/{MAX_RETRIES}): {e}")
            if retries < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
    raise Exception("Could not connect to Redis after several attempts")

def _make_cache_key(loris_tools_spread: dict) -> str:
    key_str = f"{loris_tools_spread['coin']}_{loris_tools_spread['buy_on']}_{loris_tools_spread['sell_on']}"
    return "markets_data:" + hashlib.md5(key_str.encode()).hexdigest()

def save_markets_data(loris_tools_spread: dict, markets_data: dict) -> bool:
    """Save markets_data for a given loris_tools_spread with TTL."""
    redis_client = get_redis_client()
    try:
        key = _make_cache_key(loris_tools_spread)
        redis_client.setex(key, REDIS_CACHE_TTL, json.dumps(markets_data))
        logger.info(f"Saved markets_data to Redis for {loris_tools_spread['coin']}")
        return True
    except Exception as e:
        logger.error(f"Failed to save to Redis: {e}")
        return False

def check_data_in_redis(loris_tools_spread: dict) -> bool:
    """Retrieve cached markets_data if available, else None."""
    redis_client = get_redis_client()
    try:
        key = _make_cache_key(loris_tools_spread)
        data = redis_client.get(key)
        if data:
            logger.info(f"Using cached markets_data for {loris_tools_spread['coin']}")
            return True
            # return json.loads(data)
        else:
            return False
    except Exception as e:
        logger.warning(f"Failed to read from Redis: {e}")
    return False