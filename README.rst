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
TODO
