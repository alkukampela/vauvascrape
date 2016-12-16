import configparser
import json
import bs4
import requests

# TODO share the utilities with scraper

CONFIG_PATH = 'config/scraper.ini'


def get_configuration(config_path=CONFIG_PATH):
    config = configparser.ConfigParser()
    config.read(config_path)
    return {
        'db_host': config.get('Database', 'Host'),
        'db_port': config.getint('Database', 'Port'),
        'db_name': config.get('Database', 'DbName'),
        'db_user': config.get('Database', 'User'),
        'db_password': config.get('Database', 'Password'),
        'batch_size': config.getint('PostParser', 'BatchSize'),
    }


def dump_to_json_file(filename, content):
    with open(filename, 'w+') as file_handle:
        file_handle.write(json.dumps(content,
                                     indent=2,
                                     default=lambda o: str(o),
                                     ensure_ascii=False))
