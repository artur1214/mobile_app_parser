"""Module with functions to parse one single app"""
import asyncio
from typing import Any

import aiohttp

from playmarket_parser import formats
from playmarket_parser import specs
from playmarket_parser import utils
from playmarket_parser import datasafety
from playmarket_parser import permissions


def parse_dom(dom: str, app_id: str, url: str) -> dict[str, Any]:
    dataset = utils.parse_dataset_dom(dom)
    result = {}

    for k, spec in specs.ElementSpecs.Detail.items():
        if isinstance(spec, list):
            for sub_spec in spec:
                content = sub_spec.extract_content(dataset)

                if content is not None:
                    result[k] = content
                    break
        else:
            content = spec.extract_content(dataset)

            result[k] = content

    result["appId"] = app_id
    result["url"] = url

    return result


async def get_app_info(app_id: str, lang: str = "en", country: str = "us"):
    url = formats.detail.build(app_id, lang, country)
    try:
        res = await utils.get_page(url, 10, 404)
        if not res:
            return None
        res = parse_dom(res, app_id, url)
        res['datasafety'] = await datasafety.get_app_safety_data(app_id, lang)
        perms = await permissions.get_permissions(app_id, lang, country)
        res['permissionsJson'] = perms
        res['interestedPerms'] = ';\n'.join(
            permissions.get_interested_permissions(perms)
        )
        return res
    except aiohttp.ClientError:
        return None

