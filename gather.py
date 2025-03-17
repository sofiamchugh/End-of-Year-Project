import node
import re
import validators
from bs4 import BeautifulSoup
import numpy as np
from sentence_transformers import SentenceTransformer, util
from rank_bm25 import BM25Okapi
from sklearn.preprocessing import MinMaxScaler
import nltk
from nltk.tokenize import sent_tokenize
nltk.download('punkt')

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

def get_bm25_score(text, keywords):
    try:
        tokenized_text = [nltk.word_tokenize(sent) for sent in text]
        tokenized_keywords = [nltk.word_tokenize(keyword.lower()) for keyword in keywords]
        flattened_keywords = [word for sublist in tokenized_keywords for word in sublist]

        print("Tokenized Text (First 100 words):", tokenized_text[0][:200])
        print("Flattened Keywords:", flattened_keywords)
        common_words = set(flattened_keywords) & set(tokenized_text[0])
        print("Common Words:", common_words)

        if not any(common_words):
                   return 0
        if not any(tokenized_text):
            raise ValueError("Tokenized text is empty.")
    
        bm25 = BM25Okapi(tokenized_text)
        bm25_scores = bm25.get_scores(flattened_keywords)
        return bm25_scores[0]
    
    except Exception as e:
        raise ValueError(f"Error in computing BM25 score")
    
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

    
def getRelevance(soup, keywords):
    bm25_weight = 0.5   
    sbert_weight = 0.5
    bm25_score = 0
    sbert_score = 0
    try: 
        web_text = strainSoup(soup)
        if not web_text:
            raise ValueError("Your strainer is broken")
    
        bm25_score = get_bm25_score(web_text, keywords)
        print(bm25_score)
        sbert_score = get_sbert_score(web_text, keywords)
        scores = np.array([[bm25_score, sbert_score]])

        if bm25_score is None:
            raise ValueError("BM25 score error")
        
        if sbert_score is None:
            raise ValueError("SBERT score error")
        
        print(f"bm25 score: {bm25_score} \n sbert score: {sbert_score}\n")
       
        try: 
            # Normalize scores 
            scaler = MinMaxScaler()
            normalized_scores = scaler.fit_transform(scores.reshape(-1, 1)).flatten()
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
