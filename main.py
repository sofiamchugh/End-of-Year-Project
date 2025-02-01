import tkinter as tk
from tkinter import ttk
from on_start import OnStartFrame
from visuals import GatherFrame
from concurrent.futures import ThreadPoolExecutor
import node
from queue import Queue
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
import threading
from gather import findLinks, getRelevance, linkExists

#setup for selenium to open URLs in chrome
chrome_options = Options()
chrome_options.add_argument("--headless")  
chrome_options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument("--no-sandbox")  

class App(tk.Tk):
    def __init__(self):
            super().__init__()
            self.title("Gather")
            self.geometry("800x600")
            self.container = ttk.Frame(self)
            self.container.pack(fill="both", expand=True)
            self.frames = {}
            self.data_queue = Queue()
            self.seen = set()
            self.lock = threading.Lock()
            self.executor = ThreadPoolExecutor(max_workers = 3)
            self.init_frames()
            self.nodes = []

    def init_frames(self):
          self.frames["OnStart"] = OnStartFrame(parent=self.container, controller=self, data_queue=self.data_queue, seen=self.seen)
          self.frames["Gathering"] = GatherFrame(parent=self.container, controller=self, data_queue=self.data_queue)
          for frame in self.frames.values():
                frame.grid(row=0, column=0, sticky="nsew")
          self.show_frame("OnStart")
    
    def show_frame(self, frame_name):
          frame = self.frames[frame_name]
          frame.tkraise()

    def gather(self, firstNode, keywords, homepage_url):
        def worker(thisNode):
            try:
                print(f"processing URL {thisNode.url}")
                with webdriver.Chrome(options=chrome_options) as driver:

                    #fetch web content and turn into beautiful soup object
                    driver.get(thisNode.url)
                    time.sleep(3) 
                    text = driver.page_source
                    soup = BeautifulSoup(text, 'html.parser')

                    firstNode.relevance = getRelevance(soup, keywords)
                    #run keyword search through soup
                    links = findLinks(soup, homepage_url)
                    #find all links to other pages on the same website

                    for linkFound in links:
                        #for each link 
                        with self.lock:
                            if(linkExists(linkFound, self.seen)==False):
                            #if we haven't processed this URL already
                                child = node.Node(linkFound, thisNode)
                                #create a new node corresponding to URL 
                                self.data_queue.put(child)
                                #add node to queue for graph visualisation
                                """self.nodes.append(child.print_me)"""
                                self.seen.add(child.url)
                                #add node to set for uniqueness checks
                                firstNode.add_child(child)
                                #add node to previous node's list of children
                                self.executor.submit(worker, child)
                                #submit node for processing

                    self.data_queue.put(thisNode)
                    #the second time a node is put in the queue it is finished processing
                    #the node will no longer be animated in the graph
            except Exception as e:
                print(f"Gathering error {e}")
        self.executor.submit(worker, firstNode)
        print("done")

app = App()
app.mainloop()