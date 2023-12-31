"""Code to parse single app info from appstore"""

import asyncio
import json

from appstore_parser import utils
import bs4
import dataclasses
from price_parser import Price

PRIVACY_DETAILS = 'https://amp-api.apps.apple.com/v1/catalog/us/apps/' \
                  '{}?l=en-us&platform=web&fields=privacyDetails'


@dataclasses.dataclass
class App:
    """Class to serialize App dict

    This class must represent dict with parsed app info
    """
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
    """Parse single app info from HTML dom.

    Args:
        page (str): page HTML string.

    Returns:
        dict | None: parsed app info or None
          if provided HTML doesn't contain valid app info.

    """
    soup = bs4.BeautifulSoup(page, 'lxml')
    title = soup.find('h1', class_='product-header__title app-header__title')
    if title:
        title = utils.get_text(title)
    description_html = soup.find('div', class_='section__description')
    if not description_html and not title:
        return
    description_html = description_html and description_html.find(
        'div', class_='l-row')
    description = description_html and description_html.text
    summary = soup.find(
        'h2',
        class_='product-header__subtitle app-header__subtitle'
    )
    summary = summary and summary.text and summary.text.strip()
    score = soup.find(
        'span',
        class_='we-customer-ratings__averages__display'
    )
    score = score and score.text and float(score.text.replace(',', '.').strip())
    ratings = soup.find(
        'div',
        class_='we-customer-ratings__count small-hide medium-show'
    )
    ratings = ratings and ratings.text and \
              ratings.text.replace('Ratings', '').strip()
    price = soup.find(
        'li',
        class_='inline-list__item inline-list__item-'
               '-bulleted app-header__list__item--price'
    )
    price = price and price.text and Price.fromstring(price.text.strip())
    currency = price.currency
    price = price.amount_float
    free = bool((not price) or (price == 0))
    developer_link = soup.find(
        'h2',
        class_='product-header__identity app-header__identity'
    ).find('a')
    developer = developer_link and developer_link.text and \
                developer_link.text.strip()
    developer_id = None
    if developer_link:
        developer_id = int(json.loads(
            developer_link.get('data-metrics-click'))['targetId'])
    privacy_link = soup.find('section', class_='app-privacy').find('a')
    privacy_link = privacy_link and privacy_link.get('href')
    return {
        'title': title,
        'description': description,
        'descriptionHTML': str(description_html),
        'summary': summary,
        'score': score,
        'ratings': ratings,
        'price': price or 0,
        'free': free,
        'currency': currency,
        'developer': developer,
        'developer_id': developer_id,
        'privacy_policy': privacy_link
    }


async def get_app_info(url: str, reset=0):
    """Parse single app info from url. And makes resets.

    Appstore sometimes responses with not valid HTML response
      (instead gives `loading` page etc.). So, we

    Args:
        url (str): Url to parse from
        reset (int): Field, used only in recursion.
          If function retries get url data 4 times and it's not succeed
          None will be returned

    Returns:
        dict | None: parsed app info or None
          if it's unable to get data from provided url

    """
    res = await utils.get_page(url)
    res = parse_app_info(res)
    if res is None:
        if reset > 3:
            return None
        await asyncio.sleep(5)
        res = await get_app_info(url, reset + 1)
    return res


if __name__ == '__main__':
    async def main():
        pass


    asyncio.run(main())
