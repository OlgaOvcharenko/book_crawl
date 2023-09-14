from urllib.request import urlopen
from bs4 import BeautifulSoup
from enum import Enum
import pandas as pd
import re
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


class Rating(Enum):
    Zero = 0
    One = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5


class BookDataScraper():
    expected_cols = [ 
        'url', 'description', 'name', 'rating', 'category', 
        'upc', 'product type', 
        'price (excl. tax)', 'price (incl. tax)', 'tax', 
        'availability', 'number of reviews']
    
    BOOK_SHOP_URL = "http://books.toscrape.com/index.html"
    BOOK_SHOP_BASE_URL = "http://books.toscrape.com"


    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.books_df = pd.DataFrame(columns=self.expected_cols)

    def collect_data(self):
        soup_main = self._get_data_from_url()

        # Get categories and get books for each
        category_link = self._get_all_category_links(soup_main)
        # TODO parallel
        for category, link in category_link.items():
            if self.verbose:
                print(f"Extracting {category} category, collected {self.books_df.shape[0]} items.")

            full_url = self.BOOK_SHOP_BASE_URL + "/" + link
            soup_category = self._get_data_from_url(full_url)
            self._get_items_from_page_markup(soup_category, self.expected_cols, category, full_url)

    def _get_data_from_url(self, url: str = BOOK_SHOP_URL) -> BeautifulSoup:
        """"Extracts data from the given url."""
        if url == '':
            raise TypeError("URL must be non-empty.")
            
        try: 
            page = urlopen(url)
            markup = page.read().decode("utf-8")
            soup = BeautifulSoup(markup=markup, features="html.parser")
            return soup
        except Exception as e:
            print("Not valid url to ectract the data.", e)

    def _get_book_url_from_main_page_book(self, book_class: BeautifulSoup):
        try:
            url = "catalogue/" + book_class.find('a', href=True).attrs.get("href").replace("../", "")
            # name = book_class.find('img', attrs={"class": "thumbnail"}).attrs.get("alt")
            # price = float(book_class.find('p', attrs={"class": "price_color"}).string[1:])
            # avail = True if book_class.find('p', attrs={"instock availability"}).text.strip() == "In stock" else False
        except Exception as e:
            print("Impossible to fetch book data from the main page.", e)
        return url

    def _parse_desc_table(self, table:BeautifulSoup, expected: list):
        all_keys = [th.text.lower() for th in table.findAll("th")]
        assert all_keys == expected, "Unknown keys"

        def prepare_val(key: str, val:str):
            if 'price' in key or 'tax' in key:
                return float(val[1:])
            elif key == 'availability':
                return int(''.join(filter(str.isdigit, val)))
            elif key == "number of reviews":
                return int(val)
            else: 
                return val

        all_vals = [prepare_val(key, th.text) for key, th in zip(all_keys, table.findAll("td"))]

        return dict(map(lambda i,j : (i,j) , all_keys, all_vals))

    def _get_vals_from_description(self, book_class: BeautifulSoup, expected_cols: list):
        try:
            name = book_class.find("div", attrs={"class": "col-sm-6 product_main"}).find("h1").text
            description_elem = book_class.find("div", attrs={"class": "sub-header", "id": "product_description"})
            description = description_elem.next_element.next_element.next_element.next_element.next_element.next_element.text if description_elem else ""
            rating = Rating[book_class.find("p", attrs={"class": "star-rating"}).attrs.get("class")[1]]

            book_vals = self._parse_desc_table(book_class.find('table', attrs={"class": "table table-striped"}), expected_cols)
            book_vals["description"] = description
            book_vals["name"] = name
            book_vals["rating"] = rating
            return book_vals
        except Exception as e:
            print("Impossible to fetch book data from the description page.", e)

    def _get_items_from_page_markup(self, soup: BeautifulSoup, expected_cols:list, category: str, category_url: str):
        for book_class in soup.findAll('article', attrs={"class": "product_pod"}):
            new_book_url = self._get_book_url_from_main_page_book(book_class)

            # Get book data from description page and add to data frame
            description = self._get_data_from_url(self.BOOK_SHOP_BASE_URL + "/" + new_book_url)
            new_book = self._get_vals_from_description(description.find('article', attrs={"class": "product_page"}), expected_cols[5:])
            new_book["url"] = new_book_url
            new_book["category"] = category
            self.books_df = self.books_df._append(new_book, ignore_index=True)

            if self.verbose:
                print(f"\t\tCollected 1 book {new_book.get('name')}.")

        # Get data recursively from next pages
        next_page = self._next_page_url(soup)
        if next_page:
            if self.verbose:
                print("\tAnother page.")

            next_soap = self._get_data_from_url(category_url.replace("index.html", "") + "/" + next_page)
            self._get_items_from_page_markup(next_soap, expected_cols, category, category_url)


    def _get_all_category_links(self, soup: BeautifulSoup):
        all_generes = soup.find('ul', attrs={"class": "nav nav-list"}).findAll("a", href=True)
        category_link = dict()
        
        # Skip books, then all categories
        for genre in all_generes[1:]:
            category_link[genre.text.strip().lower()] = genre['href']
        return category_link

    def _next_page_url(self, soup: BeautifulSoup):
        buttons = soup.find('ul', attrs={"class": "pager"})
        if buttons:
            buttons = buttons.findAll("a", href=True)
            next = [button["href"] for button in buttons if button.text == "next"]
            return next[0] if len(next) > 0 else False
        return False
    
    def save_to_csv(self, path:str = "data/last_update.csv"):
        self.books_df.to_csv(path)

book_scraper = BookDataScraper(verbose=True)
book_scraper.collect_data()
book_scraper.save_to_csv()
print(book_scraper.books_df.shape)
