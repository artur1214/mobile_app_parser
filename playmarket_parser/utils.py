import json
import os

import aiohttp
import dotenv

from . import regexes
from . import specs

dotenv.load_dotenv()
# PROXY_URL = os.environ.get('PROXY_URL')
# PROXY_PASS = os.environ.get('PROXY_PASS')
# PROXY_USER = os.environ.get('PROXY_USER')
# PROXY_AUTH_NEEDED = os.environ.get('PROXY_NEED_AUTH')
# PROXY_AUTH = aiohttp.BasicAuth(
#     PROXY_USER, PROXY_PASS) if PROXY_AUTH_NEEDED else None

PROXY_ENABLED = bool(int(os.environ.get('PROXY_ENABLED', 0)))


def extract_data_from_app(el, mappings):
    res = {}
    for key, spec_value in mappings.items():
        if isinstance(spec_value, list):
            res[key] = specs.nested_lookup(el, spec_value, True)
        else:
            res[key] = spec_value['fun'](
                specs.nested_lookup(el, spec_value['path'], True))
    return res


async def get_page(url: str,
                   timeout: int | None = None, none_on: int | list[int] = None):
    """Makes get request to page with proxy (if enabled)

    Args:
        url (str): url to process.
        timeout (int|None): connection max time in seconds.
        none_on (int | list[int]):
    """
    if timeout is not None:
        timeout = aiohttp.ClientTimeout(connect=timeout)
    else:
        timeout = aiohttp.ClientTimeout(total=300)
    # proxy_params = {
    #     'proxy': PROXY_URL,
    #     'proxy_auth': PROXY_AUTH
    # } if PROXY_URL else {}
    async with aiohttp.ClientSession(timeout=timeout,
                                     trust_env=PROXY_ENABLED) as session:
        async with session.get(url) as resp:
            if none_on is not None:
                if (isinstance(none_on, int) and none_on == resp.status) \
                        or (isinstance(none_on, (list, tuple, set))
                            and resp.status in none_on):
                    return None
            res = await resp.text()
            return res


async def post_page(url, data):
    # proxy_params = {
    #     'proxy': PROXY_URL,
    #     'proxy_auth': PROXY_AUTH
    # } if PROXY_URL else {}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }) as resp:
            res = await resp.text()
            return res

def parse_dataset_dom(dom: str):
    """Parses main dataset from dom. (from script tags)"""
    matches = regexes.SCRIPT.findall(dom)
    dataset = {}
    for match in matches:
        key_match = regexes.KEY.findall(match)
        value_match = regexes.VALUE.findall(match)
        if key_match and value_match:
            key = key_match[0]
            value = json.loads(value_match[0])
            dataset[key] = value
    return dataset
