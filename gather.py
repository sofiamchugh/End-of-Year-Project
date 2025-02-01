import node
import re
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from nltk.corpus import wordnet

"""def getSynonyms(word):
    synonyms = set()
    for syn in wordnet.synsets(word):
        for lemma in syn.lemmas():
            synonyms.add(lemma.name().replace("_", " "))
    return list(synonyms)
"""
def getRelevance(soup, keywords):
    """keywordsExpanded = []
    for word in keywords:
        keywordsExpanded.append(getSynonyms(word))

    web_text = soup.get_text(separator=" ")  
    #get all text from soup
    web_text = re.sub(r'\s+', ' ', web_text).strip()  
    #remove newlines and extra spaces
   # vectorizer = TfidfVectorizer(stop_words='english')
    #remove stop words"""

    """documents = [web_text, " ".join(keywords)]  
    tfidf_matrix = vectorizer.fit_transform(documents)

    similarity_score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])
    return similarity_score[0][0]  # Return the cosine similarity score"""
    return 0


def findLinks(soup, homepage_url):
    links = []
    for link in soup.find_all('a'):
        l = link.get('href')
        if l:
            if (l[0] == '/'):
                l = homepage_url + l
            if(homepage_url not in l):
                #this accounts for:
                #javascript:void() links or similar
                #URLs that take us outside of the website
                continue
            links.append(l)
    
    return links

def linkExists(url, seen):
    for i in seen:
        if url in i:
            return True
    return False
