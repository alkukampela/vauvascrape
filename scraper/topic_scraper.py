import argparse
import requests
import bs4
import re
import pg

import utilities


BASE_URL = 'http://www.vauva.fi'
TOPIC_LIST_URL = BASE_URL + '/keskustelu/alue/{subforum}?page={page}'


def parse_topic_id_from_url(topic_url):
    # URL format:
    # /keskustelu/1660425/miks-salkkareissa-osa-ii?changed=1480763430
    reg_match = re.search(r'\/([0-9]+)', topic_url).group(0)
    return reg_match[1:]


def get_subforum_name(conn, subforum_id):
    row = conn.query('select name from subforums where id=$1',
                     subforum_id).namedresult()
    if not row:
        raise ValueError('Invalid subforum id')
    return row[0].name


def get_topics(page, subforum):
    topic_list_url = TOPIC_LIST_URL.format(subforum=subforum, page=page)
    topic_list_response = requests.get(topic_list_url)

    if topic_list_response.status_code != 200:
        return []

    topics = []
    topic_list_soup = utilities.convert_to_soup(topic_list_response.text)

    for topic in topic_list_soup.find_all('span', {'class': 'title'}):
        topic_url = topic.a['href']
        topics.append({
            'id': parse_topic_id_from_url(topic_url),
            'url': BASE_URL + topic_url,
            'title': topic.a.contents[-1]
        })

    return topics


def scrape_topics(subforum_id, first_page, last_page):
    conn = pg.DB(dbname='vauvafi', host='localhost', port=5432)
    subforum_name = get_subforum_name(conn, subforum_id)
    for page in range(first_page, last_page + 1):
        topics = get_topics(page, subforum_name)
        if not topics:
            print('reached end of {} on page {}'.format(subforum_name, page))
            break
        for topic in topics:
            topic['subforum_id'] = subforum_id
            try:
                conn.begin()
                conn.insert('topics', topic)
            except pg.IntegrityError:
                pass
            finally:
                conn.commit()

def main():
    parser = argparse.ArgumentParser(
        description='Tool for scraping content from vauva.fi forum')
    parser.add_argument(
        '-sf', metavar='subforum', type=int,
        help='id of the subforum', default=1)
    parser.add_argument(
        '-fp', metavar='first_page', type=int,
        help='number of the first page to fetch', default=0)
    parser.add_argument(
        '-lp', metavar='last_page', type=int,
        help='number of the last page to fetch', default=100)
    parser.add_argument(
        '-cp', metavar='config_path', type=str,
        help='path to the configuration file of the scraper')

    args = parser.parse_args()

    if args.fp > args.lp:
        raise ValueError("First page can't be after last page")
    if args.cp is None:
        raise ValueError('Configuration file not specified')

    config = utilities.get_configuration(args.cp)
    scrape_topics(args.sf, args.fp, args.lp)


if __name__ == '__main__':
    main()
