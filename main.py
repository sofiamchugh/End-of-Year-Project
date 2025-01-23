import tkinter as tk
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

chrome_options = Options()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode
chrome_options.add_argument("--disable-dev-shm-usage")  # Use /tmp for shared memory
chrome_options.add_argument("--no-sandbox")  # Disable sandboxing



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
            self.executor = ThreadPoolExecutor(max_workers = 3)
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
    def gather(self, firstNode, keywords, homepage_url):
        def worker(thisNode):
            try:
                print(f"processing URL {thisNode.url}")
                
                with webdriver.Chrome(options=chrome_options) as driver:
                    driver.get(thisNode.url)
                    time.sleep(3) 
                    text = driver.page_source
                    soup = BeautifulSoup(text, 'html.parser')
                    links = findLinks(soup, homepage_url)
                    print(f"found {len(links)} links")
         #firstNode.relevance = getRelevance(firstNode.url)
                    firstNode.init_complete()
                    for linkFound in links:
                        with self.lock:
                            if(linkExists(linkFound, self.seen)==False):
                                child = node.Node(linkFound, thisNode)
                                self.data_queue.put(child)
                                self.seen.add(linkFound)
                                firstNode.add_child(child)
                        #self.gather(child, keywords, homepage_url)
                                self.executor.submit(worker, child)
            except Exception as e:
                print(f"Gathering error {e}")
        self.executor.submit(worker, firstNode)
        print("done")
app = App()
app.mainloop()