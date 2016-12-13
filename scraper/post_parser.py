import argparse
import requests
import re
import json
from datetime import datetime

import pg
import bs4

import utilities


class PostParser:

    # E.g. "klo 22:32 | 18.4.2008"
    VAUVA_DATETIME_FORMAT = 'klo %H:%M | %d.%m.%Y'

    CONTENT_CLASSES = re.compile('^(field-name-body|field-name-comment-body)$')


    def __init__(self, config):
        self.db = None
        self.config = config


    def get_next_topic_id_to_parse(self):
        while True:
            row = self.db.query(
                'SELECT T.id '+
                'FROM topics T '+
                'LEFT JOIN posts P '+
                'ON T.id = P.topic_id '+
                'WHERE T.is_invalid = false '+
                'GROUP BY T.id ' +
                'HAVING COUNT(P.*) = 0 ' +
                'ORDER BY RANDOM() LIMIT 1').namedresult()
            if not row:
                print('No topics left to parse')
                return

            yield row[0].id


    def get_post_pages(self, topic_id):
        rows = self.db.query(
            'SELECT content ' +
            'FROM post_pages ' +
            'WHERE topic_id = $1 ' +
            'ORDER BY page_number', topic_id).namedresult()
        return [row.content for row in rows]


    def parse_post_timestamp(self, post_soup):
        container = post_soup.find('div', {'class': 'field-name-post-date'})
        timestamp_str = container.find('div', {'class': 'field-item'}).contents[0]
        return datetime.strptime(timestamp_str, PostParser.VAUVA_DATETIME_FORMAT)


    def remove_quotations(self, post_content):
        for quote in post_content.find_all('blockquote'):
            quote.replaceWith('')
        return post_content


    def remove_linefeeds(self, post_content):
        return post_content.replace('\n', ' ')


    def purify_content(self, post_content_soap):
        post_content_soap = utilities.remove_attributes(post_content_soap)
        post_content_soap = self.remove_quotations(post_content_soap)

        # Replace br-tags with linefeeds
        for br in post_content_soap.find_all('br'):
            br.replace_with('\n')

        post_content = post_content_soap.get_text()
        post_content = self.remove_linefeeds(post_content)

        # Remove multiple whitespaces
        post_content = re.sub('\s+', ' ', post_content).strip()
        return post_content


    def parse_post_content(self, post_soup):
        container = post_soup.find('div', {'class': PostParser.CONTENT_CLASSES})
        if container is None:
            return

        post_content_soap = container.find('div', {'class': 'field-item'})
        post_content = self.purify_content(post_content_soap)
        return post_content


    def parse_posts(self, sanoma_comment_soups):
        posts = []
        for sanoma_comment_soup in sanoma_comment_soups:
            content = self.parse_post_content(sanoma_comment_soup)
            if not content:
                # No need to store empty posts
                continue

            post_time = self.parse_post_timestamp(sanoma_comment_soup)
            posts.append({
                'content': content,
                'post_time': post_time,
            })

        return posts


    def parse_topic(self, pages):
        sanoma_comment_soups = []
        for page in pages:
            page_soup = utilities.convert_to_soup(page)
            sanoma_comment_soups += page_soup.find_all('div', {'class': 'sanoma-comment'})

        return self.parse_posts(sanoma_comment_soups)


    def add_topic_id_post_numbers(self, topic_id, posts):
        for i, post in enumerate(posts):
            post['topic_id'] = topic_id
            post['post_number'] = i+1
        return posts


    def mark_topic_as_invalid(self, topic_id):
        self.db.query('UPDATE topics SET is_invalid=TRUE WHERE id = $1', topic_id)

    def save_posts(self, posts):
        for post in posts:
            self.db.insert('posts', post)

    def parse_topics(self):
        self.db = pg.DB(dbname=self.config['db_name'],
                        host=self.config['db_host'],
                        port=self.config['db_port'],
                        user=self.config['db_user'],
                        passwd=self.config['db_password'])

        self.db.begin()
        for topic_id in self.get_next_topic_id_to_parse():
            print('Parsing topic ' + str(topic_id))
            post_pages = self.get_post_pages(topic_id)
            posts = self.parse_topic(post_pages)

            if posts is None:
                # Only empty posts in topic, mark it as invalid
                self.mark_topic_as_invalid(topic_id)
            else:
                posts = self.add_topic_id_post_numbers(topic_id, posts)
                self.save_posts(posts)

            self.db.commit()
            self.db.begin()

        self.db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Tool for parsing post data from vauva.fi forum')
    parser.add_argument(
        '-cp', metavar='config_path', type=str,
        help='path to the configuration file of the parser')
    args = parser.parse_args()

    config = utilities.get_configuration(args.cp)

    post_parser = PostParser(config)
    post_parser.parse_topics()


if __name__ == '__main__':
    main()
