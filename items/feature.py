from typing import Mapping, Optional


def features() -> Mapping[str, Optional[str]]:
    if not hasattr(features, 'features'):
        setattr(features, 'features', {
            'autobanword': 'Auto Ban Word',
            'noasciiart': 'No Large ASCII Art',
            'nolinks': 'No URLs/Links',
            'annoyinglinks': 'No Annoying URLs/Links',
            'emotespam': 'No Emote Spam',
            })
    return getattr(features, 'features')
