"""
Caching system for analysis results
"""

class CacheManager:
    """Manages caching of analysis results."""
    
    def __init__(self):
        self._cache = {}
    
    def get(self, key: str):
        """Get cached result."""
        return self._cache.get(key)
    
    def set(self, key: str, value):
        """Set cached result."""
        self._cache[key] = value