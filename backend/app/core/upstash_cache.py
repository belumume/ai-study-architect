"""
Upstash Redis REST API client for serverless Redis caching
"""

import os
import json
import requests
import logging
from typing import Any, Optional
from datetime import timedelta

logger = logging.getLogger(__name__)


class UpstashRedisClient:
    """REST-based Redis client for Upstash (works on serverless)"""
    
    def __init__(self):
        self.url = os.getenv("UPSTASH_REDIS_REST_URL")
        self.token = os.getenv("UPSTASH_REDIS_REST_TOKEN")
        self.headers = {}
        
        if self.url and self.token:
            self.headers = {"Authorization": f"Bearer {self.token}"}
            self.connected = True
            logger.info("Upstash Redis connected via REST API")
        else:
            self.connected = False
            logger.warning("Upstash Redis not configured, using mock cache")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Upstash Redis"""
        if not self.connected:
            return None
            
        try:
            response = requests.get(
                f"{self.url}/get/{key}",
                headers=self.headers
            )
            if response.status_code == 200:
                data = response.json()
                result = data.get("result")
                if result:
                    # Try to parse JSON if it looks like JSON
                    try:
                        return json.loads(result)
                    except (json.JSONDecodeError, TypeError):
                        return result
            return None
        except Exception as e:
            logger.warning(f"Upstash get failed for {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Set value in Upstash Redis with optional TTL in seconds"""
        if not self.connected:
            return True  # Mock success
            
        try:
            # Serialize value to JSON
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            # Build command
            command = ["SET", key, value]
            if ex:
                command.extend(["EX", str(ex)])
            
            response = requests.post(
                f"{self.url}/",
                headers=self.headers,
                json=command
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Upstash set failed for {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from Upstash Redis"""
        if not self.connected:
            return True
            
        try:
            response = requests.post(
                f"{self.url}/",
                headers=self.headers,
                json=["DEL", key]
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Upstash delete failed for {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Upstash Redis"""
        if not self.connected:
            return False
            
        try:
            response = requests.post(
                f"{self.url}/",
                headers=self.headers,
                json=["EXISTS", key]
            )
            if response.status_code == 200:
                return response.json().get("result", 0) > 0
            return False
        except Exception as e:
            logger.warning(f"Upstash exists check failed for {key}: {e}")
            return False
    
    def ping(self) -> bool:
        """Check if Upstash is reachable"""
        if not self.connected:
            return False
            
        try:
            response = requests.post(
                f"{self.url}/",
                headers=self.headers,
                json=["PING"]
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern (use sparingly)"""
        if not self.connected:
            return []
            
        try:
            response = requests.post(
                f"{self.url}/",
                headers=self.headers,
                json=["KEYS", pattern]
            )
            if response.status_code == 200:
                return response.json().get("result", [])
            return []
        except Exception as e:
            logger.warning(f"Upstash keys failed for {pattern}: {e}")
            return []
    
    def info(self) -> dict:
        """Get Upstash stats"""
        if not self.connected:
            return {}
            
        try:
            # Get database info via INFO command
            response = requests.post(
                f"{self.url}/",
                headers=self.headers,
                json=["INFO", "stats"]
            )
            if response.status_code == 200:
                info_str = response.json().get("result", "")
                # Parse INFO output
                stats = {}
                for line in info_str.split("\n"):
                    if ":" in line:
                        key, value = line.split(":", 1)
                        stats[key] = value
                return stats
            return {}
        except Exception as e:
            logger.warning(f"Upstash info failed: {e}")
            return {}