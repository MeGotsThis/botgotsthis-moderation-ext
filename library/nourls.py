import json
import os
from typing import List, Optional, Set

import aiofiles
import aioodbc.cursor

from lib.cache import CacheStore
from lib.database import DatabaseMain

botUrlFile: str = 'bot-urls.json'
botRegexUrlFile: str = 'bot-regex-urls.json'


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


async def get_bad_urls(data: CacheStore, background: bool=False) -> List[str]:
    return [
        'strawpoii.me',
    ]


async def get_bot_urls(data: CacheStore, background: bool=False) -> List[str]:
    urls: List[str]
    key: str = 'bot-urls'
    reload: bool = False
    val: Optional[str] = await data.redis.get(key)
    if background and val is not None:
        ttl: int = await data.redis.ttl(key)
        reload = ttl < 30
    if val is None or reload:
        urlData: str
        if os.path.isfile(botUrlFile):
            async with aiofiles.open(botUrlFile, 'r',
                                     encoding='utf-8') as file:
                urlData = await file.read(None)
        else:
            urlData = '[]'
        await data.redis.setex(key, 300, urlData)
        urls = json.loads(urlData)
    else:
        urls = json.loads(val)
    return urls


async def get_bot_regex_urls(data: CacheStore, background: bool=False
                             ) -> List[str]:
    urls: List[str]
    key: str = 'bot-regex-urls'
    reload: bool = False
    val: Optional[str] = await data.redis.get(key)
    if background and val is not None:
        ttl: int = await data.redis.ttl(key)
        reload = ttl < 30
    if val is None or reload:
        urlData: str
        if os.path.isfile(botRegexUrlFile):
            async with aiofiles.open(botRegexUrlFile, 'r',
                                     encoding='utf-8') as file:
                urlData = await file.read(None)
        else:
            urlData = '[]'
        await data.redis.setex(key, 300, urlData)
        urls = json.loads(urlData)
    else:
        urls = json.loads(val)
    return urls
