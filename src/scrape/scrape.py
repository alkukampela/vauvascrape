from bs4 import BeautifulSoup
import requests
import json
import time
import random

BASE_URL = 'http://www.vauva.fi'
VAUVA_URL = BASE_URL + '/keskustelu/alue/{subject}?page={page}'

def get_sleep_time():
    return random.randrange(100, 221) / 1000

def get_soup(html):
    return BeautifulSoup(html, 'html.parser')

def fetch_as_soup(url):
    response = requests.get(url)
    return get_soup(response.text)

def get_threads(page):
    thread_page_response = requests.get(VAUVA_URL.format(subject='aihe_vapaa', page=page))
    if thread_page_response.status_code != 200:
        return []

    threads = []
    thread_page_soup = get_soup(thread_page_response.text)
    for single_thread in thread_page_soup.find_all('span', {'class': 'title'}):
        # Remove redundant content
        for span in single_thread.find_all('span'):
            span.replaceWith('')
        single_thread = get_soup(str(single_thread))

        threads.append({
            'url': BASE_URL + single_thread.a['href'],
            'title': single_thread.a.contents[0],
        })
    return threads

def get_page_count(thread_soup):
    last_page_bullet = thread_soup.find('li', {'class': 'pager-last last'})
    if last_page_bullet is not None:
        return int(last_page_bullet.a.contents[0])
    return 1

def get_page_content(page):
    return str(page.find('div', {'class': 'region-main'}))

def get_keijo(thread):
    keijo = {
        'title': thread['title'],
        'url': thread['url'],
        'pages': [],
    }
    first_page_soup = fetch_as_soup(thread['url'])
    page_count = get_page_count(first_page_soup)
    keijo['pages'].append(get_page_content(first_page_soup))

    for page_number in range(1, page_count):
        page_url = thread['url'] + '?page=' + str(page_number)
        print('fetching ' + page_url)
        page = fetch_as_soup(page_url)
        content = get_page_content(page)
        keijo['pages'].append(content)
        time.sleep(get_sleep_time())

    return keijo


def main():
    page = 0
    threads = []
    while True:
        threads += get_threads(page)
        if not threads:
            break
        page += 1
        # TODO
        break

    keijos = []
    for thread in threads:
        keijos.append(get_keijo(thread))

    with open('keijos.json', 'w+') as f:
        f.write(json.dumps(keijos, indent=2))

if __name__ == '__main__':
    main()
