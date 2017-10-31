import pgdb
from gensim.corpora import Dictionary, MmCorpus
from gensim.models.ldamulticore import LdaMulticore
from pre_processing import get_rows
import pyLDAvis
import pyLDAvis.gensim

_NORMALIZED_TOPIC_QUERY = 'SELECT * FROM normalized_topics'

def get_normalized_topics(db):
    for topic in get_rows(db, _NORMALIZED_TOPIC_QUERY):
        yield topic.content

def build_dictionary(normalized_topic_stream):
    dictionary = Dictionary(normalized_topic_stream)
    dictionary.filter_extremes(no_below=10, no_above=0.4)
    dictionary.compactify()
    return dictionary

def get_topic_bows(dictionary, normalized_topic_stream):
    for topic in normalized_topic_stream:
        yield dictionary.doc2bow(topic)

def build_corpus(dictionary, fname):
    topic_bow_generator = get_topic_bows(dictionary, get_normalized_topics(db))
    MmCorpus.serialize(fname, topic_bow_generator)
    corpus = MmCorpus(fname)
    return corpus

def train_lda(db):
    dictionary = build_dictionary(get_normalized_topics(db))
    corpus = build_corpus(dictionary, 'corpus_mm')
    lda = LdaMulticore(corpus, num_topics=50, id2word=dictionary, workers=3)
    lda.save('lda_model')

if __name__ == '__main__':
    with pgdb.connect(database='vauvafi') as db:
        train_lda(db)