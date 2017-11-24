import datetime

from bot.coroutine import background
from . import tasks


async def call_load(timestamp: datetime.datetime) -> None:
    await tasks.loadBadUrls(timestamp)


background.add_task(call_load, datetime.timedelta(seconds=1))
