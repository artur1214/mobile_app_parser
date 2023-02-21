"""Module for parse chrome extensions webstore"""
import asyncio
import json
import urllib.parse
from chrome_parser import app_parser
from chrome_parser import utils

__all__ = ('utils', 'app_parser', 'parse')

SEARCH_TERM_URL = (
    "https://chrome.google.com/webstore/ajax/"
    "item?hl={}&gl={}"
    "&pv=20210820&mce="
    "atf%2Cpii%2Crtr%2Crlb%2Cgtc"
    "%2Chcn%2Csvp%2Cwtd%2Chap%2Cnma%"
    "2Cdpb%2Cutb%2Chbh%2Cebo%2Chqb%2Cif"
    "m%2Cndd%2Cntd%2Coiu%2Cuga%2Cc3d%2Cncr%"
    "2Chns%2Cctm%2Cac%2Chot%2Chfi%2Cdtp%2Cmac%"
    "2Cbga%2Cfcf%2Chsp%2Crma&count=112&"
    "searchTerm={}&sortBy=0"
    "&rt=j"
    "&category=extensions"
    "&container=CHROME"
)


MAPPINGS = {
    'id': [0],
    'title': [1],
    'developer': [2],
    'small_logo': [3],
    'big_logo': [4],
    'very_big_logo': [5],
    'summary': [6],
    'type': [9],
    'text_type': [10],
    'score': [12],
    'reviews': [22],
    'installs': [23],
    'details': {
        'path': [46],
        'fun': lambda url: 'https://chrome.google.com' + url
    },
    'developer_site': [81]
}


async def get_items_from_search_term(search_term: str, lang='en', country='US'):
    """parses all extensions by provided search term

    Parses data from Google's batch request api. Batch request api is very
     complex.
     See https://kovatch.medium.com/deciphering-google-batchexecute-74991e4e446c
     if you want get some useful information.

    Args:
        search_term (str): term from search string
        lang (str): language, which we provide into google api
        country(str) lang attribute analog but with country code

    Returns:
        list[dict]: list with parsed info


    """
    resp = await utils.post_page(
        SEARCH_TERM_URL.format(lang, country, search_term),
        data='login=&'
    )
    data = resp[5:]

    data = json.loads(data)
    data = utils.nested_lookup(data, [0, 1, 1])
    res = []
    for item in data:
        res.append(utils.extract_data_from_app(item, MAPPINGS))
    return res


async def parse_search(url: str, lang='en', country='US'):
    """Parses apps info from provided search url

    Gets url like https://play.google.com/store/search?q=minecraft&c=apps
      parses all app ids from that page, then parses all info from pages with
      apps infos (by app id)

    Args:
        url (str): url from which we will parse info.
        lang (str): language code, which we provide into google api
        country(str) lang attribute analog but with country code

    Returns:
        list[dict]: list with parsed info
    """
    term = url.split('?')[0].split('/')[-1]
    apps = await get_items_from_search_term(term, lang, country)
    res = []
    for app in apps:
        url = app.get('id')
        res.append(app_parser.parse_app(url))
    res = await asyncio.gather(*res)
    return res


async def parse(url: str):
    """Main chrome parse function

    wrapper for parse_search or parse_app function calls. Must be used always
      instead of more low level functions. Gets url, returns result. Easy :).

    """
    query = urllib.parse.urlparse(url).query
    query = urllib.parse.parse_qs(query)
    lang = query.get('hl', [])
    if lang:
        lang = lang[0] or 'en'
    country = query.get('hl', [])
    if country:
        country = country[0] or 'US'

    if '/search/' in url:
        res = await parse_search(url, lang, country)
    else:
        _id = url.split('?')[0].split('/')[-1]
        res = [await app_parser.parse_app(_id, lang, country)]
    return res


if __name__ == '__main__':
    async def main():
        res = await parse(
            'https://chrome.google.com/webstore/search/some%20data')

    asyncio.run(main())
