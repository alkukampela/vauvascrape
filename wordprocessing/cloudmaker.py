import argparse
import re
import libvoikko
import pg
import operator
from itertools import filterfalse
from collections import OrderedDict

import utilities
import sanitation

VOIKKO_BASEFORM = 'BASEFORM'
ILLEGAL_CHARS_REGEX = r',|!|\?|\.|\)|\(|\^|/|"|&|:|;|=|~|\+|\[|\]|{|}|_|\*|\|'
MAX_WORD_LENGTH = 50

def count_frequencies(baseform_words):
    frequencies = dict()
    words_in_corpus = 0
    for baseform_word in baseform_words:
        if baseform_word in frequencies:
            frequencies[baseform_word] += 1
        else:
            frequencies[baseform_word] = 1
        words_in_corpus += 1

    for key, value in frequencies.items():
        frequencies[key] /= words_in_corpus

    frequencies = OrderedDict(sorted(frequencies.items(), key=operator.itemgetter(0)))
    return OrderedDict(sorted(frequencies.items(), key=operator.itemgetter(1), reverse=True))

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


def get_sanitized_topic(config):
    db = pg.DB(dbname=config['db_name'],
               host=config['db_host'],
               port=config['db_port'],
               user=config['db_user'],
               passwd=config['db_password'])

    posts = db.query('SELECT content '
                     'FROM posts '
                     'WHERE topic_id=$1 '
                     'ORDER BY post_number', 1660425).namedresult()

    topic = ' '.join([post.content for post in posts])

    topic = remove_smilies(topic)
    # Remove unneeded characters
    topic = re.sub(ILLEGAL_CHARS_REGEX, ' ', topic)
    # Remove multiple whitespaces
    topic = re.sub(r'\s+', ' ', topic).strip()

    return topic


def main():
    parser = argparse.ArgumentParser(
        description='Tool for parsing post data from vauva.fi forum')
    parser.add_argument(
        '-cp', metavar='config_path', type=str,
        help='path to the configuration file of the parser')
    args = parser.parse_args()
    config = utilities.get_configuration(args.cp)

    topic = (get_sanitized_topic(config))
    baseword_frequencies = get_baseword_frequencies(topic)

    for word, freq in baseword_frequencies.items():
        print(word + ': '+str(freq))

if __name__ == '__main__':
    main()
