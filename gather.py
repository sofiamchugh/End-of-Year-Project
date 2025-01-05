import node
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import urllib.request
from selenium.webdriver.chrome.options import Options
def getRelevance():
    print("hi")

def findLinks(soup):
    print("\nfinding links")
    print(root_url)
    links = []
    for link in soup.find_all('a'):
        l = link.get('href')
        if l:
            if (l[0] == '/'):
                l = root_url + l
            if (l[0]== '#'):
                print("not a link")
                continue
            print(l)
            links.append(l)
    
    return links

def linkExists(url):
    print("\nchecking link")
    for i in node.nodes:
        #print(i.url)
        if (i.url == url):
            return True
    return False

#accesses the webpage and populates the node struct with relevant information
#repeats recursively for each new link it finds
def gather(firstNode, keywords):
    print("gathering...")
    try:
        global root_url
        root_url = firstNode.url.split(".com")[0] + ".com"
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run Chrome in headless mode
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(firstNode.url)
        time.sleep(3)
        text = driver.page_source
        #text = urllib.request.urlopen(firstNode.url).read().decode('utf-8')
        soup = BeautifulSoup(text, 'html.parser')
        with open("file.txt", "w", encoding = "utf-8") as f:
            f.write(soup.prettify())
        links = findLinks(soup)
    #firstNode.relevance = getRelevance(firstNode.url)
        firstNode.init_complete()
        print("finished finding links")
        print("adding links as children")
        for linkFound in links:
            if(linkExists(linkFound)==False):
                print("\n new child ", linkFound)
                child = node.Node(linkFound, firstNode)
                firstNode.add_child(child)
              #  gather(child, keywords)
        print("finished adding children")
        print("first node has %i children", len(firstNode.children))
        print("total nodes: %i", len(node.nodes))
    except Exception as e:
        print(f"Gathering error{e}")