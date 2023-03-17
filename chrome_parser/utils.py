import json
import os

import aiohttp
import dotenv

dotenv.load_dotenv()

PROXY_ENABLED = bool(int(os.environ.get('PROXY_ENABLED', 0)))
DEFAULT_CHROME_LANG = os.environ.get('DEFAULT_CHROME_LANG', 'en')
DEFAULT_CHROME_COUNTRY = os.environ.get('DEFAULT_CHROME_COUNTRY', 'US')


def extract_data_from_app(el, mappings):
    res = {}
    for key, spec_value in mappings.items():
        if isinstance(spec_value, list):
            res[key] = nested_lookup(el, spec_value, True)
        else:
            res[key] = spec_value['fun'](
                nested_lookup(el, spec_value['path'], True))
    return res


def nested_lookup(source, indexes, none_on_error=False):
    """Recursive nested_lookup. (never reaches recursive deep. must be ok.)"""
    try:
        if len(indexes) == 1:
            return source[indexes[0]]
        return nested_lookup(source[indexes[0]], indexes[1::])
    except (TypeError, IndexError) as exc:
        if none_on_error:
            return None
        else:
            raise exc


# This code is duplicated with playstore parser. It's ok, we have this because
# we want to make 2 SEPARATED parsers. so removing this will not break other.
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
