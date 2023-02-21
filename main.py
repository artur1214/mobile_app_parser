"""Frontend server for parser."""

import io
import urllib.parse

import aiohttp_jinja2
import jinja2
from aiohttp import web

from playmarket_parser import parse_from_url, save_json_to_csv
from appstore_parser import parse as parse_apple
from chrome_parser import parse as chrome_parse

routes = web.RouteTableDef()


@routes.view('/')
class IndexView(web.View):
    """Main view class"""
    @aiohttp_jinja2.template('index.html')
    async def get(self):
        """GET request handler"""
        return {
            'current_host': f'{self.request.scheme}://{self.request.host}'
        }

    async def post(self):
        """POST request handler"""
        data = await self.request.post()
        if link := data.get('link'):
            try:
                host = urllib.parse.urlparse(link).netloc
                if 'apple.' in host:
                    res = await parse_apple(link)
                # result = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
                elif 'play.google' in host:
                    res = await parse_from_url(link)
                else:
                    res = await chrome_parse(link)

                stream = io.StringIO()
                res = save_json_to_csv(res, stream)
                print(res)
                return web.json_response(
                    data=res,
                    status=200 if res.get('ok') else 200
                )
                # return web.json_response(res)
            except (ValueError, IndexError) as exc:
                print('error!', exc)
                return web.json_response(
                    data={
                        'ok': False,
                        'data': exc
                    },
                    status=500
                )


def make_app() -> web.Application:
    """Creates app

    This function creates new app instance. We create new Application instance
    on every call because it's needed for tests.

    Returns:
        web.Application

    """

    app = web.Application()

    aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))
    app.add_routes(routes)
    return app


if __name__ == '__main__':
    web.run_app(make_app())
    # url = 'https://play.google.com/store/search?q=minecraft&c=apps'
    # asyncio.run(parse_from_url(url))
