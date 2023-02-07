import itertools
import urllib.parse
from pprint import pprint

from . import specs
from . import utils


PLAY_STORE_BASE_URL = "https://play.google.com"
SAFETY_URL = f'{PLAY_STORE_BASE_URL}/store/apps/datasafety?'

def map_data_entries(entries):
    if not entries:
        return []
    res = []
    for entry in entries:
        entry_res = []
        type_ = specs.nested_lookup(entry, [0, 1])
        details = specs.nested_lookup(entry, [4])
        for detail in details:
            entry_res.append({
                'data': specs.nested_lookup(detail, [0]),
                'optional': specs.nested_lookup(detail, [1]),
                'purpose': specs.nested_lookup(detail, [2]),
                'type': type_
            })
        res.append(entry_res)
    res = list(itertools.chain(*res))
    return res


def map_security_practices(entries):
    if not entries:
        return []
    res = []
    for entry in entries:
        res.append({
            'practice': specs.nested_lookup(entry, [1]),
            'description': specs.nested_lookup(entry, [2, 1])
        })
    return res


MAPPINGS = {
    'sharedData': {
        'path': ['ds:3', 1, 2, 137, 4, 0, 0],
        'fun': map_data_entries
    },
    'collectedData': {
        'path': ['ds:3', 1, 2, 137, 4, 1, 0],
        'fun': map_data_entries
    },
    'securityPractices': {
        'path': ['ds:3', 1, 2, 137, 9, 2],
        'fun': map_security_practices
    },
    'privacyPolicyUrl': ['ds:3', 1, 2, 99, 0, 5, 2]
}


async def get_app_safety_data(app_id: str, lang: str | None = None):
    url = SAFETY_URL + f'id={app_id}'
    if lang:
        url += f'&hl={lang}'
    res = await utils.get_page(url)
    res = utils.parse_dataset_dom(res)
    res = utils.extract_data_from_app(res, MAPPINGS)
    return res

if __name__ == '__main__':
    import asyncio
    async def main():
        res = await get_app_safety_data('ru.sports')
        #print(res)
    asyncio.run(main())