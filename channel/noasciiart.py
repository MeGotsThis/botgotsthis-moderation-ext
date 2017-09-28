import re
from contextlib import suppress
from typing import Optional  # noqa: F401

from bot import utils
from lib.data import ChatCommandArgs
from lib.helper import parser, timeout
from lib.helper.chat import feature, permission

minMessageLength: int = 50
defaultThreshold: float = 60.0


@feature('noasciiart')
@permission('bannable')
@permission('chatModerator')
async def filterAsciiArt(args: ChatCommandArgs) -> bool:
    if len(args.message) < minMessageLength:
        return False

    countNoAlphaNum: int = sum(len(s) for s
                               in re.findall(r'[^\w\s]+', str(args.message)))
    threshold: float = await args.database.getChatProperty(
        args.chat.channel, 'asciiArtThreshold', defaultThreshold, float)
    if countNoAlphaNum / len(args.message) >= threshold / 100.0:
        reason: Optional[str]
        if await args.database.getChatProperty(
                args.chat.channel, 'noasciiartSilent', False, int):
            reason = None
        else:
            reason = 'ASCII Art is banned'
        await timeout.timeout_user(
            args.database, args.chat, args.nick, 'noasciiart', 0,
            str(args.message), reason)
        if not args.permissions.owner:
            return True
    return False


@feature('noasciiart')
@permission('broadcaster')
async def commandSetAsciiThreshold(args: ChatCommandArgs) -> bool:
    threshold: Optional[float] = None
    with suppress(ValueError):
        if len(args.message) >= 2:
            threshold = float(args.message[1])
    await args.database.setChatProperty(args.chat.channel, 'asciiArtThreshold',
                                        str(threshold))
    if threshold is None:
        args.chat.send(f'''\
Set the ASCII Art Threshold to the default {defaultThreshold}%''')
    else:
        args.chat.send(f'Set the ASCII Art Threshold to {threshold}%')
    return True


@feature('noasciiart')
@permission('broadcaster')
async def commandSetAsciiArtSilent(args: ChatCommandArgs) -> bool:
    value: Optional[bool] = None
    if len(args.message) > 1:
        response: parser.Response
        response = parser.get_response(args.message.lower[1])
        if response == parser.Unknown:
            args.chat.send(f'''\
        Unrecognized second parameter: {args.message[1]}''')
            return True
        if response == parser.Yes:
            value = True
        if response == parser.No:
            value = False

    await args.database.setChatProperty(
        args.chat.channel, 'noasciiartSilent', utils.property_bool(value))
    if value is None:
        args.chat.send('''\
Silent timeouts for ascii art has been reverted to default behavior (disabled)\
''')
    elif value:
        args.chat.send('''\
Silent timeouts for ascii art has been enabled in this chat''')
    else:
        args.chat.send('''\
Silent timeouts for ascii art has been disabled in this chat''')
    return True
