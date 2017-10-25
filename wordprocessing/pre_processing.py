import pgdb
import libvoikko
from gensim.models.phrases import Phrases, Phraser

_VOIKKO = libvoikko.Voikko('fi')
_POST_QUERY = 'SELECT id, content FROM posts'
_BATCH_SIZE = 100

with open('stop_words.txt') as f:
    stop_words = [word.rstrip() for word in f]

def get_posts(db):
    # TODO change loop to while True when actually doing this
    cursor = db.cursor()
    cursor.execute(_POST_QUERY)
    for i in range(50):
        posts = cursor.fetchmany(_BATCH_SIZE)
        if not posts:
            break
        yield from posts

def get_normalized_sentences(db):
    for post in get_posts(db):
        for sentence in split_post(post):
            yield normalize(sentence.sentenceText)

def split_post(post):
    return _VOIKKO.sentences(post.content)

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

# TODO normalize full posts, apply trigram model, store somewhere?
db = pgdb.connect(database='vauvafi')
phrases = Phrases(get_normalized_sentences(db))
bigram = Phraser(phrases)
trigram = Phrases(bigram[get_normalized_sentences(db)])
