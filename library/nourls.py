import json
from typing import Optional, Set

import aioodbc.cursor

from lib.cache import CacheStore
from lib.database import DatabaseMain


def _redisKey(broadcaster: str) -> str:
    return f'twitch:{broadcaster}:urls-whitelist'


async def get_urls_whitelist(broadcaster: str, data: CacheStore) -> Set[str]:
    urls: Set[str]
    key: str = _redisKey(broadcaster)
    val: Optional[str] = await data.redis.get(key)
    if val is None:
        urls = await get_urls_whitelist_db(broadcaster)
        await data.redis.setex(key, 3600, json.dumps(list(urls)))
    else:
        urls = set(json.loads(val))
    return urls


async def get_urls_whitelist_db(broadcaster: str) -> Set[str]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    urls: Set[str] = set()
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT urlMatch FROM url_whitelist WHERE broadcaster=?
'''
        url: str
        async for url, in await cursor.execute(query, (broadcaster,)):
            urls.add(url)
        return urls


async def reset_urls_whitelist(broadcaster: str, data: CacheStore) -> None:
    await data.redis.delete(_redisKey(broadcaster))
