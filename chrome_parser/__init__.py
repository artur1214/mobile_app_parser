import asyncio

import utils
__all__ = ('utils',)


async def parse_search(url: str):
    page = await utils.get_page(url)
    print(page)
    with open('main.html', 'w+', encoding="utf-8") as f:
        f.write(page)


async def parse(url: str):
    return await parse_search(url)

if __name__ == '__main__':
    async def main():
        res = await parse('https://chrome.google.com/webstore/search/some%20data')


    asyncio.run(main())