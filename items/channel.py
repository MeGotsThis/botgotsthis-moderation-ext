﻿from typing import Iterable, Mapping, Optional

from lib.data import ChatCommand

from ..channel import autobanword
from ..channel import noasciiart
from ..channel import noemotes
from ..channel import nourls


def filterMessage() -> Iterable[ChatCommand]:
    yield nourls.filterAnyUrlWithNoFollows
    yield autobanword.filterAutoBanWord
    yield noasciiart.filterAsciiArt
    yield noemotes.filterEmoteSpam
    yield nourls.filterNoUrl
    yield nourls.filterAnnoyingUrl


def commands() -> Mapping[str, Optional[ChatCommand]]:
    if not hasattr(commands, 'commands'):
        setattr(commands, 'commands', {
            '!managebanword': autobanword.commandManageBanWord,
            '!setasciithreshold': noasciiart.commandSetAsciiThreshold,
            '!setasciiartsilent': noasciiart.commandSetAsciiArtSilent,
            '!setemotespammode': noemotes.commandSetEmoteSpamMode,
            '!seturlmode': nourls.commandSetUrlMode,
            '!urlwhitelist': nourls.commandUrlWhitelist,
            }
        )
    return getattr(commands, 'commands')


def commandsStartWith() -> Mapping[str, Optional[ChatCommand]]:
    return {}


def processNoCommand() -> Iterable[ChatCommand]:
    return []
