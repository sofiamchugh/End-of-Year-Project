import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.user_agent import UserAgent
class Node:
    def __init__(self, url, parent):
        self.parent = parent
        self.url = url
        self.children = []
    def add_child(self,child):
        self.children.append(child)
    def node_as_json(self, links, crawl_delay):
        """Converts node object into JSON dict for uploading to blob storage in Azure."""
        node_data = {
            "url": self.url,
            "parent": self.parent,
            "links": links  ,
            "crawl_delay": crawl_delay
        }
        return node_data
    def node_from_json(self, node_data, app):
        """Uses JSON dict to populate node information, including adding children."""
        if node_data: 
            self.url = node_data["url"]
            if node_data["parent"] == "None":
                self.parent = None
            else:
                self.parent = node_data["parent"]
            links = node_data["links"]
            for link in links:
                with app.lock:
                    if link not in app.seen: #only add previously unseen links to children
                        if app.rules.url_is_allowed(link): #check for exclusion in robots.txt
                            app.seen.add(link)
                            child = Node(link, self.url)
                            self.add_child(child)
                        else:
                            print(f"{link} is not allowed")
            print(f"added {len(self.children)} nodes")
        else:
            print("Node data not found. ")
