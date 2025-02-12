import node
import re
import validators
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer("all-MiniLM-L6-v2")

def strainSoup(soup):
    # Remove script elements and embedded content
    for tag in soup(["script", "style", "iframe"]):
        tag.decompose()

    # Remove elements described as ads/sponsored content
    for ad in soup.find_all(["div", "ins"], class_=lambda x: x and ("ad" in x.lower() or "sponsored" in x.lower())):
        ad.decompose()

    return soup

def UrlIsValid(url):
    if not validators.url(url):
        return False
    else:
        return True
    
def getRelevance(soup, keywords):
    print(f"keywords = {keywords}")
    web_text = soup.get_text(separator=" ")  
    #get all text from soup
    web_text = re.sub(r'\s+', ' ', web_text).strip()  
    #remove newlines and extra spaces
    
    web_embedding = model.encode(web_text, convert_to_tensor=True)
    #SBERT vector for the webpage text
    keyword_embedding = model.encode(" ".join(keywords), convert_to_tensor=True)
    #SBERT vector for the keywords
    similarity_score = util.pytorch_cos_sim(web_embedding, keyword_embedding).item()
    #compute cosine similarity
    print(f"\nsimilarity score {similarity_score}")
    return similarity_score

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
