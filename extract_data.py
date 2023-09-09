from urllib.request import urlopen
from bs4 import BeautifulSoup
from enum import Enum
import pandas as pd
import re


# class syntax
class Rating(Enum):
    One = 1
    Two = 2
    Three = 3
    Four = 4
    Five = 5


BOOK_SHOP_URL = "http://books.toscrape.com/index.html"
BOOK_SHOP_BASE_URL = "http://books.toscrape.com"


def get_data_from_url(url: str = BOOK_SHOP_URL) -> BeautifulSoup:
    """"Extracts data from the given url."""
    if url == '':
        raise TypeError("URL must be non-empty.")
    
    try: 
        page = urlopen(url)
    except Exception:
        print("Not valid url to ectract the data.")

    markup = page.read().decode("utf-8")
    soup = BeautifulSoup(markup=markup, features="html.parser")
    return soup

def get_book_url_from_main_page_book(book_class: BeautifulSoup):
    try:
        url = book_class.find('a', href=True).attrs.get("href")
        # name = book_class.find('img', attrs={"class": "thumbnail"}).attrs.get("alt")
        # price = float(book_class.find('p', attrs={"class": "price_color"}).string[1:])
        # avail = True if book_class.find('p', attrs={"instock availability"}).text.strip() == "In stock" else False
    except Exception:
        print("Impossible to fetch book data from the main page.")
    return url

def parse_desc_table(table:BeautifulSoup, expected: list):
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

def get_vals_from_description(book_class: BeautifulSoup, expected_cols: list):
    try:
        # FIXME selectum
        category = None
        name = book_class.find("div", attrs={"class": "col-sm-6 product_main"}).find("h1").text
        description = book_class.find("div", attrs={"class": "sub-header", "id": "product_description"})\
            .next_element.next_element.next_element.next_element.next_element.next_element.text
        rating = Rating[book_class.find("p", attrs={"class": "star-rating"}).attrs.get("class")[1]]

        book_vals = parse_desc_table(book_class.find('table', attrs={"class": "table table-striped"}), expected_cols)
        book_vals["description"] = description
        book_vals["name"] = name
        book_vals["rating"] = rating
        book_vals["categoty"] = category
        return book_vals
    except Exception:
        print("Impossible to fetch book data from the description page.")

def get_items_from_page_markup(soup: BeautifulSoup, books_df:pd.DataFrame, expected_cols:list) -> pd.DataFrame:
    for book_class in soup.findAll('article', attrs={"class": "product_pod"}):
        new_book_url = get_book_url_from_main_page_book(book_class)

        # Get book data from description page and add to data frame
        description = get_data_from_url(BOOK_SHOP_BASE_URL + "/" + new_book_url)
        new_book = get_vals_from_description(description.find('article', attrs={"class": "product_page"}), expected_cols[5:])
        new_book["url"] = new_book_url
        books_df = books_df._append(new_book, ignore_index=True)
    return books_df

# TODO
# category
# fixup
# pages
    
expected_cols = [ 
        'url', 'description', 'name', 'rating', 'category', 
        'upc', 'product type', 
        'price (excl. tax)', 'price (incl. tax)', 'tax', 
        'availability', 'number of reviews']
books_df = pd.DataFrame(columns=expected_cols)

soup = get_data_from_url()
get_items_from_page_markup(soup)

