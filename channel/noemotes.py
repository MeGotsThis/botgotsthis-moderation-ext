from contextlib import suppress
from typing import Dict, List, Optional, cast  # noqa: F401

from lib.data import ChatCommandArgs
from lib.helper import parser, timeout
from lib.helper.chat import feature, min_args, permission


@feature('emotespam')
@permission('bannable')
@permission('chatModerator')
async def filterEmoteSpam(args: ChatCommandArgs) -> bool:
    properties: List[str]
    properties = ['noemotesThreshold', 'noemotesSubscriberThreshold',
                  'noemotesSilent']
    thresholds: Dict[str, Optional[int]]
    thresholds = await args.data.getChatProperties(
        args.chat.channel, properties, None, int)
    if thresholds['noemotesThreshold'] == 0:
        return False
    threshold: int = thresholds['noemotesThreshold'] or 5
    if args.permissions.subscriber:
        if thresholds['noemotesSubscriberThreshold'] == 0:
            return False
        threshold = thresholds['noemotesSubscriberThreshold'] or threshold
    count: int = 0
    with suppress(ValueError):
        if (args.tags is not None and 'emotes' in args.tags
                and args.tags['emotes']):
            emoteList: str = cast(str, args.tags['emotes'])
            emotes: List[List[str]]
            emotes = [e.split(':')[1].split(',') for e in emoteList.split('/')]
            count = sum(map(len, emotes))
    if count > threshold:
        reason: Optional[str]
        if thresholds['noemotesSilent']:
            reason = None
        else:
            reason = 'Too many Emotes'
        await timeout.timeout_user(args.data, args.chat, args.nick,
                                   'noemotes', 0, str(args.message), reason)
        if not args.permissions.owner:
            return True
    return False


@feature('emotespam')
@min_args(2)
@permission('broadcaster')
async def commandSetEmoteSpamMode(args: ChatCommandArgs) -> bool:
    value: Optional[int]
    try:
        value = int(args.message[2])
    except (IndexError, ValueError):
        value = None

    if args.message.lower[1] == 'threshold':
        await args.data.setChatProperty(
            args.chat.channel, 'noemotesSubscriberThreshold',
            str(value) if value is not None else None)
        if value is None:
            args.chat.send('''\
Set the emote spam threshold to the default (5 emotes)''')
        elif value:
            args.chat.send(f'Set the emote spam threshold to {value} emotes')
        else:
            args.chat.send('Set the emote spam threshold to unlimited emotes')
    if args.message.lower[1] == 'subscribers':
        await args.data.setChatProperty(
            args.chat.channel, 'noemotesSubscriberThreshold',
            str(value) if value is not None else None)
        if value is None:
            args.chat.send('''\
Set the emote spam threshold for subscribers to the default (normal threshold)\
''')
        elif value:
            args.chat.send(f'''\
Set the emote spam threshold for subscribers to {value} emotes''')
        else:
            args.chat.send('''\
Set the emote spam threshold for subscribers to unlimited emotes''')
    if args.message.lower[1] == 'silent':
        value = None
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
        await args.data.setChatProperty(
            args.chat.channel, 'noemotesSilent',
            str(value) if value is not None else None)
        if value is None:
            args.chat.send('''\
Silent timeouts for emotes spam has been reverted to default behavior \
(disabled)''')
        elif value:
            args.chat.send('''\
Silent timeouts for emotes spam has been enabled in this chat''')
        else:
            args.chat.send('''\
Silent timeouts for emotes spam has been disabled in this chat''')
    return True
