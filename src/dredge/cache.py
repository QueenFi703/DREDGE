"""
DREDGE Cache and Persistence Layer
Provides caching for spectra, unified inference results, and model outputs.
Supports both in-memory and persistent storage backends.
"""
import json
import time
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, Union, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("DREDGE.Cache")


class CacheBackend:
    """Base class for cache backends."""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        raise NotImplementedError
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL in seconds."""
        raise NotImplementedError
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        raise NotImplementedError
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        raise NotImplementedError
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        raise NotImplementedError


class MemoryCache(CacheBackend):
    """In-memory cache backend with TTL support."""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info("Initialized in-memory cache")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache, respecting TTL."""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        
        # Check TTL
        if entry.get('expires_at'):
            if time.time() > entry['expires_at']:
                # Expired - delete and return None
                del self._cache[key]
                logger.debug(f"Cache entry expired: {key}")
                return None
        
        logger.debug(f"Cache hit: {key}")
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            entry = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl if ttl else None
            }
            self._cache[key] = entry
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)" if ttl else f"Cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to set cache entry: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache delete: {key}")
            return True
        return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        active_entries = 0
        expired_entries = 0
        
        for key, entry in self._cache.items():
            if entry.get('expires_at') and time.time() > entry['expires_at']:
                expired_entries += 1
            else:
                active_entries += 1
        
        return {
            'total_entries': len(self._cache),
            'active_entries': active_entries,
            'expired_entries': expired_entries
        }


class FileCache(CacheBackend):
    """File-based persistent cache backend."""
    
    def __init__(self, cache_dir: Union[str, Path] = ".cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Initialized file cache: {self.cache_dir}")
    
    def _get_path(self, key: str) -> Path:
        """Get file path for cache key."""
        # Hash the key to create a safe filename
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.json"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from file cache."""
        path = self._get_path(key)
        
        if not path.exists():
            return None
        
        try:
            with open(path, 'r') as f:
                entry = json.load(f)
            
            # Check TTL
            if entry.get('expires_at'):
                if time.time() > entry['expires_at']:
                    # Expired - delete and return None
                    path.unlink()
                    logger.debug(f"Cache entry expired: {key}")
                    return None
            
            logger.debug(f"Cache hit: {key}")
            return entry['value']
        except Exception as e:
            logger.error(f"Failed to read cache entry: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in file cache."""
        path = self._get_path(key)
        
        try:
            entry = {
                'value': value,
                'created_at': time.time(),
                'expires_at': time.time() + ttl if ttl else None,
                'key': key  # Store original key for debugging
            }
            
            with open(path, 'w') as f:
                json.dump(entry, f)
            
            logger.debug(f"Cache set: {key} (TTL: {ttl}s)" if ttl else f"Cache set: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to write cache entry: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from file cache."""
        path = self._get_path(key)
        
        if path.exists():
            path.unlink()
            logger.debug(f"Cache delete: {key}")
            return True
        return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        count = 0
        for path in self.cache_dir.glob("*.json"):
            path.unlink()
            count += 1
        logger.info(f"Cleared {count} cache entries")
        return True
    
    def exists(self, key: str) -> bool:
        """Check if key exists and is not expired."""
        return self.get(key) is not None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = len(list(self.cache_dir.glob("*.json")))
        return {
            'total_entries': total,
            'cache_dir': str(self.cache_dir)
        }


class ResultCache:
    """
    High-level cache for DREDGE results with type-specific handling.
    Caches spectra, unified inference, and model inference results.
    """
    
    def __init__(self, backend: Optional[CacheBackend] = None, default_ttl: int = 3600):
        """
        Initialize result cache.
        
        Args:
            backend: Cache backend (defaults to MemoryCache)
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.backend = backend or MemoryCache()
        self.default_ttl = default_ttl
        logger.info(f"Initialized ResultCache with TTL={default_ttl}s")
    
    def _make_key(self, prefix: str, params: Dict[str, Any]) -> str:
        """Create cache key from prefix and parameters."""
        # Sort params for consistent keys
        param_str = json.dumps(params, sort_keys=True)
        key_hash = hashlib.sha256(param_str.encode()).hexdigest()
        return f"{prefix}:{key_hash[:16]}"
    
    def get_spectrum(self, max_modes: int, dimensions: int) -> Optional[Dict[str, Any]]:
        """Get cached string spectrum."""
        key = self._make_key("spectrum", {"max_modes": max_modes, "dimensions": dimensions})
        return self.backend.get(key)
    
    def set_spectrum(self, max_modes: int, dimensions: int, result: Dict[str, Any], 
                     ttl: Optional[int] = None) -> bool:
        """Cache string spectrum result."""
        key = self._make_key("spectrum", {"max_modes": max_modes, "dimensions": dimensions})
        return self.backend.set(key, result, ttl or self.default_ttl)
    
    def get_unified_inference(self, dredge_insight: str, quasimoto_coords: List[float], 
                             string_modes: List[int]) -> Optional[Dict[str, Any]]:
        """Get cached unified inference result."""
        key = self._make_key("unified", {
            "insight": dredge_insight,
            "coords": quasimoto_coords,
            "modes": string_modes
        })
        return self.backend.get(key)
    
    def set_unified_inference(self, dredge_insight: str, quasimoto_coords: List[float],
                             string_modes: List[int], result: Dict[str, Any],
                             ttl: Optional[int] = None) -> bool:
        """Cache unified inference result."""
        key = self._make_key("unified", {
            "insight": dredge_insight,
            "coords": quasimoto_coords,
            "modes": string_modes
        })
        return self.backend.set(key, result, ttl or self.default_ttl)
    
    def get_inference(self, model_id: str, inputs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached model inference result."""
        key = self._make_key(f"inference:{model_id}", inputs)
        return self.backend.get(key)
    
    def set_inference(self, model_id: str, inputs: Dict[str, Any], result: Dict[str, Any],
                     ttl: Optional[int] = None) -> bool:
        """Cache model inference result."""
        key = self._make_key(f"inference:{model_id}", inputs)
        return self.backend.set(key, result, ttl or self.default_ttl)
    
    def clear(self) -> bool:
        """Clear all cached results."""
        return self.backend.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self.backend.get_stats()
        stats['default_ttl'] = self.default_ttl
        stats['backend_type'] = type(self.backend).__name__
        return stats
