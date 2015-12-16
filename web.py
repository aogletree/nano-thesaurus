"""
Web Scraper 

This is a module that visits a specific website, downloads all the paper abstracts it finds, and outputs a file 
with the word count of all meaningful words.
"""

import mechanize   #Emulates a browser to interact with web pages
import operator    #For sorting the words
import re          #Regular expression operations
import time
import urllib2
import datetime
from itertools import ifilter
from collections import Counter, defaultdict
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup
import matplotlib.pylab as plt
import pandas as pd
import numpy as np
import bibtexparser

pd.set_option('mode.chained_assignment','warn')

%matplotlib inline

OAI = "{http://www.openarchives.org/OAI/2.0/}"
ARXIV = "{http://arxiv.org/OAI/arXiv/}"

def harvest(arxiv="physics:cond-mat"):
    df = pd.DataFrame(columns=("title", "abstract", "categories", "created", "id", "doi"))
    base_url = "http://export.arxiv.org/oai2?verb=ListRecords&"
    url = (base_url +
           "from=2010-01-01&until=2014-12-31&" +
           "metadataPrefix=arXiv&set=%s"%arxiv)
    
    while True:
        print "fetching", url
        try:
            response = urllib2.urlopen(url)
            
        except urllib2.HTTPError, e:
            if e.code == 503:
                to = int(e.hdrs.get("retry-after", 30))
                print "Got 503. Retrying after {0:d} seconds.".format(to)

                time.sleep(to)
                continue
                
            else:
                raise
            
        xml = response.read()

        root = ET.fromstring(xml)

        for record in root.find(OAI+'ListRecords').findall(OAI+"record"):
            arxiv_id = record.find(OAI+'header').find(OAI+'identifier')
            meta = record.find(OAI+'metadata')
            info = meta.find(ARXIV+"arXiv")
            created = info.find(ARXIV+"created").text
            created = datetime.datetime.strptime(created, "%Y-%m-%d")
            categories = info.find(ARXIV+"categories").text

            # if there is more than one DOI use the first one
            # often the second one (if it exists at all) refers
            # to an eratum or similar
            doi = info.find(ARXIV+"doi")
            if doi is not None:
                doi = doi.text.split()[0]
                
            contents = {'title': info.find(ARXIV+"title").text,
                        'id': info.find(ARXIV+"id").text,#arxiv_id.text[4:],
                        'abstract': info.find(ARXIV+"abstract").text.strip(),
                        'created': created,
                        'categories': categories.split(),
                        'doi': doi,
                        }

            df = df.append(contents, ignore_index=True)

        # The list of articles returned by the API comes in chunks of
        # 1000 articles. The presence of a resumptionToken tells us that
        # there is more to be fetched.
        token = root.find(OAI+'ListRecords').find(OAI+"resumptionToken")
        if token is None or token.text is None:
            break

        else:
            url = base_url + "resumptionToken=%s"%(token.text)
            
    return df

df = harvest()

#Store the data locally so we don't have to scrape it again

store = pd.HDFStore("/Users/adrianogletree/Desktop.h5")
#store['df'] = df
#df = store['df']
store.close()

#Word counts

word_bag = " ".join(df.abstract.apply(lambda t: t.lower()))

Counter(word_bag.split()).most_common(n=10)

#Remove stopwords and basic mathematical symbols
from nltk.corpus import stopwords

stops = [word for word in stopwords.words('english')]
stops += ["=", "->"]
words = filter(lambda w: w not in stops,
               word_bag.split())
top_twenty = Counter(words).most_common(n=20)

bar_chart(top_twenty)

#Stemming
import nltk.stem as stem

porter = stem.PorterStemmer()
for w in ("measurement", "measurements", "measured", "measure"):
    print w, "->", porter.stem(w)

word_stems = map(lambda w: (porter.stem(w),w), words)
stem2words = defaultdict(set)
for stem, word in word_stems:
    stem2words[stem].add(word)

top_twenty = Counter(w[0] for w in word_stems).most_common(n=20)

bar_chart(top_twenty)

# list all words which correspond to each top twenty stem
for stem,count in top_twenty:
    print stem, "<-", ", ".join(stem2words[stem])
