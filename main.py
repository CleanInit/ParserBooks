import aiohttp
import asyncio
import logging
from utils.parserBook import parserBook
          
async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://books.toscrape.com/catalogue/page-1.html") as response:
            response.raise_for_status()
            html_content = await response.text()
            parser = parserBook()
            page_current, page_total = await parser._get_count_page(html_content=html_content)

            tasks = [parser._parsing_pages_books(session=session, page_number=page_number, page_total=page_total) for page_number in range(1, page_total + 1)]
            await asyncio.gather(*tasks)

            tasks = [parser._process_html(url=url, x=x, session=session, count_urls=len(parser.url_data)) for x, url in enumerate(parser.url_data, start=1)]
            await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())