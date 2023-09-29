"""Useful functions for app_store parser"""
import os

import aiohttp
import bs4.element
import dotenv


dotenv.load_dotenv()


PROXY_ENABLED = bool(int(os.environ.get('PROXY_ENABLED', 0)))


def get_text(parent: bs4.element.Tag):
    """Returns tag inner text (text without childs texts)"""
    return ''.join(parent.find_all(string=True, recursive=False)).strip()


async def get_page(url: str,
                   timeout: int | None = None, none_on: int | list[int] = None):
    """Makes GET request to page with proxy (if enabled)
    Args:
        url (str): url to process

        timeout (int): connection max time in seconds

        none_on (int | list): codes which must return None if responded.

    Returns:
        str: Response text
        None: If response code was provided in none_on

    Raises:
          aiohttp.ClientTimeout: if server not responded
          AttributeError: if text not provided
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
    """Makes POST request to page with proxy (if enabled)
    Args:
        url (str): url to process.
        data (Any): data to send.

    Returns:
        str: Response text

    Raises:
          aiohttp.ClientTimeout: if server not responded
          AttributeError: if text in response is not provided
    """
    async with aiohttp.ClientSession(trust_env=PROXY_ENABLED) as session:
        async with session.post(url, data=data, headers={
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8'
        }) as resp:
            res = await resp.text()
            return res


async def post(url, data):
    async with aiohttp.ClientSession(trust_env=PROXY_ENABLED) as session:
        async with session.post(url, json=data, headers={
            'Content-Type': 'application/json'
        }) as resp:
            if resp.status == 200:
                return await resp.json()
            else:
                return None
