from bs4 import BeautifulSoup
import requests
import json
import time
import random
import itertools
import re
import configparser

BASE_URL = 'http://www.vauva.fi'
TOPIC_LIST_URL = BASE_URL + '/keskustelu/alue/{subforum}?page={page}'

def get_sleep_time():
    return random.randrange(100, 221) / 1000


def convert_to_soup(html):
    return BeautifulSoup(html, 'html.parser')


def fetch_as_soup(url):
    print('fetching ' + url)
    response = requests.get(url)
    return convert_to_soup(response.text)


def get_page_count(topic_soup):
    last_page_bullet = topic_soup.find('li', {'class': 'pager-last last'})
    if last_page_bullet is not None:
        return int(last_page_bullet.a.contents[0])
    return 1


def get_page_content(page):
    main_region = page.find('div', {'class': 'region-main'})

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


def parse_topic_id_from_url(topic_url):
    # URL format:
    # /keskustelu/1660425/miks-salkkareissa-osa-ii?changed=1480763430
    reg_match = re.search(r'\/([0-9]+)', topic_url).group(0)
    return reg_match[1:]


def get_topics(page, subforum='aihe_vapaa'):
    topic_list_url = TOPIC_LIST_URL.format(subforum=subforum, page=page)
    topic_list_response = requests.get(topic_list_url)

    if topic_list_response.status_code != 200:
        # NOTE:
        # We get timeout (503) to the request on a non-existent pages.
        # Consider checking only for that and reattempt/skip on other
        # errors.
        return []

    topics = []
    topic_list_soup = convert_to_soup(topic_list_response.text)

    for topic in topic_list_soup.find_all('span', {'class': 'title'}):
        topic_url = topic.a['href']
        topics.append({
            'id': parse_topic_id_from_url(topic_url),
            'url': BASE_URL + topic_url,
            'title': topic.a.contents[-1]
        })

    return topics


def get_topic_contents(topic):
    topic_contents = {
        'title': topic['title'],
        'url': topic['url'],
        'pages': [],
    }
    first_page_soup = fetch_as_soup(topic['url'])
    content = get_page_content(first_page_soup)
    topic_contents['pages'].append(content)

    page_count = get_page_count(first_page_soup)

    for page_number in range(1, page_count):
        page_url = topic['url'] + '&page=' + str(page_number)
        page = fetch_as_soup(page_url)
        content = get_page_content(page)
        topic_contents['pages'].append(content)
        time.sleep(get_sleep_time())

    return topic_contents


def dump_to_json_file(filename, content):
    with open(filename, 'w+') as file_handle:
        file_handle.write(json.dumps(content, indent=2))


def get_configuration():
    config = configparser.ConfigParser()
    config.read('scrape.ini')
    return {
        'index_file': config.get('Dump Files', 'TopicIndex'),
        'content_file':  config.get('Dump Files', 'TopicContents')
    }


def main():
    config = get_configuration()

    # Get list of topics
    topics = []
    for page in itertools.count():
        topics += get_topics(page)
        if not topics or page > 2:
            break

    dump_to_json_file(config['index_file'], topics)

    # Get contents of the topics
    topic_contents = []
    for topic in topics:
        topic_contents.append(get_topic_contents(topic))

    dump_to_json_file(config['content_file'], topic_contents)

if __name__ == '__main__':
    main()
