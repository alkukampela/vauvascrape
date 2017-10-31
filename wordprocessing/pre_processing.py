import pgdb
import libvoikko
from gensim.models.phrases import Phrases, Phraser

_VOIKKO = libvoikko.Voikko('fi')

_POST_QUERY = 'SELECT id, content FROM posts'
_TOPIC_QUERY = '''SELECT topic_id AS id, string_agg(content, '\n\n') AS content
                  FROM posts
                  GROUP BY topic_id'''
_INSERT_NORMALIZED = 'INSERT INTO normalized_topics(id, content) VALUES(%d, %s)'
_BATCH_SIZE = 100

with open('stop_words.txt') as f:
    stop_words = [word.rstrip() for word in f]

def get_rows(db, query):
    with db.cursor() as cursor:
        cursor.execute(query)
        while True:
            rows = cursor.fetchmany(_BATCH_SIZE)
            if not rows:
                break
            yield from rows

def get_topics(db):
    yield from get_rows(db, _TOPIC_QUERY)

def get_posts(db):
    yield from get_rows(db, _POST_QUERY)

def get_normalized_sentences(db):
    for post in get_posts(db):
        for sentence in split_to_sentences(post.content):
            yield normalize(sentence.sentenceText)

def split_to_sentences(text):
    return _VOIKKO.sentences(text)

def normalize(text):
    words = []
    for token in tokenize(text):
        if not is_word(token):
            continue
        word = lemmatize(token)
        if word and not is_stop_word(word):
            words.append(word)
    return words

def tokenize(text):
    return _VOIKKO.tokens(text)

def is_word(token):
    return token.tokenType == libvoikko.Token.WORD

def lemmatize(token):
    analysis = _VOIKKO.analyze(token.tokenText)
    try:
        return analysis[0]['BASEFORM'].lower()
    except (IndexError, KeyError):
        return None

def is_stop_word(word):
    return word in stop_words

def build_phrase_model(sentence_stream):
    return Phraser(Phrases(sentence_stream))

def pre_process(text, bigram, trigram):
    return list(trigram[bigram[normalize(text)]])

def pre_process_topics(db):
    bigram = build_phrase_model(get_normalized_sentences(db))
    bigram.save('bigram_model')
    trigram = build_phrase_model(bigram[get_normalized_sentences(db)])
    trigram.save('trigram_model')
    with db.cursor() as cursor:
        cursor.executemany(_INSERT_NORMALIZED, (
            (topic.id, pre_process(topic.content, bigram, trigram))
            for topic in get_topics(db)
        ))
    db.commit()

if __name__ == '__main__':
    with pgdb.connect(database='vauvafi') as db:
        pre_process_topics(db)