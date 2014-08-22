__author__ = 'elenagr'

import os
import time
import MySQLdb as mdb
from gensim import corpora
import enron
import create_dic as dic
import argparse
import stemming as stem
import enron


class MyCorpus(object):
     def __init__(self, dict_name,size=None):
        self.dict_name = dict_name
        self.dictionary=corpora.Dictionary.load_from_text(dict_name)
        self.connection = mdb.connect('localhost', 'kpmg1', 's2ds', 'enron')
        self.cur = self.connection.cursor()
        if size == None:
            self.cur.execute("select id from emails order by id desc limit 1;")
            res = self.cur.fetchall()
            tmp = [int(col) for row in res for col in row]
            self.size=tmp[0]
        else:
            self.size = size

     def __iter__(self):
        try:
            for id in range(1,self.size):
                self.cur.execute(" select text from emails where id = {0} ".format(id))
                tmp = self.cur.fetchall()
                text_stem = stem.stemmingString(tmp[0][0], id, stopwords=False)
                yield self.dictionary.doc2bow(text_stem, allow_update=False)
        finally:
            self.connection.close()


parser = argparse.ArgumentParser(description="Generating a corpus")
parser.add_argument("--raw", help="Use raw dictionary (don't apply customization)",default=False, action='store_true')
parser.add_argument("--stopwords", help="Add stopwords",default=False, action='store_true')
parser.add_argument("--minfreq", help="Create a dictionary using the whole set of emails",default=0,required = False, type=int)
parser.add_argument('--maxfreq', help = 'Number of emails used to build the dictionary',
                    default=300000,required = False, type=int)

def main():

    args = parser.parse_args()
    min=args.minfreq
    max=args.maxfreq
    stopws=args.stopwords
    raw=args.raw

    if raw == True:
        print "Creating corpus..."
        corpus=MyCorpus("dictionary_freq.txt")
        corpora.mmcorpus.MmCorpus.serialize('corpus.mm', corpus)
    elif raw == False:
        print "Customizing dictionary..."
        dic.customizeDic(min,max,stopwords=stopws)
        print "Creating corpus..."
        corpus=MyCorpus("new_dic_freq.txt")
        filename="corpus_min{0}_max{1}_stopwds{2}.mm".format(min,max,stopws)
        corpora.mmcorpus.MmCorpus.serialize(filename, corpus)

    return corpus

if __name__ == '__main__':
    main()
