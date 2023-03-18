import asyncio
import json
import pprint

from chrome_parser import utils

MAPPINGS = {
    'id': [0,0],
    'title': [0, 1],
    'developer': [0, 2],
    'small_logo': [0, 3],
    'big_logo': [0, 4],
    'very_big_logo': [0, 5],
    'summary': [0, 6],
    'type': [0, 9],
    'text_type': [0, 10],
    'score': [0, 12],
    'reviews': [0, 22],
    'installs': [0, 23],
    'details': {
        'path': [0, 46],
        'fun': lambda url: 'https://chrome.google.com' + url
    },
    'developer_site': [0, 81],
    'description': [1],
    'current_version': [6],
    'updated_at': [7],
    'languages': [8],
    'size': [25],
    'privacy_url': [35, 2],
    'developer_email': [35, 0],
    'developer address': [35, 1],
    'privacy_types': {
        'path': [39],
        'fun': lambda val: ','.join(str(val))
    },
}


async def parse_app(_id: str, lang='en', country='US'):
    res = await utils.post_page(
        'https://chrome.google.com/webstore/ajax/detail?'
        f'hl={lang}&gl={country}'
        '&pv=20210820'
        '&mce=atf%2Cpii%2Crtr%2Crlb%2Cgtc%2Chcn%2Csvp%2Cwtd%2Chap%2Cnma%2Cdpb'
        '%2Cutb%2Chbh%2Cebo%2Chqb%2Cifm%2Cndd%2Cntd%2Coiu%2Cuga%2Cc3d%2Cncr%2'
        'Chns%2Cctm%2Cac%2Chot%2Chsf%2Chfi%2Cdtp%2Cmac%2Cbga%2Cepb%2Cfcf%2Crai%2Crma'
        f'&id={_id}'
        '&container=CHROME'
        '&rt=j',
        data='login=&'
    )
    data = res[5:]
    data = json.loads(data)
    data = utils.nested_lookup(data, [0, 1, 1])
    res = utils.extract_data_from_app(data, MAPPINGS)
    return res




if __name__ == '__main__':
    async def main():
        await parse_app('https://chrome.google.com/webstore/detail/adguard-adblocker/bgnkhhnnamicmpeenaelnjfhikgbkllg?hl=ru&gl=RU')

    asyncio.run(main())