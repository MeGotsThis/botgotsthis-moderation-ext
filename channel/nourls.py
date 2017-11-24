import asyncio
import re
from datetime import datetime
from typing import Any, List, Mapping, Optional, Set, Tuple  # noqa: F401

import aioodbc.cursor  # noqa: F401

from bot import data, utils  # noqa: F401
from lib import cache
from lib.data import ChatCommandArgs
from lib.data.message import Message
from lib.database import DatabaseMain
from lib.helper import parser, timeout
from lib.helper.chat import feature, min_args, not_permission, permission
from lib.helper.message import messagesFromItems
from ..library import nourls as library


@feature('nolinks')
@permission('bannable')
@permission('chatModerator')
async def filterNoUrl(args: ChatCommandArgs) -> bool:
    properties: List[str] = ['nourlAllowSubscriber', 'nourlSilent']
    modes: Mapping[str, bool] = await args.data.getChatProperties(
        args.chat.channel, properties, False, bool)
    if modes['nourlAllowSubscriber'] and args.permissions.subscriber:
        return False
    matches: List[str]
    matches = re.findall(parser.twitchUrlRegex, str(args.message))
    if matches:
        whitelist: Set[str]
        whitelist = await library.get_urls_whitelist(args.chat.channel,
                                                     args.data)
        for match in matches:
            good: bool = False
            for w in whitelist:
                if w in match:
                    good = True
                    break
            if not good:
                reason: Optional[str]
                if modes['nourlSilent']:
                    reason = None
                else:
                    reason = 'No URLs are allowed'
                await timeout.timeout_user(
                    args.data, args.chat, args.nick, 'nourl', 0,
                    str(args.message), reason)
                if not args.permissions.owner:
                    return True
    return False


@feature('annoyinglinks')
@not_permission('moderator')
@permission('chatModerator')
async def filterAnnoyingUrl(args: ChatCommandArgs) -> bool:
    properties: List[str] = ['nourlAllowSubscriber', 'nourlSilent']
    modes: Mapping[str, bool] = await args.data.getChatProperties(
        args.chat.channel, properties, False, bool)
    if modes['nourlAllowSubscriber'] and args.permissions.subscriber:
        return False
    matches: List[str] = re.findall(parser.twitchUrlRegex, str(args.message))
    if matches:
        badUrls: List[str] = [
            'strawpoii.me',
        ]
        botUrls: List[str] = await library.get_bot_urls(args.data)
        for match in matches:
            bad: bool = False
            level: int = 0
            badUrl: str
            for badUrl in badUrls:
                if badUrl in match.lower():
                    bad = True
                    break
            for badUrl in botUrls:
                if badUrl in match.lower():
                    bad = True
                    level = 1
                    break
            if bad:
                reason: Optional[str]
                if modes['nourlSilent']:
                    reason = None
                else:
                    reason = 'No Annoying URLs are allowed'
                await timeout.timeout_user(
                    args.data, args.chat, args.nick, 'annoyurl', level,
                    str(args.message), reason)
                return True
    return False


@feature('nolinks')
@min_args(2)
@permission('broadcaster')
async def commandSetUrlMode(args: ChatCommandArgs) -> bool:
    value: Optional[bool] = None
    if len(args.message) > 2:
        response: parser.Response
        response = parser.get_response(args.message.lower[2])
        if response == parser.Unknown:
            args.chat.send(f'''\
Unrecognized second parameter: {args.message[2]}''')
            return True
        if response == parser.Yes:
            value = True
        if response == parser.No:
            value = False

    if args.message.lower[1] == 'subscribers':
        await args.data.setChatProperty(
            args.chat.channel, 'nourlAllowSubscriber',
            utils.property_bool(value))
        if value is None:
            args.chat.send('''\
Subscriber URLs/links allowance have been reverted to default behavior \
(disabled)''')
        elif value:
            args.chat.send('''\
Subscribers are allowed to post URLs/links in this chat''')
        else:
            args.chat.send('''\
Subscribers are not allowed to post URLs/links in this chat''')
    if args.message.lower[1] == 'silent':
        await args.data.setChatProperty(args.chat.channel, 'nourlSilent',
                                        utils.property_bool(value))
        if value is None:
            args.chat.send('''\
Silent timeouts for URLs/links has been reverted to default behavior \
(disabled)''')
        elif value:
            args.chat.send('''\
Silent timeouts for URLs/links has been enabled in this chat''')
        else:
            args.chat.send('''\
Silent timeouts for URLs/links has been disabled in this chat''')
    return True


@feature('nolinks')
@min_args(2)
@permission('broadcaster')
async def commandUrlWhitelist(args: ChatCommandArgs) -> bool:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    query: str
    params: Tuple[Any, ...]

    if args.message.lower[1] == 'list':
        whitelist: List[str]
        async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
            query = 'SELECT urlMatch FROM url_whitelist WHERE broadcaster=?'
            whitelist = [w async for w,
                         in await cursor.execute(query, (args.chat.channel,))]
        args.chat.send(messagesFromItems(whitelist, 'Whitelisted URLs: '))
        return True

    if len(args.message) < 3:
        return False

    if args.message.lower[1] in ['add', 'insert', 'new']:
        async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
            try:
                query = '''
INSERT INTO url_whitelist (broadcaster, urlMatch) VALUES (?, ?)
'''
                params = args.chat.channel, args.message.lower[2]
                await cursor.execute(query, params)
                await db.commit()
                await library.reset_urls_whitelist(args.chat.channel,
                                                   args.data)
                args.chat.send(f'''\
{args.message.lower[2]} has been added to the URL whitelist''')
            except Exception:
                args.chat.send(f'''\
{args.message.lower[2]} could not have been added to URL whitelist, it might \
be already there''')
        return True
    if args.message.lower[1] in ['del', 'delete', 'rem', 'remove']:
        async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
            query = '''
DELETE FROM url_whitelist WHERE broadcaster=? AND urlMatch=?
'''
            params = args.chat.channel, args.message.lower[2]
            await cursor.execute(query, params)
            await db.commit()
            await library.reset_urls_whitelist(args.chat.channel, args.data)
            if cursor.rowcount == 0:
                args.chat.send(f'''\
{args.message.lower[2]} could not been removed from the URL whitelist, it \
might not be there''')
            else:
                args.chat.send(f'''\
{args.message.lower[2]} has been removed from the URL whitelist
''')
        return True
    return False


@permission('bannable')
async def filterAnyUrlWithNoFollows(args: ChatCommandArgs) -> bool:
    if re.search(parser.twitchUrlRegex, str(args.message)):
        asyncio.ensure_future(
            log_url_if_no_follow(
                args.chat, args.nick, args.message, args.timestamp))
    return False


async def log_url_if_no_follow(chat: 'data.Channel',
                               nick: str,
                               message: Message,
                               timestamp: datetime) -> None:
    dataCache: cache.CacheStore
    async with cache.get_cache() as dataCache:
        if await dataCache.twitch_num_followers(nick):
            return

    # Record all urls with users of no follows
    utils.print(f'{chat.ircChannel} {nick}: {message}',
                file='no-follow-url.log', timestamp=timestamp)
