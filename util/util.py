import re
import hashlib
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlunparse, urljoin

def clean_url(url):
    """Processes URL to match blob naming format."""
    clean_url = url.replace("https://", "").replace("http://", "").replace("/", "_").replace(".", "-")
    return clean_url

def url_as_blob_name(url):
    return f"{clean_url(url)}.html" 


def make_safe_task_id(url: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_-]", "_", url)
    if len(safe) > 58:  # 64 - len("task-") = 59
        # Hash the original to keep uniqueness
        hash_suffix = hashlib.md5(url.encode()).hexdigest()[:6]
        safe = f"{safe[:52]}_{hash_suffix}"
    return f"task-{safe}"

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

def find_links(soup, url):      
    links = []     
    for link in soup.find_all('a'):         
        l = link.get('href')         
        filetypes = ['.pdf', '.doc', '.xlsx', '.png', '.jpeg', '.jpg']         
        if l:             
            l = urljoin(url, l)             
            if '#' in l:                 
                continue             
            if any(ext in l.lower() for ext in filetypes):                 
                continue             
            l = process_url(l)             
            if get_base_homepage(l) != get_base_homepage(url):                 
                continue             
            links.append(l)     
    return links
