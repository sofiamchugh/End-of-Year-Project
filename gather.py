import node
import re
import validators
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
nltk.download('punkt_tab')
nltk.download('punkt')

# Load a transformer model for contextual similarity
model = SentenceTransformer("all-MiniLM-L6-v2")

def strain_soup(soup):
    # Remove script elements and embedded content
    for tag in soup(["script", "style", "iframe"]):
        tag.decompose()

    # Remove elements described as ads/sponsored content
    for ad in soup.find_all(["div", "ins"], class_=lambda x: x and ("ad" in x.lower() or "sponsored" in x.lower())):
        ad.decompose()

    unwanted_texts = [
        "copy link", 
        "link copied to clipboard",
        "Copy this link", 
        "Copied to clipboard",
        "Share link",
        "Click to copy",
        "skip to content",
        "skip to footer",
        "link copied"
    ]
    web_text = soup.get_text(separator=" ")  
    web_text = re.sub(r'\s+', ' ', web_text).strip()
    for text in unwanted_texts:
        web_text = re.sub(text, '', web_text, flags=re.IGNORECASE)
    web_text = web_text.lower()

    return sent_tokenize(web_text)

def url_is_valid(url):
    return validators.url(url)

def get_sbert_score(text, keywords):
    try:
        # Compute SBERT similarity
            sentence_embedding = model.encode(text, convert_to_tensor=True)
          #  web_embedding = sentence_embedding.mean(dim=0)
            keyword_embedding = model.encode(" ".join(keywords), convert_to_tensor=True)
            sbert_scores = util.pytorch_cos_sim(sentence_embedding, keyword_embedding)

            return sbert_scores.max().item()
    except Exception as e:
        raise ValueError(f"Error in computing SBERT similarity:{e}")
    
def get_term_frequency(text, keyword):
    """
    S-BERT needs at least two keywords to score texts in a way that suits our purposes,
    so for a single keyword we compute the term frequency.
    The TF is very crudely normalized to return scores similar to the ranges of the S-BERT algorithm.
    """
    try:
        words = [word.lower() for sentence in text for word in word_tokenize(sentence)]
        word_counts = Counter(words)
        keyword_count = word_counts[keyword[0].lower()]
        tf = keyword_count / len(words) * 10 
        print(f"Term frequency = {tf}")
        if tf <= 0.01:
            #low relevance score
            return 0.2
        elif tf >= 0.1:
            #a single keyword being 1 out of 10 words in a text is highly relevant 
            return 0.7
        else:
            #medium relevance score
            return 0.5
    except Exception as e:
        raise ValueError(f"Error in getting term frequency: {e}")

def get_relevance(soup, keywords):
    relevance = 0
    try: 
        web_text = strain_soup(soup)
        if not web_text:
            raise ValueError("Your strainer is broken")
        
        if (len(keywords) == 1) and " " not in keywords[0]:
            relevance = get_term_frequency(web_text, keywords)
        else: 
            relevance = get_sbert_score(web_text, keywords)

    except Exception as e:
        print(f"Error in relevance function:{e}")
    return relevance


def find_links(soup, homepage_url):
    links = []
    for link in soup.find_all('a'):
        l = link.get('href')
        if l:
            if (l[0] == '/'):
                l = homepage_url + l
            if '#' in l:
                continue
            if '.pdf' in l:
                continue
            links.append(l)
    
    return links

def link_exists(url, seen):
    for i in seen:
        if url in i:
            return True
    return False
