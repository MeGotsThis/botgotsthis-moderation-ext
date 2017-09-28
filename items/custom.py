from typing import Collection, Iterable

from lib.data import CustomCommandField, CustomCommandProcess


def fields() -> Iterable[CustomCommandField]:
    return []


def properties() -> Collection[str]:
    return []


def postProcess() -> Iterable[CustomCommandProcess]:
    return []
