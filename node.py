
from bs4 import BeautifulSoup
class Node:
    def __init__(self, url, parent):
        self.url = url
        self.parent = parent
        self.relevance = 0
        self.isAnimated = True
        self.children = []
        nodes.append(self)
        print("node created")
        
    def init_complete(self):
        self.isAnimated = False
    def add_child(self,child):
        self.children.append(child)
    def set_relevance(self,relevance):
        self.relevance = relevance
    def set_coords(self, x, y):
        self.x = x
        self.y = y
nodes = []