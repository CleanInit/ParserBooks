from bs4 import BeautifulSoup
import re
import json
import os
import shutil
import aiofiles

class HtmlToJsonParser:
    def __init__(self, html_content: str, url: str):
        self.html_content = html_content

        self.soup = BeautifulSoup(html_content, "lxml")
        self.RATING_MAP = {
            "Zero": 0,
            "One": 1,
            "Two": 2,
            "Three": 3,
            "Four": 4,
            "Five": 5
        }

        self.result_data = {
            "title": None,
            "book rating": None,
            "book type": None,
            "description": None,
            "price (excl. tax)": None,
            "price (incl. tax)": None,
            "tax": None,
            "available": None,
            "number of reviews": None,
            "upc": None,
            "book_url": url
            }

    async def _get_other(self):
        price_table = self.soup.select_one("table.table.table-striped")

        if not price_table:
            return 0, 0

        excl_price, incl_price, tax, available, number_of_reviews, upc = None, None, None, None, None, None

        rows = price_table.find_all("tr")
        for row in rows:
            header = row.find("th").get_text(strip=True).lower()
            value = row.find("td").get_text(strip=True)
            if "upc" == header:
                upc = value
            elif "price (excl. tax)" == header:
                excl_price = value
            elif "price (incl. tax)" == header:
                incl_price = value
            elif "tax" == header:
                tax = value
            elif header == "availability":
                value = re.match(r"In stock \((\d+) available\)", value)
                available = value.group(1)
            elif header == "number of reviews":
                number_of_reviews = value
        return excl_price, incl_price, tax, available, number_of_reviews, upc

        return 1, 1

    async def _get_description(self):
        description = self.soup.select("#content_inner article p")
        return description[-1].get_text(strip=True) if description else None

    async def _get_type(self):
        links = self.soup.select("ul.breadcrumb li a")
        return links[-1].get_text(strip=True) if links else None

    async def _get_title(self):
        title = self.soup.find("h1").get_text(strip=True)
        return title

    async def _get_rating(self):
        rating_tag = self.soup.find("p", class_="star-rating")
        if rating_tag:
            classes = rating_tag.get("class", [])
            for cls in classes:
                if cls in self.RATING_MAP:
                    return self.RATING_MAP[cls]

    async def _save_json(self, currently_path: str):

        json_data = json.dumps(self.result_data, ensure_ascii=False, indent=4)

        if not os.path.exists(currently_path):
            async with aiofiles.open(currently_path, 'w+', encoding='utf-8') as file:
                await file.write(json_data)

    async def _saving_to_json(self, folder_json_save: str = "jsons"):
        file_name = self.result_data["title"]
        book_type = self.result_data["book type"]
        currently_folder_path = os.path.join(folder_json_save, book_type)
        os.makedirs(currently_folder_path, exist_ok=True)
        try:
            currently_path = os.path.join(currently_folder_path, f"{file_name}.json")
            await self._save_json(currently_path=currently_path)
        except FileNotFoundError:
            currently_path = os.path.join(currently_folder_path, f"{file_name.replace('/', '_').replace(':', '-')}.json")
            await self._save_json(currently_path=currently_path)

    async def start(self):
        self.result_data["title"] = await self._get_title()
        self.result_data["book rating"] = await self._get_rating()
        self.result_data["book type"] = await self._get_type()
        self.result_data["description"] = await self._get_description()
        excl_price, incl_price, tax, available, number_of_reviews, upc = await self._get_other()

        self.result_data["price (excl. tax)"] = excl_price
        self.result_data["price (incl. tax)"] = incl_price
        self.result_data["tax"] = tax
        self.result_data["available"] = available
        self.result_data["number of reviews"] = number_of_reviews
        self.result_data["upc"] = upc
