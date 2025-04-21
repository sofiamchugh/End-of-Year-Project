from user_agent import UserAgent
class Node:
    def __init__(self, url, parent):
        self.parent = parent
        self.relevance = 0
        self.url = url
        self.children = []
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
    def node_from_json(self, node_data, seen, lock, rules):
        if node_data: 
            self.url = node_data["url"]
            if node_data["parent"] == "None":
                self.parent = None
            else:
                self.parent = node_data["parent"]
            self.relevance = node_data["relevance"]
            links = node_data["links"]
            for link in links:
                with lock:
                    if link not in seen:
                        if rules.url_is_allowed(link):
                            seen.add(link)
                            child = Node(link, self.url)
                            self.add_child(child)
                        else:
                            print(f"{link} is not allowed")
        else:
            print("Node data not found. ")
