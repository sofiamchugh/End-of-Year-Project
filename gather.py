import node
from bs4 import BeautifulSoup
import urllib.request
def getRelevance():
    print("hi")

def findLinks(soup):
    for link in soup.find_all('a'):
        print(link.get('href'))

def linkExists(url):
    return True
#accesses the webpage and populates the node struct with relevant information
#repeats recursively for each new link it finds
def gather(firstNode, keywords):
    print("gathering...")
    text = urllib.request.urlopen(firstNode.url).read()
    soup = BeautifulSoup(text, 'html.parser')
    links = findLinks(soup)
    """
    firstNode.relevance = getRelevance(firstNode.url)
    firstNode.initComplete()
    links = firstNode.findLinks(soup)
    for linkFound in links:
        if(linkExists(linkFound)==False):
            child = node.Node(linkFound, firstNode)
            firstNode.add_child(child)
            gather(child, keywords)
    """