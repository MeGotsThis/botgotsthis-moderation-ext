from datetime import datetime

from lib import cache

from .library import nourls


async def loadBadUrls(timestamp: datetime) -> None:
    data: cache.CacheStore
    async with cache.get_cache() as data:
        await nourls.get_bad_urls(data, background=True)
        await nourls.get_bot_urls(data, background=True)
