import node
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import urllib.request
from selenium.webdriver.chrome.options import Options
from threading import Thread
def getRelevance():
    print("hi")

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
        if i == url:
            return True
    return False

#accesses the webpage and populates the node struct with relevant information
#repeats recursively for each new link it finds
"""
def gather(self, firstNode, keywords):
    print("gathering...")
    def worker():
        try:
            global root_url
            root_url = firstNode.url.split(".com")[0] + ".com"

            chrome_options = Options()
            chrome_options.add_argument("--headless")  # Run Chrome in headless mode
            driver = webdriver.Chrome(options=chrome_options)

            driver.get(firstNode.url)
            time.sleep(3) 
            text = driver.page_source
            soup = BeautifulSoup(text, 'html.parser')
            links = findLinks(soup)
         #firstNode.relevance = getRelevance(firstNode.url)
            firstNode.init_complete()
            print("finished finding links")
            print("adding links as children")
            for linkFound in links:
                if(linkExists(linkFound)==False):
                    print("\n new child ", linkFound)
                    child = node.Node(linkFound, firstNode)
                    self.data_queue.put(child)
                    firstNode.add_child(child)
              #  gather(child, keywords)
            print("finished adding children")
            print("first node has %i children", len(firstNode.children))
            print("total nodes: %i", len(node.nodes))
        except Exception as e:
            print(f"Gathering error{e}")
    thread = Thread(target=worker)
    thread.daemon = True
    thread.start()
    """