class Node:
    def __init__(self, url, parent):
        self.parent = parent
        self.relevance = 0
        self.url = url
        self.children = []
        self.content = None
    def add_child(self,child):
        self.children.append(child)
    def set_relevance(self,relevance):
        self.relevance = relevance
    def set_content(self, content):
        self.content = content
    def set_coords(self, x, y):
        self.x = x
        self.y = y
    def node_as_json(self, links, crawl_delay):
        node_data = {
            "url": self.url,
            "parent": self.parent,
            "relevance": self.relevance, 
            "links": links  ,
            "crawl_delay": crawl_delay
        }
        return node_data
