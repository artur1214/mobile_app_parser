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

    @aiohttp_jinja2.template('index.html')
    async def get(self):
        return {
            'current_host': f'{self.request.scheme}://{self.request.host}'
        }

    async def post(self):
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
                save_json_to_csv(res, stream)
                return web.Response(text=stream.getvalue())
                # return web.json_response(res)
            except Exception as e:
                print('error!', e)
                return web.Response(text=str(e))


app = web.Application()

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))
app.add_routes(routes)


if __name__ == '__main__':
    web.run_app(app)
    # url = 'https://play.google.com/store/search?q=minecraft&c=apps'
    # asyncio.run(parse_from_url(url))
