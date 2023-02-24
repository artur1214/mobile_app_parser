"""Module for parse app store"""
import asyncio
import csv
import json

from appstore_parser.app_parser import get_app_info
from appstore_parser import utils
import bs4
import re

__all__ = ('parse', 'save_json_to_csv', 'get_app_info')


def save_json_to_csv(data: list[dict], file):
    """Saves json data into csv file. or file-like stream

    Args:
        data (list[dict]): list with data to save
        file (TextIO): IO object (file, tokenstream, etc.)
          with 'write' method

    """
    output = csv.writer(file)
    output.writerow(data[0].keys())  # header row
    for row in data:
        output.writerow(row.values())


async def parse(url: str):
    if re.search(r'app/.*/id([0-9]+)', url):
        res = [await get_app_info(url)]
    elif re.search(r'search/.*', url):
        res = await parse_search_link(url)
    else:
        raise ValueError(url + ' is not valid url to parse.')
    return list(filter(None, res))


async def parse_search_link(url: str):
    page = await utils.get_page(url)
    soup = bs4.BeautifulSoup(page, 'lxml')
    links = await get_app_links(soup, url)
    coroutines = [get_app_info(link) for link in links]
    return await asyncio.gather(*coroutines)


async def get_app_links(page, url) -> list:
    links = get_links_from_usual(page) if not is_react(page) \
        else await get_links_from_react(url)
    print(f'found {len(links)} elements to parse.')

    return links


def is_react(page) -> bool:
    return bool(page.find('div', id='react-app'))


def get_links_from_usual(page) -> list:
    links = page.find_all('a', href=\
        re.compile(r'https://apps\.apple\.com/.*/app/.*/id\d+'))

    return list() if not links \
        else [link['href'] for link in links]


async def get_links_from_react(url) -> list:
    data = await utils.post(
        'https://www.apple.com/search-assets/searchlight/search',
        {
          'locale': get_locale(url),
          'page': '0',
          'query': get_query(url),
          'requestedService': '',
          'resultPerPage': '30',
          'selectedService': '',
          'src': 'aml_serp'
        }
    )

    if not data:
        return list()

    if 'results' not in data:
        return list()

    right_index = 0

    for i, res in enumerate(data['results']):
        if res['sectionName'] == 'exploreCurated':
            right_index = i
            break

    if 'sectionResults' not in data['results'][right_index]:
        return list()

    links = []

    for res in data['results'][right_index]['sectionResults']:
        if 'navLinks' not in res:
            continue

        if 'link' not in res['navLinks'][0]:
            continue

        links.append(res['navLinks'][0]['link'])

    return links


def get_locale(url):
    locale = 'en_US' # fallback locale
    try:
        with open('appstore_parser/react-locales.json') as locales:
            locales = locales.read()
            locales = json.loads(locales)
            res = re.match(r'https://www.apple.com/([\w\-]{2,5})/.*', url)

            return locales[res.group(1)]
    except Exception:
        return locale


def get_query(url):
    res = re.match(r'https://www.apple.com/\w+/search/([^?]+)(\?.+)?', url)

    return res.group(1)


if __name__ == '__main__':
    async def main():
        res = await parse('https://apps.apple.com/us/app/minecraft/id479516143')
        print(res)
        #save_json_to_csv(res,)
    asyncio.run(main())
