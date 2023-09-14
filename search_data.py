import time
from urllib.request import urlopen
from bs4 import BeautifulSoup
from enum import Enum
import pandas as pd
from joblib import Parallel, delayed
from match_books import Matcher
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


    def __init__(self, cache_update_ts: float = 0.0) -> None:
        self.matcher = Matcher()
        # self.categories_cache = [] can be added if data does not fit in memory
        self.data_cache = []
        self.cache_ts = 0.0
        self.cache_update_ts = cache_update_ts
        self.use_embeddings = True
        self.best_k_matches = 10

    def collect_search_data(self, query: str, extended_info: bool = False, search_all_pages: bool = False):
        # Preprocess query
        query = self.matcher.preprocess_query(query)

        # Check if cached
        if len(self.data_cache) > 0 and time.time() - self.cache_ts < self.cache_update_ts:
            final_res = []

            search_query_emb = self.matcher.get_embedding_vector(query)
            final_res = [[m] + book for book in self.data_cache \
                         if (m := self.matcher.get_matches(search_query_emb, book[0], not self.use_embeddings)) \
                         or (m := self.matcher.get_matches(query, book[0], True))]

        else:
            # Get main URL
            soup_main = self._get_data_from_url()

            # Get categories and get books for each in parallel
            categories = self._get_all_category_links(soup_main)
            combined_res = Parallel(n_jobs=len(categories))\
                (delayed(self._search_in_category)\
                (link, query, extended_info, search_all_pages) for link in categories.values())
            
            # Merge results
            final_res, self.data_cache = [], []
            for vals in combined_res:
                final_res.extend([m] + b for b, m in zip(vals[0], vals[1]))
                self.data_cache.extend(vals[2])

            self.cache_ts=time.time()
        
        # Get k best, if matched by name then prioritize
        if len(final_res) > self.best_k_matches:
            final_res = sorted(final_res, key=lambda x: x[0][0] \
                               if isinstance(x[0][0], float) else 1, reverse=True)[0:self.best_k_matches]

        return final_res

    def _search_in_category(self, link: str, query: str, extended_info: bool = False, search_all_pages: bool = False):
        full_url = self.BOOK_SHOP_BASE_URL + "/" + link
        soup_category = self._get_data_from_url(full_url)
        res_category, res_match, res_cache = self._get_items_from_page_markup(soup_category, query, extended_info, search_all_pages)
        return res_category, res_match, res_cache

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
                rating = Rating[book_class.find("p", attrs={"class": "star-rating"}).attrs.get("class")[1]].value
                return url, [name, price, avail, rating]
        except Exception as e:
            print("Impossible to fetch book data from the main page.", e)
        return url, [name, price]

    def _get_items_from_page_markup(self, soup: BeautifulSoup, search_query: str, category_url: str, extended_info: bool = False, search_all_pages: bool = False):
        matches, result, cache = [], [], []
        for book_class in soup.findAll('article', attrs={"class": "product_pod"}):
            _, new_book = self._get_book_info_from_page(book_class, extended_info)
            cache.append(new_book)

            search_query_emb = self.matcher.get_embedding_vector(search_query)
            match_res = self.matcher.get_matches(search_query_emb, new_book[0], not self.use_embeddings)
            
            if not match_res:
                match_res = self.matcher.get_matches(search_query, new_book[0], True)

            if match_res:
                result.append(new_book)
                matches.append(match_res)

        # Get data recursively from next pages
        if search_all_pages:
            next_page = self._next_page_url(soup)
            if next_page:
                next_soap = self._get_data_from_url(category_url.replace("index.html", "") + "/" + next_page)
                self._get_items_from_page_markup(next_soap, search_query, category_url)
        
        return result, matches, cache

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
    

def get_matching_result_table(query: str, matches: list, to_print=True):
    line_breaker = "\n" if to_print else "<br/>" 
    
    lines = ("+-----------------------------------------------------------------------------+" + line_breaker)
    lines += (f"Input query: {query}" + line_breaker)
    
    if len(matches) == 0:
        lines += ("No matches found." + line_breaker)
        return
    
    lines += ("--   --   --   --   --   --   --" + line_breaker)

    longest_cols = [
        (max([len(str(row[i])) for row in matches]) + 4) 
        for i in range(len(matches[0]))
    ]
    row_format = "".join(["{:>" + str(longest_col) + "}" for longest_col in longest_cols])
    names = ["Matching", "Name", "Price", "Avail.", "Raiting"] if len(matches[0]) > 3 else ["Name", "Price"]
    lines += (row_format.format(*names) + line_breaker)
    for row in matches:
        row[0] = str(row[0])
        lines += (row_format.format(*row) + line_breaker)

    lines += ("+-----------------------------------------------------------------------------+" + line_breaker)
    
    if to_print:
        print(lines)
    
    return lines

def get_result_dict(query: str, matches: list):
    res = dict()
    res["query"] = query

    if len(matches) == 0:
        res["results"] = "No matches found."
        return res
    
    names = ["Matching", "Name", "Price", "Avail. (yes/no)", "Raiting"] if len(matches[0]) > 3 else ["Matching", "Name", "Price"]

    res_matches = dict()
    for match in matches:
        match_dict = dict()
        for name, row in zip(names, match):
            if name != "Name":
                match_dict[name] = str(row)
        res_matches[match[1]] = match_dict
    res["results"] = res_matches
    return res
