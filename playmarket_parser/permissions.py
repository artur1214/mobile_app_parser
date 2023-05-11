import itertools
import json
from typing import Dict, List

from playmarket_parser.specs import ElementSpecs
from playmarket_parser import regexes
from playmarket_parser import utils

PLAY_STORE_BASE_URL = "https://play.google.com"

PERMISSIONS_URL = (
    "{}/_/PlayStoreUi/data/batchexecute?" 
    "hl={{lang}}&gl={{country}}"
).format(PLAY_STORE_BASE_URL)


INTERESTED_PERMISSIONS = [ p.strip() for p in """download files without notification
read sync statistics
receive data from Internet
control vibration
full network access
reorder running apps
change network connectivity
control Near Field Communication
create accounts and set passwords
install shortcuts
access Bluetooth settings
change your audio settings
read sync settings
use accounts on the device
pair with Bluetooth devices
view network connections
prevent device from sleeping
toggle sync on and off
run at startup""".splitlines() if p]


PAYLOAD_FORMAT_FOR_PERMISSION = "f.req=" \
                                "%5B%5B%5B%22xdSrCf%22%2C%22%5B%5B" \
                                "null%2C%5B%5C%22{app_id}" \
                                "%5C%22%2C7%5D%2C%5B%5D%5D%5D%22%2C" \
                                "null%2C%221%22%5D%5D%5D"


async def get_permissions(app_id: str, lang: str = "en",
                          country: str = "us") -> Dict[str, list]:
    """Retrieves app's permissions by app_id

    """
    dom = await utils.post_page(
        PERMISSIONS_URL.format(lang=lang, country=country),
        PAYLOAD_FORMAT_FOR_PERMISSION.format(app_id=app_id)
    )

    matches = json.loads(regexes.PERMISSIONS.findall(dom)[0])
    container = json.loads(matches[0][2])

    result = {}

    for permission_items in container:
        if isinstance(permission_items, list):
            if len(permission_items[0]) == 2:
                # rearrange layout to fit ElementSpecs
                permission_items = [["Uncategorized", None, permission_items,
                                     None]]

            for permission in permission_items:
                if permission:
                    result[
                        ElementSpecs.Permission_Type.extract_content(permission)
                    ] = ElementSpecs.Permission_List.extract_content(permission)

    return result


def get_interested_permissions(permissions: Dict[str, list]) -> List[str]:
    """Get permissions, which we are interested in"""
    texts: List[str] = list(itertools.chain(*list(permissions.values())))
    interested_permissions = []
    for perm_text in INTERESTED_PERMISSIONS:
        if perm_text.strip() in texts:
            interested_permissions.append(perm_text.strip())
    return interested_permissions
