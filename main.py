import json
import threading

import aiohttp as aiohttp

import asyncio
from urllib.parse import quote

import formats
import regexes
import specs
from app_parser import get_app_info

PLAY_STORE_BASE_URL = "https://play.google.com"


async def create_link(query_string, n_hits: int = 30, lang: str = "en",
                      country: str = "us"):
    query = quote(query_string)
    url = formats.search_results.build(query, lang, country)
    return url


async def get_dom(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            #print(resp.status)
            # if resp.status == 404:
            #     return await get_dom()
            res = await resp.text()
            #print(res)
            return res


async def parse_urls(url: str | list[str]):
    n_hits = 1000

    dom = await get_dom(url)
    matches = regexes.SCRIPT.findall(dom)
    dataset = {}
    for match in matches:
        key_match = regexes.KEY.findall(match)
        value_match = regexes.VALUE.findall(match)

        if key_match and value_match:
            key = key_match[0]
            value = json.loads(value_match[0])
            dataset[key] = value
    success = False
    # different idx for different countries and languages
    for idx in range(len(dataset["ds:4"][0][1])):
        try:
            dataset = dataset["ds:4"][0][1][idx][22][0]
            success = True
        except Exception:
            pass
    if not success:
        return []

    n_apps = min(len(dataset), n_hits)
    search_results = []
    for app_idx in range(n_apps):
        app = {}
        for k, spec in specs.ElementSpecs.Searchresult.items():
            content = spec.extract_content(dataset[app_idx])
            app[k] = content
        search_results.append(app)
    return search_results


async def main():
    res = await parse_urls('https://play.google.com/store/search?q=sport&c=apps')
    app_results = []
    proceed = []
    print(f'finded {len(res)} elements to parse')
    async def load_app_info(_app):
        app_info = await get_app_info(_app.get('appId'))
        if app_info:
            app_results.append(app_info)
        else:
            print('error on parse' + (_app.get('appId')))
        proceed.append(1)
    for app in res:
        threading.Thread(target=asyncio.run, args=(load_app_info(app),)).start()

    while 1:
        if len(proceed) == len(res):
            json.dump(app_results, open('main.json', 'w+'))
            print(f'successfully parsed {len(app_results)} elements')
            return app_results
        #print(len(proceed), len(res))
        await asyncio.sleep(0.2)

asyncio.run(main())
