import re
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, urljoin
from sentence_transformers import SentenceTransformer, util
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
nltk.download('punkt_tab')
nltk.download('punkt')

# Load a transformer model for contextual similarity
model = SentenceTransformer("paraphrase-MiniLM-L3-v2")

def process_url(url):
    parsed = urlparse(url)
    parsed = parsed._replace(query="", fragment="")
    netloc = parsed.netloc
    if netloc.startswith('www.'):
        netloc = netloc[4:]
    path = parsed.path.rstrip('/')
    new_url = parsed._replace(netloc=netloc, path=path)
    return urlunparse(new_url)

def get_base_homepage(url):
    netloc = urlparse(url).netloc
    return f"{urlparse(url).scheme}://{netloc}"

def strain_soup(soup):
    """Pre-processing to remove unnecessary content before trying to calculate relevance"""
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
        web_text = re.sub(text, '', web_text, flags=re.IGNORECASE) #Take out text describing bot actions (i.e. copying links)
    web_text = web_text.lower() #make everything lowercase

    return sent_tokenize(web_text) #tokenize before using Sentence-BERT algorithm

def get_sbert_score(text, keywords):
    """This is the primary function used to compute relevance"""
    try:
        # Compute SBERT similarity
            sentence_embedding = model.encode(text, convert_to_tensor=True)
            keyword_embedding = model.encode(" ".join(keywords), convert_to_tensor=True)
            sbert_scores = util.pytorch_cos_sim(sentence_embedding, keyword_embedding)
            return sbert_scores.max().item()
    except Exception as e:
        raise ValueError(f"Error in computing SBERT similarity:{e}")
    
def get_term_frequency(text, keyword):
    """
    Too few keywords make Sentence-BERT less accurate, so we use the more crude method 
    of computing term frequency and approximating what levels of frequency constitute 
    what size of relevance.
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
    """Pre-process the text then decide which algorithm to use and return its output."""
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

def find_links(soup, url):

    links = []
    for link in soup.find_all('a'):
        l = link.get('href')
        filetypes = ['.pdf', '.doc', '.xlsx', '.png', '.jpeg', '.jpg']
        if l:
            l = urljoin(url, l)
            if '#' in l:
                continue
            for type in filetypes:
                if type in l:
                    continue
            l = process_url(l)
            if get_base_homepage(l) != get_base_homepage(url):
                continue
            links.append(l)
    return links
