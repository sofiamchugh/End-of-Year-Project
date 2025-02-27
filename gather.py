import node
import re
import validators
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
from sklearn.preprocessing import MinMaxScaler
import nltk
nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize

# Load a transformer model for contextual similarity
model = SentenceTransformer("all-MiniLM-L6-v2")

def strainSoup(soup):
    # Remove script elements and embedded content
    for tag in soup(["script", "style", "iframe"]):
        tag.decompose()

    # Remove elements described as ads/sponsored content
    for ad in soup.find_all(["div", "ins"], class_=lambda x: x and ("ad" in x.lower() or "sponsored" in x.lower())):
        ad.decompose()

    web_text = soup.get_text(separator=" ")  
    web_text = re.sub(r'\s+', ' ', web_text).strip()
    web_text = web_text.lower()
    return sent_tokenize(web_text)


def UrlIsValid(url):
    return validators.url(url)
    
def getRelevance(soup, keywords):
    bm25_weight = 0.5   
    sbert_weight = 0.5

    try: 
        web_text = strainSoup(soup)
        if not web_text:
            raise ValueError("Your strainer is broken")
        

        bm25 = BM25Okapi([web_text.split()])  # Index the document

        bm25_scores = bm25.get_scores(keywords)  # BM25 relevance
        bm25_score = bm25_scores[0]
    
        if not bm25_scores:
            raise ValueError("BM25 Score could not be computed")
    
        try:
        # Compute SBERT similarity
            web_embedding = model.encode(web_text, convert_to_tensor=True)
            keyword_embedding = model.encode(" ".join(keywords), convert_to_tensor=True)
            sbert_score = util.pytorch_cos_sim(web_embedding, keyword_embedding).item()
        except Exception as e:
            raise ValueError(f"Error in computing SBERT similarity:{e}")

        try: 
            # Normalize scores 
            scaler = MinMaxScaler()
            scores = np.array([[bm25_score, sbert_score]])
            normalized_scores = scaler.fit_transform(scores)[0]
            print(f"bm25 score: {bm25_score} \n sbert score: {sbert_score}\n")
            # Hybrid Score: Weighted combination of both
            combined_score = (bm25_weight * normalized_scores[0]) + (sbert_weight * normalized_scores[1])
            print(f"score: {combined_score}")
            return combined_score
        except Exception as e:
            raise ValueError(f"Error in normalising and combining scores{e}")

    except Exception as e:
        print(f"Error in relevance function:{e}")


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
