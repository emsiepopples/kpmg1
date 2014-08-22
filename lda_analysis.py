#!/usr/env/python

import logging, gensim, bz2
import pdb
    
    
def main():
    
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
    
    # load id->word mapping (the dictionary), one of the results of step 2 above
    id2word = gensim.corpora.Dictionary.load_from_text('dictionary_words.txt')
    # load corpus iterator
    mm = gensim.corpora.MmCorpus('corpus.mm')
    # mm = gensim.corpora.MmCorpus(bz2.BZ2File('wiki_en_tfidf.mm.bz2')) # use this if you compressed the TFIDF output
    
    print(mm)
    
    #This is the pure gensim version. It uses variational Bayes
    #lda = gensim.models.ldamodel.LdaModel(corpus=mm, id2word=id2word, num_topics=100, update_every=1, chunksize=5000, passes=5)
    
    pdb.set_trace()
    
    
    lda_mallet = gensim.models.mallet('/Users/emma/mallet/bin/mallet', corpus=mm, id2word=id2word, num_topics=100, update_every=1, chunksize=5000, passes=5)

    
if __name__ == "__main__":

    main()