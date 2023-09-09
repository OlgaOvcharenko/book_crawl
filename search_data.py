import multiprocessing
from urllib.request import urlopen
from bs4 import BeautifulSoup
from enum import Enum
import pandas as pd
from joblib import Parallel, delayed
from match_books import Matcher
import itertools
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)


class Rating(Enum):
    Zero = 0
    One = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5


class BookSearchScraper():
    expected_cols = [ 
        'url', 'name', 'rating', 'category', 'price', 'availability'
        ]
    
    BOOK_SHOP_URL = "http://books.toscrape.com/index.html"
    BOOK_SHOP_BASE_URL = "http://books.toscrape.com"


    def __init__(self) -> None:
        self.matcher = Matcher()
    
    def preprocess_text(self, text: str):
        return text.lower()

    def collect_search_data(self, query: str, extended_info: bool = False, search_all_pages: bool = False):
        # Preprocess
        query = self.preprocess_text(query)

        # Get main URL
        soup_main = self._get_data_from_url()

        # Get categories and get books for each in parallel
        category_link = self._get_all_category_links(soup_main)
        final_res = Parallel(n_jobs=len(category_link))(delayed(self._search_in_category)(link, query, extended_info, search_all_pages) for link in category_link.values())
        final_res = list(itertools.chain.from_iterable(final_res))

        return final_res

    def _search_in_category(self, link: str, query: str, extended_info: bool = False, search_all_pages: bool = False):
        full_url = self.BOOK_SHOP_BASE_URL + "/" + link
        soup_category = self._get_data_from_url(full_url)
        res_category = self._get_items_from_page_markup(soup_category, query, extended_info, search_all_pages)
        return res_category

    def _get_data_from_url(self, url: str = BOOK_SHOP_URL) -> BeautifulSoup:
        """"Extract data from the given url."""
        if url == '':
            raise TypeError("URL must be non-empty.")
            
        try: 
            page = urlopen(url)
            markup = page.read().decode("utf-8")
            soup = BeautifulSoup(markup=markup, features="html.parser")
            return soup
        except Exception as e:
            print("Not valid url to ectract the data.", e)
    
    def _get_book_info_from_page(self, book_class: BeautifulSoup, extended_info: bool = False):
        try:
            url = "catalogue/" + book_class.find('a', href=True).attrs.get("href").replace("../", "")
            name = book_class.find('img', attrs={"class": "thumbnail"}).attrs.get("alt").lower()
            price = float(book_class.find('p', attrs={"class": "price_color"}).string[1:])

            if extended_info:
                avail = True if book_class.find('p', attrs={"instock availability"}).text.strip() == "In stock" else False
                rating = Rating[book_class.find("p", attrs={"class": "star-rating"}).attrs.get("class")[1]]
                return url, [name, price, avail, rating]
        except Exception as e:
            print("Impossible to fetch book data from the main page.", e)
        return url, [name, price]

    def _get_items_from_page_markup(self, soup: BeautifulSoup, search_query: str, category_url: str, extended_info: bool = False, search_all_pages: bool = False):
        result = []
        for book_class in soup.findAll('article', attrs={"class": "product_pod"}):
            new_book_url, new_book = self._get_book_info_from_page(book_class, extended_info)
            if self.matcher.contains_query(search_query, new_book[0]):
                result.append(new_book)

        # Get data recursively from next pages
        if search_all_pages:
            next_page = self._next_page_url(soup)
            if next_page:
                next_soap = self._get_data_from_url(category_url.replace("index.html", "") + "/" + next_page)
                self._get_items_from_page_markup(next_soap, search_query, category_url)
        
        return result

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
    

def print_matching_result(query: str, matches: list):
    print("+-----------------------------------------------------------------------------+")
    print(f"Input query: {query}")
    
    if len(matches) == 0:
        print("No matches found.")
        return
    
    print("--   --   --   --   --   --   --")

    longest_cols = [
        (max([len(str(row[i])) for row in matches]) + 4) for i in range(len(matches[0]))
    ]
    row_format = "".join(["{:>" + str(longest_col) + "}" for longest_col in longest_cols])
    names = ["Name", "Price", "Avail.", "Raiting"] if len(matches[0]) > 2 else ["Name", "Price"]
    print(row_format.format(*names))
    for row in matches:
        print(row_format.format(*row))

    print("+-----------------------------------------------------------------------------+")


book_scraper = BookSearchScraper()
query="Alice in wonderland"
res_books = book_scraper.collect_search_data(query, search_all_pages=True, extended_info=True)
print_matching_result(query, res_books)
