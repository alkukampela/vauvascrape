import configparser
import json
import bs4


CONFIG_PATH = 'config/scraper.ini'


def get_configuration(config_path=CONFIG_PATH):
    config = configparser.ConfigParser()
    config.read(config_path)
    return {
        'index_file': config.get('Dump Files', 'TopicIndex'),
        'content_file': config.get('Dump Files', 'TopicContents')
    }

def dump_to_json_file(filename, content):
    with open(filename, 'w+') as file_handle:
        file_handle.write(json.dumps(content, indent=2))

def convert_to_soup(html):
    return bs4.BeautifulSoup(html, 'html.parser')

def fetch_as_soup(url):
    print('fetching ' + url)
    response = requests.get(url)
    return convert_to_soup(response.text)
