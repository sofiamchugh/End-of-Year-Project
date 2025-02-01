
from bs4 import BeautifulSoup
class Node:
    def __init__(self, url, parent):
        self.url = url
        self.parent = parent
        self.relevance = 0
        self.children = []
    def add_child(self,child):
        self.children.append(child)
    def set_relevance(self,relevance):
        self.relevance = relevance
    def set_coords(self, x, y):
        self.x = x
        self.y = y
    def print_me(self):
        return self.url + ": " + self.relevance