from bs4 import BeautifulSoup
import requests
import json
import time
import random
import itertools

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
    for span in main_region.find_all('li', {'class': 'pager'}):
        span.replaceWith('')

    # Remove message actions
    for span in main_region.find_all('div', {'class': 'bottom clearfix'}):
        span.replaceWith('')

    return str(main_region)


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
        topics.append({
            'url': BASE_URL + topic.a['href'],
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
        page_url = topic['url'] + '?page=' + str(page_number)
        page = fetch_as_soup(page_url)
        content = get_page_content(page)
        topic_contents['pages'].append(content)
        time.sleep(get_sleep_time())

    return topic_contents


def main():

    # Get list of topics
    topics = []
    for page in itertools.count():
        topics += get_topics(page)
        if not topics:
            break
        # TODO
        break

    # Get contents of the topics
    topic_contents = []
    for topic in topics:
        topic_contents.append(get_topic_contents(topic))

    # TODO write to DB
    with open('vauva-topics.json', 'w+') as f:
        f.write(json.dumps(topic_contents, indent=2))


if __name__ == '__main__':
    main()
