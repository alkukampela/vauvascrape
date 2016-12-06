import argparse
import pg
import random
import sys
import time
import datetime
import re

from utilities import *


def get_sleep_time():
    return random.randrange(100, 221) / 1000


def fetch_page_as_soup(topic_url, page_number):
    url = topic_url + '?page=' + str(page_number)
    print('fetching ' + url)
    response = requests.get(url)
    if response.status_code == 200:
        return convert_to_soup(response.text)
    return None


def get_page_count(topic_soup):
    last_page_bullet = topic_soup.find('li', {'class': 'pager-last last'})
    if last_page_bullet is not None:
        return int(last_page_bullet.a.contents[0])
    return 1


def get_page_content(page_soup):
    main_region = page_soup.find('div', {'class': 'region-main'})

    # Remove social media integrations
    for span in main_region.find_all('div', {'class': 'before clearfix'}):
        span.replaceWith('')

    # Remove comment form
    for span in main_region.find_all('div', {'class': 'comment-form-wrapper'}):
        span.replaceWith('')

    # Remove paging
    for span in main_region.find_all('ul', {'class': 'pager'}):
        span.replaceWith('')

    # Remove paging title
    for span in main_region.find_all('h2', {'class': 'element-invisible'}):
        span.replaceWith('')

    # Remove message actions
    for span in main_region.find_all('div', {'class': 'bottom clearfix'}):
        span.replaceWith('')

    return str(main_region)


def get_topic_pages(topic_url):
    pages = []
    first_page_soup = fetch_page_as_soup(topic_url, 0)
    if not first_page_soup:
        return []
    content = get_page_content(first_page_soup)
    pages.append({'page_number': 0, 'content': content})

    page_count = get_page_count(first_page_soup)

    for page_number in range(1, page_count):
        page_soup = fetch_page_as_soup(topic_url, page_number)

        if not page_soup:
            # Content couldn't be fetched
            return []

        content = get_page_content(page_soup)
        pages.append({'page_number': page_number, 'content': content})
        # Tryin' to be polite
        time.sleep(get_sleep_time())

    return pages


def remove_old_posts(db, topic_id):
    db.query('DELETE FROM post_pages WHERE topic_id = $1', topic_id)


def get_next_topic_to_fetch(db, fetch_time_limit):
    row = db.query('SELECT id, url '+
                   'FROM topics '+
                   'WHERE is_invalid = false '+
                   'AND fetch_time < $1'
                   'ORDER BY RANDOM() LIMIT 1', fetch_time_limit).namedresult()
    if not row:
        db.close()
        print('No topics to fetch')
        sys.exit()

    return  {
        "id": row[0].id,
        "url": row[0].url
    }


def save_topic_pages(db, topic_id, pages):
    for page in pages:
        page['topic_id'] = topic_id
        db.insert('post_pages', page)


def set_fetch_time(db, topic_id):
    db.query('UPDATE topics SET fetch_time = NOW() WHERE id = $1', topic_id)


def mark_topic_as_invalid(db, topic_id):
    db.query('UPDATE topics SET is_invalid=TRUE WHERE id = $1', topic_id)


def fetch_topic_contents(config, fetch_time_limit):
    db = pg.DB(dbname=config['db_name'],
               host=config['db_host'],
               port=config['db_port'])
    while True:
        db.begin()
        topic_metadata = get_next_topic_to_fetch(db, fetch_time_limit)
        remove_old_posts(db, topic_metadata['id'])
        pages = get_topic_pages(topic_metadata['url'])
        if not pages:
            print('Topic id '+str(topic_metadata['id'])+' was marked as invalid')
            mark_topic_as_invalid(db, topic_metadata['id'])
            db.commit()
            continue

        save_topic_pages(db, topic_metadata['id'], pages)
        set_fetch_time(db, topic_metadata['id'])
        db.commit()
        print('Topic id '+str(topic_metadata['id'])+ ' saved with '+str(len(pages))+' pages.')

    db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Tool for scraping topic posts from vauva.fi forum')
    parser.add_argument(
        '-cp', metavar='config_path', type=str,
        help='path to the configuration file of the scraper')

    args = parser.parse_args()

    if args.cp is None:
        raise ValueError('Configuration file not specified')

    config = get_configuration(args.cp)

    # TODO: read from argument
    fetch_time_limit = '2000-01-01'

    fetch_topic_contents(config, fetch_time_limit)

if __name__ == '__main__':
    main()
