import configparser
import json
import bs4
import requests

CONFIG_PATH = 'config/scraper.ini'


def get_configuration(config_path=CONFIG_PATH):
    config = configparser.ConfigParser()
    config.read(config_path)
    return {
        'db_host': config.get('Database', 'Host'),
        'db_port': int(config.get('Database', 'Port')),
        'db_name': config.get('Database', 'DbName'),
        'db_user': config.get('Database', 'User'),
        'db_password': config.get('Database', 'Password'),
    }


def dump_to_json_file(filename, content):
    with open(filename, 'w+') as file_handle:
        file_handle.write(json.dumps(content,
                                     indent=2,
                                     default=lambda o: str(o),
                                     ensure_ascii=False))


def convert_to_soup(html):
    return bs4.BeautifulSoup(html, 'html.parser')


def remove_attributes(soup):
    for tag in soup.findAll(True): 
        tag.attrs = {}
    return soup
