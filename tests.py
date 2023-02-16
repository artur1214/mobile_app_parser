from aiohttp.test_utils import AioHTTPTestCase
from aiohttp import web


class MyAppTestCase(AioHTTPTestCase):

    async def get_application(self):
        """
        Override the get_app method to return your application.
        """
        from main import make_app
        return make_app()

    async def test_page_founded(self):
        async with self.client.request("GET", "/") as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
        self.assertIn("<head>", text)

    async def test_page_not_founded(self):
        async with self.client.request("GET", "/invalid_link") as resp:
            self.assertEqual(resp.status, 404)

    async def test_send_apple(self):
        async with self.client.request("POST", "/", data={
            'link': 'https://apps.apple.com/us/app/minecraft/id479516143'}
                                       ) as resp:
            self.assertEqual(resp.status, 200)
            text = await resp.text()
        self.assertIn("Explore infinite worlds and build everything "
                      "from the simplest of homes to the grandest"
                      " of castles.", text)
        self.assertEqual(200, resp.status)
