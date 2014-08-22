__author__ = 'elenagr'

import os
import time
import MySQLdb as mdb
from gensim import corpora
import argparse
import enron
import stemming as stem
import re

from collections import Counter



def customizeDic(minfreq, maxfreq, stopwords=False):

    """
    This function loads an existing dictionary called "dictionary_freq.txt" and reduces its
    vocabulary by ignoring the stopwords if wanted and/or least frequent words (given by the lowest
     frequency parameter freq) and/or
    :param freq: lowest number of documents where the word was found
    :return: returns the new reduced dictionary
    """

    # Load dictionary
    dic=corpora.Dictionary.load_from_text("dictionary_freq.txt")

    # Create a list with the words that appear in less than N documents given by freq
    minfreq_ids = [tokenid for tokenid, docfreq in dic.dfs.iteritems() if docfreq < minfreq]
    maxfreq_ids = [tokenid for tokenid, docfreq in dic.dfs.iteritems() if docfreq > maxfreq]



    if stopwords == True:
        # Load the stopwords list
        stoplist = enron.getCustomStopwords()
        # Create a list with the ids of the words in the stopwords list
        stop_ids = [dic.token2id[stopword] for stopword in stoplist
                    if stopword in dic.token2id]
        dic.filter_tokens(minfreq_ids + maxfreq_ids + stop_ids)
    elif stopwords == False:
        # Eliminate non desired entries in our dictionary
        dic.filter_tokens(minfreq_ids + maxfreq_ids)

    #use re to remove some relics in the database

    myre1 = re.compile(r'(.)\1{2,}\w+')       #repeated character words
    myre2 = re.compile(r'(|\w*)\\[a-z,\\]*')  #backslash words
    myre3 = re.compile(r'[a-z]{20,}')         #words longer than 20 characters

    words1 = [dic.token2id[i] for i in dic.token2id.keys() if myre1.search(i)]
    words2 = [dic.token2id[i] for i in dic.token2id.keys() if myre2.search(i)]
    words3 = [dic.token2id[i] for i in dic.token2id.keys() if myre3.search(i)]

    allwords = list(set(words1+words2+words3))

    dic.filter_tokens(allwords)

    # Assign new ids to the remaining words to adjust for the reduced vocabulary
    dic.compactify()

    # Save the new dictionary for reference
    dic.save_as_text("new_dic_words.txt", sort_by_word=True)
    dic.save_as_text("new_dic_freq.txt", sort_by_word=False)
    
    return dic

def initializeDic(N, stopwords=False):
    """
    This function initialize the dictionary in case there is no any previously saved in disk
    :param N: number of emails to build it (recommended 3)
    :return: returns the dictionary
    """

    print "Initializing dictionary with the first {0} emails \n".format(N-1)

    # Open the connection to the DB
    connection = mdb.connect('localhost', 'kpmg1', 's2ds', 'enron')
    cur = connection.cursor()

    texts = []
    ids = []

    # Query emails for given ids
    for id in range(1, N):
        cur.execute(" select text from emails where id = {0} ".format(id))
        tmp = cur.fetchall()
        texts.append(tmp[0][0])
        ids.append(id)

    texts_id = zip(ids, texts)
    # Apply stemming to the given text
    texts_stem = stem.stemmingListofStrings(texts_id,stopwords=stopwords)
    texts_stem = [text for id, text in texts_stem]

    # Builds a dictionary based on the words found in the given texts
    dictionary = corpora.Dictionary(texts_stem)

    return dictionary


parser = argparse.ArgumentParser(description="Generating a dictionary")
parser.add_argument('-N', '--Ndic', help = 'Number of texts considered for initial dictionary',
                    required = True, type=int)
parser.add_argument('-dic', '--initialize', help='initialize dictionary', default=False, action='store_true')
parser.add_argument('--append', help='append word mapping to existing file', default=False,
                    action='store_true')
parser.add_argument("--stopwords", help="Add stopwords",default=False, action='store_true')
parser.add_argument("--all", help="Create a dictionary using the whole set of emails",default=False, action='store_true')
parser.add_argument('-emails', '--emails', help = 'Number of emails used to build the dictionary',
                    required = False, type=int)

def main():
    """
    This function generates a dictionary (map id<-> word) based on the texts saved in the enron database
    In the file dictionary_freq.txt one can see the word id, the word and the number of emails where that
    particular word appear
    There are two dictionary, one in alphabetic order (dictionary_word.txt) and another one ordered by frequency
    (dictionary_freq.txt)
    It also produces a file map_words.txt with the email id and all the words that appear in each of them.
    A complementary file map_freqs.txt contains the frequency for each of the words of the previous file.

    :return:
    """
    # Read arguments:
    args = parser.parse_args()
    N=args.Ndic
    stopws=args.stopwords
    all=args.all

    start_code = time.time()

    # Remove files which will be generated within this function to avoid appending to an existing file unless
    # there is an argument which explicitly requires append to existing file
    if (args.append == False):
        if os.path.exists("word_replace_dic.csv"):
            os.remove("word_replace_dic.csv")
        if os.path.exists("ngrams_found.csv"):
            os.remove("ngrams_found.csv")

    # Open the connection to the DB
    connection = mdb.connect('localhost', 'kpmg1', 's2ds', 'enron')
    cur = connection.cursor()

    if all == True:
        # In our case the IDs are ordered by entry. Otherwise you could do:
        # cur.execute("SELECT COUNT(*) FROM emails;")
        # The last ID number gives us the number of rows of the table.
        cur.execute("select id from emails order by id desc limit 1;")
        res = cur.fetchall()
        size = [int(col) for row in res for col in row]
        Nemails=size[0]
    elif all == False:
        Nemails=args.emails

    # Initialize the dictionary or reads it from file
    if (args.initialize == True):
        dictionary = initializeDic(N,stopwords=stopws)
    else:
        dictionary = corpora.Dictionary.load_from_text("dictionary_words.txt")

    # Here we go: construct the dictionary and the word-frequency mapping for each email
    for id in range(N, Nemails+1):
        cur.execute(" select text from emails where id = {0} ".format(id))
        tmp = cur.fetchall()
        text_stem = stem.stemmingString(tmp[0][0], id,stopwords=stopws)
        dictionary.doc2bow(text_stem, allow_update=True)
        # Save dictionary once in a while to make sure we don't loose everything if some error ocurrs
        if id % 1000 == 0 or id == (Nemails):
            dictionary.save_as_text("dictionary_words.txt", sort_by_word=True)
            dictionary.save_as_text("dictionary_freq.txt", sort_by_word=False)
            print 'Dictionary saved until id = {0}'.format(id)

    connection.close()

    end_code = time.time()

    codetime = end_code - start_code

    print 'Total time to create dictionary: {0} sec'.format(codetime)


if __name__ == '__main__':
    main()
