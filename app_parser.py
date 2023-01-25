import json
from typing import Any

import aiohttp

import formats
import regexes
import specs


def parse_dom(dom: str, app_id: str, url: str) -> dict[str, Any]:
    matches = regexes.SCRIPT.findall(dom)
    dataset = {}
    for match in matches:
        key_match = regexes.KEY.findall(match)
        value_match = regexes.VALUE.findall(match)

        if key_match and value_match:
            key = key_match[0]
            value = json.loads(value_match[0])

            dataset[key] = value

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
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(connect=10)) as session:
            async with session.get(url) as resp:
                if resp.status == 404:
                    return None
                res = await resp.text()
        if not res:
            return None
        print('got app', app_id)
        return parse_dom(res, app_id, url)
    except aiohttp.ClientError:
        return None
