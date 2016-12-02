from bs4 import BeautifulSoup
import requests
import json
import time
import random


BASE_URL = 'http://www.vauva.fi'
VAUVA_URL = BASE_URL + '/keskustelu/alue/{subject}?page={page}'


def get_sleep_time():
    return random.randrange(100, 221) / 1000


def convert_to_soup(html):
    return BeautifulSoup(html, 'html.parser')


def fetch_as_soup(url):
    print('fetching ' + url)
    response = requests.get(url)
    return convert_to_soup(response.text)


def get_page_count(thread_soup):
    last_page_bullet = thread_soup.find('li', {'class': 'pager-last last'})
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


def get_threads(page, subject='aihe_vapaa'):
    thread_list_url = VAUVA_URL.format(subject=subject, page=page)
    thread_list_response = requests.get(thread_list_url)
    if thread_list_response.status_code != 200:
        return []

    threads = []
    thread_list_soup = convert_to_soup(thread_list_response.text)
    for single_thread in thread_list_soup.find_all('span', {'class': 'title'}):
        # Remove redundant content
        for span in single_thread.find_all('span'):
            span.replaceWith('')
        single_thread = convert_to_soup(str(single_thread))

        threads.append({
            'url': BASE_URL + single_thread.a['href'],
            'title': single_thread.a.contents[0],
        })

    return threads


def get_thread_contents(thread):
    thread_contents = {
        'title': thread['title'],
        'url': thread['url'],
        'pages': [],
    }
    first_page_soup = fetch_as_soup(thread['url'])
    content = get_page_content(first_page_soup)
    thread_contents['pages'].append(content)

    page_count = get_page_count(first_page_soup)

    for page_number in range(1, page_count):
        page_url = thread['url'] + '?page=' + str(page_number)
        page = fetch_as_soup(page_url)
        content = get_page_content(page)
        thread_contents['pages'].append(content)
        time.sleep(get_sleep_time())

    return thread_contents


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

    thread_contents = []
    for thread in threads:
        thread_contents.append(get_thread_contents(thread))

    # TODO write to DB
    with open('vauva-threads.json', 'w+') as f:
        f.write(json.dumps(thread_contents, indent=2))


if __name__ == '__main__':
    main()
