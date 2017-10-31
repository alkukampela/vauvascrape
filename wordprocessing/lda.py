import pgdb
from gensim.corpora import Dictionary, MmCorpus
from gensim.models.ldamulticore import LdaMulticore
from pre_processing import get_rows
from tqdm import tqdm
import pyLDAvis
import pyLDAvis.gensim

def get_normalized_topics(db):
    for topic in tqdm(get_rows(db, 'SELECT * FROM normalized_topics')):
        yield topic.content

def build_dictionary(normalized_topic_stream):
    dictionary = Dictionary(normalized_topic_stream)
    dictionary.filter_extremes(no_below=10, no_above=0.4)
    dictionary.compactify()
    return dictionary

def get_topic_bows(dictionary, normalized_topic_stream):
    for topic in normalized_topic_stream:
        yield dictionary.doc2bow(topic)

with pgdb.connect(database='vauvafi') as db:
    dictionary = build_dictionary(get_normalized_topics(db))

    topic_bow_generator = get_topic_bows(dictionary, get_normalized_topics(db))
    MmCorpus.serialize('mm_corpus', topic_bow_generator)
    corpus = MmCorpus('mm_corpus')

    lda = LdaMulticore(corpus, num_topics=50, id2word=dictionary, workers=3)
    lda.save('lda_model')
