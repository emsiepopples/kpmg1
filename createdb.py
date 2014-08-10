#/usr/env/python

"""Code to create the test_db from the Enron email data"""

import email
import os, sys
import argparse
import MySQLdb as mdb
import __future__
import re
import pdb
import datetime

parser = argparse.ArgumentParser("Create database from email files")
parser.add_argument("startdir", type = str, help='Starting place for directory tree')


def createDB():

    """Creates connection to mysql and creates the DB in standard form"""

    #connect to local server with following usernames

    connection = mdb.connect('localhost', 'kpmg1', 's2ds')
    cursor=connection.cursor()


    #DB schema. We can amend this however we want as we go.
    #I've written everything as 1 table as that seemed the easiest, but
    # if we want to create more tables that's easy.  Just do:
    # TABLES['newname']= and fill in the new columns in the same format
    #I've added a local file location to be helpful during debugging/creation

    DB_NAME='enron'
    TABLES={}
    TABLES['emails'] = (\
        "CREATE TABLE `emails` (\
          `id` INT NOT NULL AUTO_INCREMENT,\
          `sender` varchar(100) NOT NULL,\
          `to` text(5000) NOT NULL,\
          `subject` varchar(500), \
          `date` datetime NOT NULL,\
          `cc` text(5000),\
          `bcc` text(5000),\
          `rawtext` text(30000) NOT NULL,\
          `text` text(30000) NOT NULL,\
          `fileloc` varchar(500) NOT NULL,\
          PRIMARY KEY (id)\
        ) ENGINE=InnoDB;")

    #try to create. If not raise exception and exit

    try:

        cursor.execute("CREATE DATABASE {0} DEFAULT CHARACTER SET 'utf8'".format(DB_NAME))

    except mdb.Error as err:

        print ("Failed creating database",format(err))
        return

    #Try to create table


    #can iterate over the table names and the associated query

    for name,ddl in TABLES.iteritems():

        #must tell it which db to use first

        cursor.execute('USE `enron`;')


        try:

            print ("Creating table {0}: \n".format(name))
            cursor.execute(ddl)

        except mdb.Error, err:

            if int(str(err).split()[0][1:5]) == 1050:

                print ("Table {0} already exists".format(name))
            else:
                print (err)


    if connection:
        connection.close()

    #Close the empty database if it is created correctly

    return


def deleteTable(cur, tablename):

    cur.execute("""DROP TABLE IF EXISTS {0}""".format(tablename))
    return

def deleteDB(cur, dbname):

    cur.execute("""DROP DATABASE IF EXISTS {0}""".format(dbname))
    return

def connectDB(db):

    connection = mdb.connect('localhost', 'kpmg1', 's2ds', db)
    cursor=connection.cursor()

    return (connection,cursor)


def formatDate(datestring):

    #this is probably specific to this email system I don't know

    datestring = datestring.split()

    #got a weird error where the year in the email is listed as 0001 so add 1900
    #to enable python to deal with it.

    if (int(datestring[3]) < 1900): datestring[3] = str(int(datestring[3])+1900)
    rearrange = '{0} {1} {2} {3}'.format(datestring[1], datestring[2].upper(), datestring[3], datestring[4])
    
    

    dateobj = datetime.datetime.strptime(rearrange, '%d %b %Y %H:%M:%S')

    formatdate = datetime.datetime.strftime(dateobj, '%Y-%m-%d %H:%M:%S')
    return formatdate


def addDBEntry(connect,cur, tablename, email, filepath):


    print '**************************'
    print filepath

    sender = email['From']
    to = email['To']

    if (to != None): 

        to = re.sub('"', '', to)
        to = re.sub("(E-mail)", "", to)
        to = re.sub('<', '', to)
        to = re.sub('>', '', to)

    else:
        to = 'unknown'


    cc = email['X-cc']

    if (cc != None):
        cc = re.sub('"', '', cc)
        cc = re.sub('(E-mail)', '', cc)
        cc = re.sub('<', '', cc)
        cc = re.sub('>', '', cc)

    else:
        cc = ''



    bcc=email['X-bcc']
    
    if (bcc != None):
        bcc = re.sub('"', '', bcc)
        bcc = re.sub('(E-mail)', '', bcc)
        bcc = re.sub('<', '', bcc)
        bcc = re.sub('>', '', bcc)

    else:
        bcc = ''

    subject=email['Subject']
    subject = re.sub('"', '', subject)

    date = email['Date']
  
    formated_date = formatDate(date)

    localfile = filepath
    rawtext = email.get_payload()

    #convert any " to '

    rawtext = re.sub(r'"', "'", rawtext)
    #escape any apostrophes, 

    rawtext = re.sub(r"'", "\'", rawtext)



    cleantext = cleanMessage(rawtext)

    #now create the syntax to add an entry to the db

    query = """INSERT INTO {0} (`sender`, `to`, `date`,`subject`,  `cc`, `bcc`, \
        `rawtext`, `text`, `fileloc`) VALUES ("{1}", "{2}", "{3}", "{4}", "{5}", "{6}", "{7}", \
        "{8}","{9}");""".format(tablename, sender, to, formated_date, subject, cc, bcc,\
         rawtext,cleantext,filepath)

    #print query

    logfile = open('logfile', 'a')

    try:

        cur.execute(query)
        connect.commit()

        print 'Added file: {0}'.format(filepath)

    except mdb.Error, err:

        print err
        logfile.write("Error {0} File {1}\n".format(err, filepath))
        return


    #just run some if loops to check length of fields to check the fields are setup correctly
    #we can delete this later



    if len(rawtext)>19900: logfile.write('Raw text too long {0}: {1}\n'.format(len(rawtext),filepath))
    if len(cleantext)>19900: logfile.write('Clean text too long {0}: {1}\n'.format(len(cleantext),filepath))
    if len(to)>1000: logfile.write('To too long {0}: {1}\n'.format(len(to), filepath))
    if len(sender)>100: logfile.write('From too long {0}: {1}\n'.format(len(sender), filepath))
    if len(cc)>1000: logfile.write('CC too long {0}: {1}\n'.format(len(cc), filepath))
    if len(bcc)>1000: logfile.write('BCC too long {0}: {1}\n'.format(len(bcc), filepath))
    if len(subject)>200: logfile.write('Subject too long {0}: {1}\n'.format(len(subject),filepath))

    logfile.close()
    return

def cleanMessage(message):

    #remove \n

    clean1 = re.sub(r'\n', ' ', message)

    #remove - which repeat >=3 times

    clean2 = re.sub(r'-{3,}', '', clean1)

    #remove leading/trailing whitespace

    clean2 = clean2.strip()

    #locate multiple email chains and cut on first occurance of Original Message
    #this creates a match object

    match = re.search(r'Original Message', clean2)

    #match.start is the index of the first occurance of the search string. Want the 
    #message from the beginning to that point

    if (match==None):
        return clean2
    else:

        clean3 = clean2[:match.start()]

        return clean3





def main():
 
    args = parser.parse_args()

    #First thing: create the DB

    createDB()
    connection, cursor = connectDB('enron')




    #start directory is unique for each person

    startdir = args.startdir

    found = []

    for dir,subdir,files in os.walk(startdir):

        for ff in files:

            found.append(os.path.join(dir,ff))

    for message in found:

        #create email object from the file list.  Process each one then send to DB

        with open(message, 'r') as efile:
            msg = email.message_from_file(efile)
        

        addDBEntry(connection,cursor, 'emails', msg, message)

    connection.close()




if __name__ == '__main__':
    main()
