import argparse
import re
import libvoikko
import pg
import operator
from itertools import filterfalse
from collections import OrderedDict, Counter

import utilities
import sanitation

VOIKKO_BASEFORM = 'BASEFORM'
ILLEGAL_CHARS_REGEX = r',|!|\?|\.|\)|\(|\^|/|"|&|:|;|=|~|\+|\[|\]|{|}|_|\*|\|'
MAX_WORD_LENGTH = 50

def count_frequencies(baseform_words):
    frequencies = Counter(baseform_words)
    words_in_corpus = len(baseform_words)

    freq_list = []
    for word, frequency in frequencies.items():
        freq_list.append({
            "word": word,
            "frequency": frequency,
            "scaled_frequency": frequency / words_in_corpus,
        })

    return words_in_corpus, freq_list

def remove_numbers(words):
    return list(filterfalse(lambda word: word.isdigit(), words))

def remove_common_words(words):
    common_words = sanitation.get_common_words()
    return list(filterfalse(lambda word: word in common_words, words))


def get_baseform_word(voikko, word):
    word = word[0:MAX_WORD_LENGTH - 1]
    word_analysis = voikko.analyze(word)
    pros_words = []

    if word_analysis:
        pros_words.append(word_analysis[0][VOIKKO_BASEFORM])
    else:
        voikko_suggestions = voikko.suggest(word)
        if voikko_suggestions:
            # Coumpound words might have been typed together
            suggestions = voikko_suggestions[0].split()

            for suggestion in suggestions:
                suggestion_voikko = voikko.analyze(suggestion)
                if suggestion_voikko:
                    pros_words.append(suggestion_voikko[0][VOIKKO_BASEFORM])
                else:
                    pros_words.append(suggestion)

    if not pros_words:
        pros_words.append(word)

    return pros_words


def get_baseword_frequencies(topic):
    voikko = libvoikko.Voikko('fi')
    orig_words = topic.split()
    baseform_words = []
    for orig_word in orig_words:
        word = orig_word.strip('-')
        if word:
            baseform_words += get_baseform_word(voikko, word)

    baseform_words = remove_common_words(baseform_words)
    baseform_words = remove_numbers(baseform_words)
    return count_frequencies(baseform_words)


def remove_smilies(topic):
    smilies = sanitation.get_smilies()
    for smiley in smilies:
        topic = topic.replace(smiley, ' ')
    return topic


def get_sanitized_topic(db, topic_id):
    posts = db.query('SELECT content '
                     'FROM posts '
                     'WHERE topic_id=$1 '
                     'ORDER BY post_number', topic_id).namedresult()

    topic = ' '.join([post.content for post in posts])

    topic = remove_smilies(topic)
    # Remove unneeded characters
    topic = re.sub(ILLEGAL_CHARS_REGEX, ' ', topic)
    # Remove multiple whitespaces
    topic = re.sub(r'\s+', ' ', topic).strip()

    return topic


def get_next_topic_id_to_parse(db):
    while True:
        row = db.query('SELECT id '
                       'FROM topics '
                       'WHERE is_invalid = false '
                       'AND word_count = 0'
                       'ORDER BY RANDOM() '
                       'LIMIT 1').namedresult()
        if not row:
            print('No topics left to parse')
            return

        yield row[0].id


def materialize(db, topic_id, words_in_corpus, baseword_frequencies):
    db.query('UPDATE topics SET word_count=$1 WHERE id = $2',
             words_in_corpus,
             topic_id)
    for word in baseword_frequencies:
        word['topic_id'] = topic_id
        db.insert('topic_words', word)
    print('Saved {} words for topic id {}'.format(words_in_corpus, topic_id))

def mark_topic_as_invalid(db, topic_id):
    db.query('UPDATE topics SET is_invalid=TRUE WHERE id = $1', topic_id)

def process_topics(config):
    db = pg.DB(dbname=config['db_name'],
               host=config['db_host'],
               port=config['db_port'],
               user=config['db_user'],
               passwd=config['db_password'])

    db.begin()
    for topic_id in get_next_topic_id_to_parse(db):
        topic = get_sanitized_topic(db, topic_id)
        words_in_corpus, baseword_frequencies = get_baseword_frequencies(topic)
        if words_in_corpus:
            materialize(db, topic_id, words_in_corpus, baseword_frequencies)
        else:
            mark_topic_as_invalid(db, topic_id)
        db.commit()
        db.begin()

    db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Tool for parsing post data from vauva.fi forum')
    parser.add_argument(
        '-cp', metavar='config_path', type=str,
        help='path to the configuration file of the parser')
    args = parser.parse_args()
    config = utilities.get_configuration(args.cp)
    process_topics(config)


if __name__ == '__main__':
    main()
