from typing import Optional, Any
from datetime import datetime, timedelta
import json


class CacheService:
    """内存缓存服务（本地使用，无需Redis）"""

    def __init__(self):
        self._cache: dict[str, tuple[Any, datetime]] = {}
        self._default_ttl = 3600  # 默认1小时过期

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key not in self._cache:
            return None

        value, expire_time = self._cache[key]

        # 检查是否过期
        if datetime.now() > expire_time:
            del self._cache[key]
            return None

        return value

    def set(self, key: str, value: Any, ttl: int = None) -> None:
        """设置缓存"""
        if ttl is None:
            ttl = self._default_ttl

        expire_time = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expire_time)

    def delete(self, key: str) -> None:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def exists(self, key: str) -> bool:
        """检查缓存是否存在且未过期"""
        return self.get(key) is not None

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        """批量获取缓存"""
        result = {}
        for key in keys:
            value = self.get(key)
            if value is not None:
                result[key] = value
        return result

    def set_many(self, data: dict[str, Any], ttl: int = None) -> None:
        """批量设置缓存"""
        for key, value in data.items():
            self.set(key, value, ttl)

    def cleanup_expired(self) -> int:
        """清理过期缓存，返回清理数量"""
        now = datetime.now()
        expired_keys = [
            key for key, (_, expire_time) in self._cache.items()
            if now > expire_time
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)


# 全局缓存实例
cache_service = CacheService()
