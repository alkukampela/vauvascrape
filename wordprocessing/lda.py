import pgdb
from gensim.corpora import Dictionary, MmCorpus
from gensim.models.ldamulticore import LdaMulticore
from pre_processing import get_rows
from tqdm import tqdm
import pyLDAvis
import pyLDAvis.gensim

_NORMALIZED_TOPIC_QUERY = 'SELECT * FROM normalized_topics'

def get_normalized_topics(db):
    for topic in tqdm(get_rows(db, _NORMALIZED_TOPIC_QUERY)):
        yield topic.content

def build_dictionary(normalized_topic_stream):
    dictionary = Dictionary(normalized_topic_stream)
    dictionary.filter_extremes(no_below=3, no_above=0.4)
    dictionary.compactify()
    return dictionary

def get_topic_bows(dictionary, normalized_topic_stream):
    for topic in normalized_topic_stream:
        yield dictionary.doc2bow(topic)

def build_corpus(normalized_topic_stream, dictionary, fname):
    topic_bow_generator = get_topic_bows(dictionary, normalized_topic_stream)
    MmCorpus.serialize(fname, topic_bow_generator)
    corpus = MmCorpus(fname)
    return corpus

def train_lda(corpus, dictionary):
    return LdaMulticore(corpus, num_topics=50, id2word=dictionary, workers=3)

def prepare_ldavis(lda, corpus, dictionary):
    return pyLDAvis.gensim.prepare(lda, corpus, dictionary)

if __name__ == '__main__':
    with pgdb.connect(database='vauvafi') as db:
        dictionary = build_dictionary(get_normalized_topics(db))
        dictionary.save('dictionary')
        corpus = build_corpus(
            get_normalized_topics(db),
            dictionary,
            'corpus_mm')

    lda = train_lda(corpus, dictionary)
    lda.save('lda_model')
    for topic in range(10):
        print('Topic {} words\n----------------'.format(topic))
        for term, frequency in lda.show_topic(topic, topn=10):
            print('{:20} {:.3f}'.format(term, frequency))
    ldavis_data = prepare_ldavis(lda, corpus, dictionary)
    pyLDAvis.show(ldavis_data)