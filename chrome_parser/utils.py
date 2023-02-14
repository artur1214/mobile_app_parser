import json
import os

import aiohttp
import dotenv

dotenv.load_dotenv()

PROXY_ENABLED = bool(int(os.environ.get('PROXY_ENABLED', 0)))



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
