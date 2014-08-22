#/usr/env/python

"""Code to perform the TF-IDF reweighting of the corpus"""

from gensim import corpora, models
import time


# Make sure stopword removal has been disabled in create_dic (and the dictionary has been re-created) before doing this as otherwise the TF (raw co-occurence matrix) corpus should be used!


def main():
 
    start_time = time.time()

    # Load the raw count (TF) corpus
    corpus = corpora.MmCorpus('corpus.mm')

    # Define a model (which is the gensim name for a transformation) based on this corpus which performs the TFIDF transformation/calculation
    tfidf = models.TfidfModel(corpus)

    # Apply it to the input corpus
    new_corpus = tfidf[corpus]

    # Save the new corpus
    corpora.mmcorpus.MmCorpus.serialize('corpus_tfidf.mm', new_corpus)

    # This command displays the corpus. Or run a print loop over the elements of the corpus. For debugging purposes.
    #print(list(new_corpus))

    end_time=time.time()
    time_taken = end_time - start_time

    print 'Time taken to perform TF-IDF reweighting: {0}'.format(time_taken)


if __name__ == '__main__':
    main()
