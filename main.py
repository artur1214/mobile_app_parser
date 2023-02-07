import io

import aiohttp_jinja2
import jinja2
from aiohttp import web

from playmarket_parser import parse_from_url, save_json_to_csv

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
                res = await parse_from_url(link)
                stream = io.StringIO()
                save_json_to_csv(res, stream)
                return web.Response(text=stream.getvalue())
                # return web.json_response(res)
            except Exception as e:
                return web.Response(text=str(e))


app = web.Application()

aiohttp_jinja2.setup(app, loader=jinja2.FileSystemLoader('./templates'))
app.add_routes(routes)


if __name__ == '__main__':
    web.run_app(app)
    # url = 'https://play.google.com/store/search?q=minecraft&c=apps'
    # asyncio.run(parse_from_url(url))
