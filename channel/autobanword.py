import aioodbc.cursor  # noqa: F401

from typing import List  # noqa: F401

from lib.data import ChatCommandArgs
from lib.database import DatabaseMain
from lib.helper import timeout
from lib.helper.chat import feature, min_args, permission
from lib.helper.message import messagesFromItems


@feature('autobanword')
@permission('bannable')
@permission('chatModerator')
async def filterAutoBanWord(args: ChatCommandArgs) -> bool:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
        query: str = 'SELECT word FROM auto_ban_words WHERE broadcaster=?'
        async for row in await cursor.execute(query, (args.chat.channel,)):
            if row[0] in args.message.lower:
                await timeout.timeout_user(
                    args.data, args.chat, args.nick, 'autobanword', 0,
                    str(args.message), 'One of the words you said is banned')
                if args.permissions.owner:
                    return False
                else:
                    return True
    return False


@feature('autobanword')
@min_args(2)
@permission('broadcaster')
async def commandManageBanWord(args: ChatCommandArgs) -> bool:
    db: DatabaseMain
    cursor: aioodbc.cursor.Cursor
    query: str
    if args.message.lower[1] in ['list', 'listWords']:
        async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
            query = '''
SELECT word FROM auto_ban_words WHERE broadcaster=? ORDER BY word
'''
            words: List[str]
            words = [word async for word,
                     in await cursor.execute(query, (args.chat.channel,))]
        if words:
            args.chat.send(messagesFromItems(words, 'Banned Words: '))
        else:
            args.chat.send('There are no words that are banned')
    elif args.message.lower[1] in ['add', 'insert', 'new']:
        if len(args.message) < 3:
            return False

        word: str = args.message.lower[2]
        async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
            try:
                query = '''
INSERT INTO auto_ban_words (broadcaster, word) VALUES (?, ?)
'''
                await cursor.execute(query, (args.chat.channel, word))
                await db.commit()
                args.chat.send(f'''\
{word} has been added to the autoban word list''')
            except Exception:
                args.chat.send(f'''\
{word} could not have been added to autoban word list, it might be already \
there''')
    elif args.message.lower[1] in ['del', 'delete', 'rem', 'remove']:
        if len(args.message) < 3:
            return False

        word = args.message.lower[2]
        async with DatabaseMain.acquire() as db, await db.cursor() as cursor:
            query = 'DELETE FROM auto_ban_words WHERE broadcaster=? AND word=?'
            await cursor.execute(query, (args.chat.channel, word))
            await db.commit()
            if cursor.rowcount == 0:
                args.chat.send(f'''\
{word} could not been removed from the autoban word list, it might not be \
there''')
            else:
                args.chat.send(f'''\
{word} has been removed from the autoban word list''')
    return True
