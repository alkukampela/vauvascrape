import pgdb
import libvoikko
from gensim.models.phrases import Phrases, Phraser

_VOIKKO = libvoikko.Voikko('fi')
_POST_QUERY = 'SELECT id, content FROM posts'
_TOPIC_QUERY = '''SELECT topic_id AS id, string_agg(content, '\n\n') AS content
                  FROM posts
                  GROUP BY topic_id'''
_BATCH_SIZE = 100

with open('stop_words.txt') as f:
    stop_words = [word.rstrip() for word in f]

def get_rows(db, query):
    # TODO change loop to while True when actually doing this
    cursor = db.cursor()
    cursor.execute(query)
    for i in range(20):
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
        if word is not None and not is_stop_word(word):
            words.append(word)
    return words

def tokenize(text):
    return _VOIKKO.tokens(text)

def is_word(token):
    return token.tokenType == libvoikko.Token.WORD

def lemmatize(token):
    # TODO
    # Check spelling suggestions if the word is unknown?
    # Ensure these are actually good.
    analysis = _VOIKKO.analyze(token.tokenText)
    if analysis:
        return analysis[0]['BASEFORM'].lower()

def is_stop_word(word):
    return word in stop_words

# TODO normalize full posts (or topics), apply trigram model, store somewhere
db = pgdb.connect(database='vauvafi')
phrases = Phrases(get_normalized_sentences(db))
bigram = Phraser(phrases)
trigram = Phrases(bigram[get_normalized_sentences(db)])

for topic in get_topics(db):
    normalized_topic = trigram[normalize(topic.content)]
    print(' '.join(normalized_topic))

