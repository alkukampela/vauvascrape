===========
vauvascrape
===========

Toolset for scraping content from vauva.fi forum.

Requirements
------------
PostgreSQL with database schema (and subforum mappings) that can be initialized using ``db/init_db.sql`` script.

Topic Scraper
-------------

This tool scrapes topic metadata (id, url and title) from provided subforum. Metadata must be 
scraped before the actual content can be scraped.

Parameters
~~~~~~~~~~
    - ``-sf`` Subforum id, see list below. Uses 1 if not provided.
    - ``-fp`` First page where topics are looked in. Scraping starts from first page if the parameter is not provided.
    - ``-lp`` Last page where topics are looked in. Scraping stops at page 100 if the parameter is not provided.
    - ``-cp`` path to ``scrape.ini`` file.

Subforums
~~~~~~~~~~
+----+-------------------------------------------+
| id | name                                      |
+----+-------------------------------------------+
| 1  | aihe_vapaa                                |
+----+-------------------------------------------+
| 2  | vauvakuume                                |
+----+-------------------------------------------+
| 3  | raskaus_ja_synnytys                       |
+----+-------------------------------------------+
| 4  | vauvat_ja_taaperot                        |
+----+-------------------------------------------+
| 5  | kasvatus                                  |
+----+-------------------------------------------+
| 6  | perhe_ja_arki                             |
+----+-------------------------------------------+
| 7  | lapsettomuus_ja_adoptio                   |
+----+-------------------------------------------+
| 8  | erota_vai_ei_kysy_asiantuntijat_vastaavat |
+----+-------------------------------------------+
| 9  | kysy_terveydenhoitajalta                  |
+----+-------------------------------------------+
| 10 | keskustele_unesta_ja_jaksamisesta         |
+----+-------------------------------------------+
| 11 | kysy_seksuaaliterapeutilta                |
+----+-------------------------------------------+
| 12 | erota_vai_ei_asiantuntijat_vastaavat      |
+----+-------------------------------------------+
| 13 | keskustelu_unesta_ja_jaksamisesta         |
+----+-------------------------------------------+
| 14 | keskustelu_nettikiusaamisesta             |
+----+-------------------------------------------+
| 15 | seksi                                     |
+----+-------------------------------------------+
| 16 | nimet                                     |
+----+-------------------------------------------+

Post Scraper
------------
This tool gets topic's pages containing posts and stores them to DB. Some of the content in 
pages is removed before saving (f.e. social media integrations and links to various actions).
Topics are fetched in (pseudo) random order to allow paraller executioning. If fetching of topic 
fails for whatever reason the topic will be marked as invalid. Program runs until all non invalid 
topics are fetched or it's stopped (ctrl+c).

Parameters
~~~~~~~~~~
    - ``-cp`` path to ``scrape.ini`` file.

Post Parser
-----------
This tool fetches topic's posts from DB and extracts actual data from posts to ``posts``-table. 
Topics are fetched in similar fashion with Post Scraper.
Things that are stored to each post:

    - Topic's identity
    - Post content without HTML-tags and quoted content from other posts
    - Timestamp when post was published
    - Post's position in the topic

Parameters
~~~~~~~~~~
    - ``-cp`` path to ``scrape.ini`` file.