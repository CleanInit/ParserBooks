from bs4 import BeautifulSoup
import re
import aiohttp
from utils.htmlProcess import HtmlToJsonParser
import asyncio

class parserBook:
    def __init__(self):
        self.base_url = "https://books.toscrape.com/catalogue/page-{page}.html"
        self.catalog_url = "https://books.toscrape.com/catalogue/"
        self.url_data = []
        self.html_content = None
    
    async def _get_count_page(self, html_content : str = "") -> tuple[int, int]:
        soup = BeautifulSoup(html_content, "lxml")
        status_page_parsing = soup.find("li", class_="current").text.strip()
        match = re.search(r"Page (\d+) of (\d+)", status_page_parsing)
        if match:
            page_current = int(match.group(1))                    
            page_total = int(match.group(2))
            return page_current, page_total
        return 1, 1

    async def _fetch_url(self, url, session):
        async with session.get(url) as response:
            response.raise_for_status()
            return await response.text()

    async def _fetch_page(self, session, page_number: int):
        url = self.base_url.format(page=page_number)
        self.html_content = await self._fetch_url(url=url, session=session)

    async def _parse_books(self):
        soup = BeautifulSoup(self.html_content, 'lxml')

        for book in soup.find_all("li", class_="col-xs-6 col-sm-4 col-md-3 col-lg-3"):
            currently_url = f"{self.catalog_url}{book.find("a")["href"]}"
            self.url_data.append(currently_url)

    async def _process_html(self, url: str, x: int, session: aiohttp.ClientSession, count_urls: int):
        print(f"{x}/{count_urls}")
        html_content = await self._fetch_url(url=url, session=session)
        html = HtmlToJsonParser(html_content=html_content ,url=url)

        await html.start()
        await html._saving_to_json()
  
    async def _parsing_pages_books(self, session: aiohttp.ClientSession, page_number: int, page_total:int):
        print(f"{page_number}/{page_total}")
        await self._fetch_page(session=session, page_number=page_number)
        await self._parse_books()
