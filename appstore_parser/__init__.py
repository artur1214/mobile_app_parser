"""Module for parse app store"""
import asyncio
import csv
import pprint

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
    div = soup.find('div', class_='rf-serp-explore')
    links = div and div.find_all("a", string="View more")
    print(f'found {len(links)} elements to parse.')
    links = [link.get('href') for link in links]
    coroutines = [get_app_info(link) for link in links]
    res = await asyncio.gather(*coroutines)
    return res

if __name__ == '__main__':
    async def main():
        res = await parse('https://apps.apple.com/us/app/minecraft/id479516143')
        print(res)
        #save_json_to_csv(res,)
    asyncio.run(main())
