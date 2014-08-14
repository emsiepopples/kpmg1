__author__ = 'elenagr'

import logging
import re
import argparse
import math
import random
import MySQLdb as mdb

import nltk
from nltk import word_tokenize
from nltk.collocations import TrigramCollocationFinder
from nltk.metrics import BigramAssocMeasures, TrigramAssocMeasures

import gensim
from gensim.parsing.preprocessing import STOPWORDS

logging.basicConfig(format='%(levelname)s : %(message)s', level=logging.INFO)
logging.root.level = logging.INFO  # ipython sometimes messes up the logging setup; restore

parser = argparse.ArgumentParser(description="Generating a dictionary of stopwords")
parser.add_argument("--sample",help="Size of sample in percentage", required=True,type=float)
parser.add_argument("--min_freq",help="Minimal frequency of ocurrence to be considered",required=True,type=int)
parser.add_argument("--max_col",help="Maximal number of collocations to be found",required=True,type=int)
parser.add_argument("--word_len",help="Minimal word length to be considered",required=True,type=int)

def best_ngrams(words, top_n=1000, min_freq=100):

    """
    This function has been extracted from a tutorial given in Europython 2014 about
    topic modelling given by Radim Rehurek

    Extract `top_n` most salient collocations (bigrams and trigrams),
    from a stream of words. Ignore collocations with frequency
    lower than `min_freq`.

    This fnc uses NLTK for the collocation detection itself -- not very scalable!

    Return the detected ngrams as compiled regular expressions, for their faster
    detection later on.

    """
    tcf = TrigramCollocationFinder.from_words(words)
    tcf.apply_freq_filter(min_freq)
    trigrams = [' '.join(w) for w in tcf.nbest(TrigramAssocMeasures.chi_sq, top_n)]
    logging.info("%i trigrams found: %s..." % (len(trigrams), trigrams[:20]))

    bcf = tcf.bigram_finder()
    bcf.apply_freq_filter(min_freq)
    bigrams = [' '.join(w) for w in bcf.nbest(BigramAssocMeasures.pmi, top_n)]
    logging.info("%i bigrams found: %s..." % (len(bigrams), bigrams[:20]))

    # Write collocations to two files to be read by the preprocess program
    f1 = open('bigrams.txt', 'w')
    f1.writelines(["%s\n" % item  for item in bigrams])
    f1.close()

    f2 = open('trigrams.txt', 'w')
    f2.writelines(["%s\n" % item  for item in trigrams])
    f2.close()

    pat_gram2 = re.compile('(%s)' % '|'.join(bigrams), re.UNICODE)
    pat_gram3 = re.compile('(%s)' % '|'.join(trigrams), re.UNICODE)

    return pat_gram2, pat_gram3

def main():
    args = parser.parse_args()
    N = args.sample
    freq = args.min_freq
    n_col = args.max_col
    min_len = args.word_len

    print ("Sample Size: {0}*total").format(N)
    print ("Minimum frequency: {0}").format(freq)
    print ("Maximun number of collocations: {0}").format(n_col)
    print ("Minimum word length: {0}").format(min_len)

    # Open the connection to the DB
    connection = mdb.connect('localhost', 'kpmg1', 's2ds','enron')
    cur=connection.cursor()


    # In our case the IDs are ordered by entry. Otherwise you could do: cur.execute("SELECT COUNT(*) FROM emails;")
    # The last ID number gives us the number of rows of the table.
    cur.execute("select id from emails order by id desc limit 1;")
    res = cur.fetchall()
    size=[int(col) for row in res for col in row]


    # We generate a random sample of the entries.
    sample=random.sample(range(size[0]),int(math.floor(size[0]*N)))

    texts=[]

    # We query the emails in the sample and store them in a list
    for id in sample:
        cur.execute(" select text from emails where id = {0} ".format(id))
        tmp=cur.fetchall()
        texts.append(tmp[0][0])

    # Join all the text into a string to be able to count the frequency of ocurrence
    raw=" ".join(texts)

    # Additional stopwords found in the results
    add_stopwords=['http','https','www','com','href','nbsp']

    # Tokenize the text eliminating non alphanumeric characters, stopwords and also words of length <= 3
    tokens=[word for word in gensim.utils.tokenize(raw, lower=True)
                if word not in STOPWORDS and len(word) > min_len if word not in add_stopwords]

    # Find the collocations in our text based on the frequency they appear.
    # Here is where all the magic happens :-)
    best_ngrams(tokens, top_n=n_col, min_freq=freq)

    # Naive version of the code
    #text = nltk.Text(tokens)
    #coll=text.collocations()

    # Close all cursors
    connection.close()

    return


if __name__ == "__main__":
    main()

