import json
from typing import Optional, Set

import aioodbc.cursor

from lib.cache import CacheStore
from lib.database import DatabaseMain


def _redisKey(broadcaster: str) -> str:
    return f'twitch:{broadcaster}:auto-ban-words'


async def get_auto_ban_words(broadcaster: str, data: CacheStore) -> Set[str]:
    words: Set[str]
    key: str = _redisKey(broadcaster)
    val: Optional[str] = await data.redis.get(key)
    if val is None:
        words = await get_auto_ban_words_db(broadcaster)
        await data.redis.setex(key, 3600, json.dumps(list(words)))
    else:
        words = set(json.loads(val))
    return words


async def get_auto_ban_words_db(broadcaster: str) -> Set[str]:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    words: Set[str] = set()
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = '''
SELECT word FROM auto_ban_words WHERE broadcaster=?
'''
        word: str
        async for word, in await cursor.execute(query, (broadcaster,)):
            words.add(word)
        return words


async def reset_auto_ban_words(broadcaster: str, data: CacheStore) -> None:
    await data.redis.delete(_redisKey(broadcaster))
