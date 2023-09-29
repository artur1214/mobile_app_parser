"""Module for parse play market"""
import csv
import itertools
import json
import pprint
import random
import re
from io import StringIO
from typing import Any, TextIO

import asyncio
from urllib.parse import quote, urlparse, parse_qs, urlencode, urlunparse

import cytoolz
from _jsonnet import evaluate_snippet

try:
    from typing import IO
except (ImportError, ModuleNotFoundError):  # For compatibility with old python
    from typing.io import IO

try:
    from . import formats, utils, specs, regexes, permissions
    from .app_parser import get_app_info
except ImportError:
    import formats, utils, specs, regexes, permissions
    from app_parser import get_app_info

PLAY_STORE_BASE_URL = "https://play.google.com"


def more_result_section(dataset):
    try:
        return specs.nested_lookup(dataset, ['ds:4', 0, 1])
    except (Exception,) as _exc:
        return None


async def create_link(query_string, lang: str = "en",
                      country: str = "us"):
    query = quote(query_string)
    url = formats.search_results.build(query, lang, country)
    return url


def parse_service_data(dom):
    matches = regexes.SERVICE_DATA.findall(dom)
    if not matches:
        return {}
    data = matches[0]
    try:
        res = re.search(r"{'ds:[\s\S]*}}", data)
        parsed = evaluate_snippet('snippet', res.group())
        return parsed
    except (Exception,) as _exc:
        return {}


def process_data(data: str):
    try:
        data = data[5:]
        data = json.loads(data)
        data = json.loads(data[0][2])
    except TypeError:
        return None
    return data


async def check_finished(saved_apps: list[dict[str, Any]] | None,
                         token=None, apps_count: int = 100, **opts):
    if not token:
        return saved_apps or []
    default_opts = {
        'term': 'sport',
        'lang': 'en',
        'country': 'us',
    }
    for opt in opts:
        default_opts[opt] = opts[opt]
    opts = default_opts

    body = f'f.req=%5B%5B%5B%22qnKhOb%22%2C%22%5B%5B' \
           f'null%2C%5B%5B10%2C%5B10%2C{apps_count}%5D%5D%2Ctrue%2Cnull' \
           f'%2C%5B96%2C27%2C4%2C8%2C57%2C30%2C110%2C79%2C11%2C16%2C49%2C1' \
           f'%2C3%2C9%2C12%2C104%2C55%2C56%2C51%2C10%2C34%2C77%5D%5D%2Cnul' \
           f'l%2C%5C%22{token}%5C%22%5D%5D%22%2Cnull%2C%22gen' \
           f'eric%22%5D%5D%5D'
    url = f'{PLAY_STORE_BASE_URL}/_/PlayStoreUi/data/batchexecute?' \
          f'rpcids=qnKhOb&f.sid=-697906427155521722&bl=boq_playuiserver' \
          f'_20190903.08_p0&hl={opts.get("lang")}&gl={opts.get("country")}' \
          f'&authuser&soc-app=121&soc-platform=1&soc-device=1&_reqid=1065213'
    res = await utils.post_page(url, body)
    data = process_data(res)
    if not data:
        return saved_apps or []
    return await process_pages(data, saved_apps)


MAPPINGS = {
    'title': [2],
    'appId': [12, 0],
    'url': {
        'path': [9, 4, 2],
        'fun': lambda url: PLAY_STORE_BASE_URL + url
    },
    'icon': [1, 1, 0, 3, 2],
    'developer': [4, 0, 0, 0],
    'developerId': {
        'path': [4, 0, 0, 1, 4, 2],
        'fun': lambda link: link.split('?id=')[1]
    },
    'price_text': {
        'path': [7, 0, 3, 2, 1, 0, 2],
        'fun': lambda price: 'FREE' if price is None else price
    },
    'currency': [7, 0, 3, 2, 1, 0, 1],
    'price': {
        'path': [7, 0, 3, 2, 1, 0, 2],
        'fun': lambda price: 0 if price is None else float(
            re.search(r"([0-9.,]+)", price).group())
    },
    'summary': [4, 1, 1, 1, 1],
    'scoreText': [6, 0, 2, 1, 0],
    'score': [6, 0, 2, 1, 1]
}


def extract_app_list(data):
    data = specs.nested_lookup(data, [0, 0, 0])
    res = []
    if not data:
        return []
    for el in data:
        res.append(utils.extract_data_from_app(el, MAPPINGS))
    return res


async def process_pages(data, saved_apps):
    app_list = extract_app_list(data)
    token = specs.nested_lookup(data, [0, 0, 7], True)
    return await check_finished([*saved_apps, *app_list], token)


def save_json_to_csv(data: list[dict[str, Any]], file: TextIO):
    """Saves json data into csv file or stream

        Args:
            data (list[dict]): list with data to save
            file (TextIO): IO object (file, tokenstream, etc.)
             with 'write' method
    """
    try:
        if len(data) == 0:
            return {
                'ok': True,
                'csv': '',
                'data': data
            }
        output = csv.writer(file)
        output.writerow(data[0].keys())  # header row
        for row in data:
            output.writerow(row.values())
        return {
            'ok': True,
            'data': data,
            'csv': file.getvalue()
        }
    except (IndexError, AttributeError) as _exc:
        return {
            'ok': False,
            'data': _exc
        }


async def parse_urls(url: str | list[str], **opts):
    try:
        n_hits = 100

        dom = await utils.get_page(url)
        # service_data = parse_service_data(dom)
        dataset = utils.parse_dataset_dom(dom)
        json.dump(dataset, open('123.json', 'w+'))
        success = False
        res_dataset = dataset
        # different idx for different countries and languages
        for idx in range(len(dataset["ds:4"][0][1])):
            try:
                # json.dump(dataset, open('dataset.json', 'w+'))
                dataset = dataset["ds:4"][0][1][idx][22][0]
                success = True
            except (Exception,) as _exc:
                print('passed', _exc)
                pass
        if not success:
            print('NOT SUCCESSS')
            return []

        n_apps = min(len(dataset), n_hits)
        search_results = []
        for app_idx in range(n_apps):
            app = {}
            for k, spec in specs.ElementSpecs.Searchresult.items():
                content = spec.extract_content(dataset[app_idx])
                app[k] = content
            search_results.append(app)
        more_section = more_result_section(res_dataset)[0]

        token = specs.nested_lookup(more_section, [22, 1, 3, 1], True)
        return await check_finished(search_results, token, opts)
    except Exception as e:
        print('ERRR:', e)
        return []


async def parse_from_url(url: str, stream_to: IO | None = None, **kwargs):
    full_search = kwargs.get('full_search', False)
    prev = []
    codes = COUNTRY_CODES[:200]
    random.shuffle(codes)
    to_process = []
    provided_code = parse_qs(urlparse(url).query).get('gl', ['us', 'ca'])
    parsed_url = urlparse(url)
    url_params = parse_qs(parsed_url.query)
    if 'gl' in url_params:
        url_params.pop('gl')
    url = parsed_url._replace(query=urlencode(url_params, True))
    url = urlunparse(url)
    search_codes = [*IMPORTANT_CODES, *codes[:30]] if full_search else provided_code

    if detail := url.split('details?'):
        if len(detail) > 1:
            url = detail[-1].split('id=')[-1].replace('/', '')
            parsed = [await get_app_info(url)]
            parsed = list(filter(None, parsed))
            return parsed
    for code in search_codes:
        to_process.append(parse_urls(url + f'&gl={code}', country=code))
    prev = await asyncio.gather(*to_process)
    prev = list(itertools.chain(*prev))

    print(f'found {len(prev)} elements to parse')
    coroutines = []
    prev = list(cytoolz.unique(prev, lambda f: f.get('appId')))

    print(f'found FILTERED {len(prev)} elements to parse')
    for app in prev:
        coroutines.append(get_app_info(app.get('appId')))
    parsed = await asyncio.gather(*coroutines)
    parsed = list(filter(None, parsed))
    # print(successfully parsed {len(parsed)} elements')

    return parsed


__all__ = ('app_parser', 'parse_from_url', 'utils', 'datasafety', 'specs',
           'formats', 'regexes', 'save_json_to_csv', 'permissions')
COUNTRY_CODES = [
    "af",
    "al",
    "dz",
    "as",
    "ad",
    "ao",
    "ai",
    "aq",
    "ag",
    "ar",
    "am",
    "aw",
    "au",
    "at",
    "az",
    "bs",
    "bh",
    "bd",
    "bb",
    "by",
    "be",
    "bz",
    "bj",
    "bm",
    "bt",
    "bo",
    "ba",
    "bw",
    "bv",
    "br",
    "io",
    "bn",
    "bg",
    "bf",
    "bi",
    "kh",
    "cm",
    "ca",
    "cv",
    "ky",
    "cf",
    "td",
    "cl",
    "cn",
    "cx",
    "cc",
    "co",
    "km",
    "cg",
    "cd",
    "ck",
    "cr",
    "ci",
    "hr",
    "cu",
    "cy",
    "cz",
    "dk",
    "dj",
    "dm",
    "do",
    "ec",
    "eg",
    "sv",
    "gq",
    "er",
    "ee",
    "et",
    "fk",
    "fo",
    "fj",
    "fi",
    "fr",
    "gf",
    "pf",
    "tf",
    "ga",
    "gm",
    "ge",
    "de",
    "gh",
    "gi",
    "gr",
    "gl",
    "gd",
    "gp",
    "gu",
    "gt",
    "gn",
    "gw",
    "gy",
    "ht",
    "hm",
    "va",
    "hn",
    "hk",
    "hu",
    "is",
    "in",
    "id",
    "ir",
    "iq",
    "ie",
    "il",
    "it",
    "jm",
    "jp",
    "jo",
    "kz",
    "ke",
    "ki",
    "kp",
    "kr",
    "kw",
    "kg",
    "la",
    "lv",
    "lb",
    "ls",
    "lr",
    "ly",
    "li",
    "lt",
    "lu",
    "mo",
    "mk",
    "mg",
    "mw",
    "my",
    "mv",
    "ml",
    "mt",
    "mh",
    "mq",
    "mr",
    "mu",
    "yt",
    "mx",
    "fm",
    "md",
    "mc",
    "mn",
    "ms",
    "ma",
    "mz",
    "mm",
    "na",
    "nr",
    "np",
    "nl",
    "an",
    "nc",
    "nz",
    "ni",
    "ne",
    "ng",
    "nu",
    "nf",
    "mp",
    "no",
    "om",
    "pk",
    "pw",
    "ps",
    "pa",
    "pg",
    "py",
    "pe",
    "ph",
    "pn",
    "pl",
    "pt",
    "pr",
    "qa",
    "re",
    "ro",
    "ru",
    "rw",
    "sh",
    "kn",
    "lc",
    "pm",
    "vc",
    "ws",
    "sm",
    "st",
    "sa",
    "sn",
    "cs",
    "sc",
    "sl",
    "sg",
    "sk",
    "si",
    "sb",
    "so",
    "za",
    "gs",
    "es",
    "lk",
    "sd",
    "sr",
    "sj",
    "sz",
    "se",
    "ch",
    "sy",
    "tw",
    "tj",
    "tz",
    "th",
    "tl",
    "tg",
    "tk",
    "to",
    "tt",
    "tn",
    "tr",
    "tm",
    "tc",
    "tv",
    "ug",
    "ua",
    "ae",
    "uk",
    "us",
    "um",
    "uy",
    "uz",
    "vu",
    "ve",
    "vn",
    "vg",
    "vi",
    "wf",
    "eh",
    "ye",
    "zm",
    "zw"
]
IMPORTANT_CODES = [
    'us',
    'ru',
    'cn',
    'ca',
    'jp',
    'af',
    'de',
    'gb',
    'cs',
    'tr'
]
if __name__ == '__main__':
    async def main():
        res = await parse_from_url(
            'https://play.google.com/store/search?q=browser&c=apps')
        save_json_to_csv(res, open('main_test.csv', 'w+'))
        json.dump(res, open('main_test.json', 'w+'))


    asyncio.run(main())
