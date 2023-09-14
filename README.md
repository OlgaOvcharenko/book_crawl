## Objective:
A real-time search engine based on user queries from the website http://books.toscrape.com/index.html.

## How to run:
```
./run.sh
```

This script creates a virtual environment if is not already created, activates it, and starts REST API and search engine.

Possible links:
* [Help](http://127.0.0.1:5000/help): http://127.0.0.1:5000/help
* [Main page](http://127.0.0.1:5000): http://127.0.0.1:5000
* [Query example 1](http://127.0.0.1:5000/simple/alice): http://127.0.0.1:5000/simple/alice
* [Query example 2](http://127.0.0.1:5000/args/alice/true): http://127.0.0.1:5000/args/alice/true

The difference between examples 1 and 2 is that 2 specifies not only query **alice**, but also if to search on all pages **true**.

## Deliverables:

### Task 1-2: Web Scraping and Data Extraction

Built a class `search_data.BookSearchScraper` to scrape data from the website, and `search_data.BookSearchScraper.collect_search_data(query: str, search_all_pages: bool, extended_info: bool)` to collect actual results.
Search functionality accepts a query string as an input parameter. It looks through all the categories on the webpage (in parallel using `joblib` task for each) for books that match the query string and returns up to 10 best matches.

Usage example:
```
# Create a class instance with cache updates every 3 seconds
book_scraper = BookSearchScraper(cache_update_ts=3)

# Collect results on all pages and show all information (not on;y name and price)
query = "alice in wonderland"
res_books = book_scraper.collect_search_data(query, search_all_pages=True, extended_info=False)

# Print results as a formatted table
get_matching_result_table(i, res_books, True)
```

Result:
```
+------------------------------------------------------------------------------------------------+
Input query: alice
-- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
 Matching Name Price Avail.Raiting
 ['alic'] alice in wonderland (alice's adventures in wonderland #1) 55.53 1 1
 ['alic'] walt disney's alice in wonderland 12.96 1 5
+------------------------------------------------------------------------------------------------+
```
`search_data.BookSearchScraper` uses `match_books.Matcher` to match queries with books by embeddings and simple inclusion check.

Results are structured as a list of:
* List of matches or cosine similarities
* Name
* Price
* Availability
* Rating

### Task 4: API Development

Developed a REST API in Python using `flask`. The API accepts a query string as part of the input URL and returns JSON.JSON was chosen since it is more common for REST API and a suitable data format than structured list, in my humble opinion.

### Task 5: Caching Strategy

Since there is no initial query history and distribution, it does not much sense to cache query results, we do not know if any cache hit will happen. Therefore, instead, all books found on the website are cached. The cache is refreshed if it is 3 seconds old. This is a good trade-off between performance and the actual task.

<!-- Another option would be to cache categories pages and links if all books can not fit in memory. This was the first thought but then again books fit into the memory. -->

### Task 6: Use of Embeddings
Advanced search was implemented using `word2vec`. It suffers from queries containing words out of vocabulary.
Words are preprocessed: lowercase, lemmatization, and stemming. Stop words are not removed since they lead to empty book names.
The averaged vector of all words in the book name is used to calculate cosine similarity between query and books. If cos similarity is greater 0.75, this is considered as a match. 

Initially, `FastText` was used, but the model is not serializable. This means that searching in parallel is not possible without some small tricks.

### Additional:
There are two additional scripts:
* `utils/extract_data_to_csv.py` extracts the whole webpage into a CSV file. It extracts not only information from the main page but also description, etc. from the book page. Not parallelized, slower.

* `utils/utils_embeddings.py` train `word2vec` model and compute avg. book name embeddings, and store.
