"""
Redis Client Configuration

Provides Redis connection for caching and job state management
"""

import json
import os
from datetime import datetime
from typing import Any, Optional

import redis

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class RedisClient:
    """
    Redis client wrapper with connection pooling and error handling
    """

    def __init__(self):
        self.pool = redis.ConnectionPool(
            host=settings.redis.redis_host,
            port=settings.redis.redis_port,
            db=settings.redis.redis_db,
            password=settings.redis.redis_password or None,
            decode_responses=settings.redis.redis_decode_responses,
            max_connections=settings.redis.redis_max_connections,
        )
        self.client = redis.Redis(connection_pool=self.pool)
        self._test_connection()

    def _test_connection(self) -> None:
        """Test Redis connection"""
        try:
            self.client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            # During tests we allow skipping a real Redis instance
            if os.getenv("PYTEST_CURRENT_TEST"):
                logger.warning("Redis connection skipped in test environment")
                return

            logger.error(f"Failed to connect to Redis: {str(e)}", exc_info=True)
            raise

    def set(
        self, key: str, value: Any, expire: Optional[int] = None
    ) -> bool:
        """
        Set a value in Redis

        Args:
            key: Cache key
            value: Value to store (will be JSON serialized if not string)
            expire: Optional expiration time in seconds

        Returns:
            True if successful
        """
        try:
            if not isinstance(value, str):
                value = json.dumps(value, cls=DateTimeJSONEncoder)

            if expire:
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)

        except Exception as e:
            logger.error(f"Redis SET failed for key {key}: {str(e)}")
            return False

    def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get a value from Redis

        Args:
            key: Cache key
            deserialize: Whether to deserialize JSON

        Returns:
            Cached value or None if not found
        """
        try:
            value = self.client.get(key)

            if value is None:
                return None

            if deserialize and isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value

            return value

        except Exception as e:
            logger.error(f"Redis GET failed for key {key}: {str(e)}")
            return None

    def delete(self, key: str) -> bool:
        """
        Delete a key from Redis

        Args:
            key: Cache key to delete

        Returns:
            True if deleted
        """
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE failed for key {key}: {str(e)}")
            return False

    def exists(self, key: str) -> bool:
        """
        Check if key exists

        Args:
            key: Cache key

        Returns:
            True if exists
        """
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS failed for key {key}: {str(e)}")
            return False

    def expire(self, key: str, seconds: int) -> bool:
        """
        Set expiration on a key

        Args:
            key: Cache key
            seconds: Expiration time in seconds

        Returns:
            True if successful
        """
        try:
            return bool(self.client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE failed for key {key}: {str(e)}")
            return False

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """
        Increment a counter

        Args:
            key: Counter key
            amount: Increment amount

        Returns:
            New value or None if failed
        """
        try:
            return self.client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Redis INCR failed for key {key}: {str(e)}")
            return None

    def set_hash(self, name: str, mapping: dict) -> bool:
        """
        Set multiple hash fields

        Args:
            name: Hash name
            mapping: Dictionary of field-value pairs

        Returns:
            True if successful
        """
        try:
            # Serialize complex values
            serialized_mapping = {
                k: json.dumps(v) if not isinstance(v, str) else v
                for k, v in mapping.items()
            }
            return bool(self.client.hset(name, mapping=serialized_mapping))
        except Exception as e:
            logger.error(f"Redis HSET failed for hash {name}: {str(e)}")
            return False

    def get_hash(self, name: str) -> Optional[dict]:
        """
        Get all hash fields

        Args:
            name: Hash name

        Returns:
            Dictionary of field-value pairs or None
        """
        try:
            data = self.client.hgetall(name)
            if not data:
                return None

            # Deserialize values
            result = {}
            for k, v in data.items():
                try:
                    result[k] = json.loads(v)
                except json.JSONDecodeError:
                    result[k] = v

            return result

        except Exception as e:
            logger.error(f"Redis HGETALL failed for hash {name}: {str(e)}")
            return None

    def close(self) -> None:
        """Close Redis connection pool"""
        try:
            self.pool.disconnect()
            logger.info("Redis connection closed")
        except Exception as e:
            logger.error(f"Failed to close Redis connection: {str(e)}")


# Global Redis client instance
redis_client = RedisClient()
