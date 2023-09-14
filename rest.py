from flask import Flask, json
from search_data import BookSearchScraper
from search_data import get_result_dict

BOOK_SCRAPER = BookSearchScraper(cache_update_ts=3)

api = Flask("book_search")

@api.route("/", methods=["GET"])
def get_home():
    return "Welcome, for help use http://127.0.0.1:5000/help.<br/> Otherwise, enter the link."

@api.route("/help", methods=["GET"])
def get_help():
    help = "Example simple query: " + "http://127.0.0.1:5000/simple/alice" + "<br/>" + \
        "Example query with arguments " + \
        "search_all_pages (true/false) - search not only first page: " +\
        "http://127.0.0.1:5000/args/sharp%20obj/true"
    return help

@api.route("/simple/<query>", methods=["GET"])
def get_book(query: str):
    res_books = BOOK_SCRAPER.collect_search_data(query, search_all_pages=True, extended_info=True)
    print(get_result_dict(query, res_books))
    return json.dumps(get_result_dict(query, res_books))

@api.route("/args/<query>/<search_all_pages>", methods=["GET"])
def get_book_with_args(query: str, search_all_pages: str):
    search_all_pages = bool(search_all_pages)
    res_books = BOOK_SCRAPER.collect_search_data(query, search_all_pages=search_all_pages, extended_info=True)
    return json.dumps(get_result_dict(query, res_books))

if __name__ == '__main__':
    api.run()
