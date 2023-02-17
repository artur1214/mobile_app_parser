import asyncio
import json
import pprint

from appstore_parser import utils
import bs4
import dataclasses

PRIVACY_DETAILS = 'https://amp-api.apps.apple.com/v1/catalog/us/apps/{}?l=en-us&platform=web&fields=privacyDetails'


@dataclasses.dataclass
class App:
    title: str
    descriptionHTML: str
    description: str
    summary: str
    score: float
    ratings: str
    price: str
    free: bool
    currency: str | None
    developer: str
    developer_id: int
    privacy_policy: str


def parse_app_info(page: str):
    soup = bs4.BeautifulSoup(page, 'lxml')
    title = soup.find('h1', class_='product-header__title app-header__title')
    if title:
        title = utils.get_text(title)
    descriptionHTML = soup.find('div', class_='section__description')
    if not descriptionHTML and not title:
        return None
    descriptionHTML = descriptionHTML and descriptionHTML.find('div', class_='l-row')
    description = descriptionHTML and descriptionHTML.text

    summary = soup.find(
        'h2',
        class_='product-header__subtitle app-header__subtitle'
    ).text.strip()
    score = float(soup.find(
        'span',
        class_='we-customer-ratings__averages__display'
    ).text.strip())
    ratings = soup.find(
        'div',
        class_='we-customer-ratings__count small-hide medium-show'
    ).text.replace('Ratings', '').strip()
    price = soup.find(
        'li',
        class_='inline-list__item inline-list__item-'
               '-bulleted app-header__list__item--price'
    ).text.strip()
    free = bool((not price) or (price.lower() == 'free'))
    currency = 'USD' if price and ('$' in price) else None
    developer_link = soup.find(
        'h2',
        class_='product-header__identity app-header__identity'
    ).find('a')
    developer = developer_link.text.strip()
    developer_id = int(
        json.loads(developer_link.get('data-metrics-click'))['targetId'])
    privacy_link = soup.find('section', class_='app-privacy').find('a').get(
        'href')
    return {
        'title': title,
        'description': description,
        'descriptionHTML': str(descriptionHTML),
        'summary': summary,
        'score': score,
        'ratings': ratings,
        'price': price,
        'free': free,
        'currency': currency,
        'developer': developer,
        'developer_id': developer_id,
        'privacy_policy': privacy_link
    }


async def get_app_info(url: str, reset=0):
    res = await utils.get_page(url)
    res = parse_app_info(res)
    if res is None:
        if reset > 3:
            return None
        res = await get_app_info(url, reset+1)
    return res


if __name__ == '__main__':
    async def main():
        pass

    asyncio.run(main())
