from bs4 import BeautifulSoup
import requests

BASE_URL = 'http://www.vauva.fi/'
VAUVA_URL = BASE_URL + 'keskustelu/alue/{subject}?page={page}'

def get_soup(html):
    return BeautifulSoup(html, 'html.parser')

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

def get_thread_last_page_number(thread_soup):
    last_page_bullet = thread_soup.find('li', {'class': 'pager-last last'})
    if last_page_bullet is not None:
        return int(last_page_bullet.a.contents[0]) - 1
    return 0

def get_thread_pages(thread):
    first_page = requests.get(thread['url'])
    first_page_soup = get_soup(first_page.text)
    page_count = get_thread_last_page_number(first_page_soup)
    print(page_count)
    return []

def main():
    page = 0
    threads = []
    while True:
        threads += get_threads(page)
        if not threads:
            break
        page += 1
        # TODO
        if page > 5:
            break

    for thread in threads:
        thread_pages = get_thread_pages(thread)

if __name__ == '__main__':
    main()
