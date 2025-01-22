import tkinter as tk
from tkinter import messagebox
from on_start import OnStartFrame
from visuals import GatherFrame
import node
from queue import Queue
from bs4 import BeautifulSoup
from selenium import webdriver
import time
import urllib.request
from selenium.webdriver.chrome.options import Options
import threading
from gather import findLinks, getRelevance, linkExists

class App(tk.Tk):
    def __init__(self):
            super().__init__()
            self.title("Gather")
            self.geometry("800x600")
            self.container = tk.Frame(self)
            self.container.pack(fill="both", expand=True)
            self.frames = {}
            self.data_queue = Queue()
            self.seen = set()
            self.lock = threading.Lock()
            self.init_frames()
    def init_frames(self):
          self.frames["OnStart"] = OnStartFrame(parent=self.container, controller=self, data_queue=self.data_queue, seen=self.seen)
          self.frames["Gathering"] = GatherFrame(parent=self.container, controller=self, data_queue=self.data_queue)
          for frame in self.frames.values():
                frame.grid(row=0, column=0, sticky="nsew")
          self.show_frame("OnStart")
    
    def show_frame(self, frame_name):
          frame = self.frames[frame_name]
          frame.tkraise()
    def gather(self, firstNode, keywords):
        print("gathering...")
        def worker():
            try:
    
                global root_url
                #TO-DO make this work for any namespace
                root_url = firstNode.url.split(".com")[0] + ".com"
                chrome_options = Options()
                chrome_options.add_argument("--headless")  # Run Chrome in headless mode
                driver = webdriver.Chrome(options=chrome_options)
                driver.get(firstNode.url)
                time.sleep(3) 
                text = driver.page_source
                soup = BeautifulSoup(text, 'html.parser')
                links = findLinks(soup, root_url)

         #firstNode.relevance = getRelevance(firstNode.url)
                firstNode.init_complete()
                print("finished finding links")
                print("adding links as children")
                for linkFound in links:
                    if(linkExists(linkFound, self.seen)==False):
                        print("\n new child ", linkFound)
                        child = node.Node(linkFound, firstNode)
                        self.data_queue.put(child)
                        self.seen.add(child)
                        firstNode.add_child(child)
              #  gather(child, keywords)
                print("finished adding children")
                print("total nodes: %i", len(self.seen))
            except Exception as e:
                print(f"Gathering error {e}")
        thread = threading.Thread(target=worker)
        thread.daemon = True
        thread.start()
        
app = App()
app.mainloop()