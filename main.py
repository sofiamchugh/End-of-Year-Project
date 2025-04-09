from tkinter import *
import customtkinter as ctk
from on_start import OnStartFrame
from visuals import GatherFrame
import node
import time
from queue import Queue
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import threading
from urllib.parse import urlparse, urlunparse
from concurrent.futures import ThreadPoolExecutor
from gather import link_exists, get_relevance, find_links
import logging
logging.basicConfig(filename="log.txt",
                    filemode='w',
                    format='%(message)s',
                    level=logging.DEBUG)

ctk.set_appearance_mode("light")


class App(ctk.CTk):
    def __init__(self):
            super().__init__()
            self.title("Gather")
            self.geometry("800x600")
            self.container = ctk.CTkFrame(self)
            self.container.grid(row=0, column=0, sticky="nsew")
            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=1)
            self.current_frame = "OnStartFrame"
            self.frames = {}
            self.futures = set()
            self.data_queue = Queue()
            self.seen = set()
            self.lock = threading.Lock()
            self.executor = ThreadPoolExecutor(max_workers = 3)
            self.init_frames()
            self.nodes = []
            self.job_start_time = 0
    
    def finished(self):
        job_end_time = time.time() - 10.2
    
    def check_if_finished(self):
        all_done = all(f.done() for f in self.futures.copy())
        if all_done:
            job_end_time = time.time()
            print(f"Job took {job_end_time - self.job_start_time} seconds. Processed {len(self.seen)}")
        # Do any post-processing here
        else:
            self.after(500, self.check_if_finished)

    def init_frames(self):
          self.frames["OnStart"] = OnStartFrame(parent=self.container, controller=self, data_queue=self.data_queue, seen=self.seen)
          self.frames["Gathering"] = GatherFrame(parent=self.container, controller=self, data_queue=self.data_queue)
         # self.frames["Loading"] = LoadFrame(parent=self.container, controller=self )
          for frame in self.frames.values():
                frame.grid(row=0, column=0, sticky="nsew")
          self.show_frame("OnStart")

    def show_frame(self, frame_name):
        frame = self.frames[frame_name]
        frame.tkraise()
        self.current_frame = frame_name

    def gather(self, first_node, keywords):
        self.show_frame("Gathering")
        self.job_start_time = time.time()
    
        def worker(this_node):
            try:
                with sync_playwright() as p:
                    logging.debug(f"loading node {this_node.url}")
                    browser = p.chromium.launch(headless=True)  # Launch browser in headless mode
                    page = browser.new_page()
                    response = page.goto(this_node.url)
                    status_code = response.status if response else None

                    if status_code and status_code >= 400:  # Flag errors
                        logging.debug(f"Warning: HTTP {status_code} \n")

                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Scroll to the bottom
                    page.wait_for_load_state()
                    text = page.content()
                    browser.close()
                    print("browser closing")
                    soup = BeautifulSoup(text, 'html.parser')
                    #fetch web content and turn into beautiful soup object
                   
                    if keywords: 
                        this_node.set_relevance(get_relevance(soup, keywords))

                    else:
                        this_node.set_relevance(0.5)
                    
                    this_node.set_content(soup)
                    self.data_queue.put(this_node)
                    logging.debug("node added to queue")
                    #run keyword search through soup
                    links = find_links(soup, this_node.url, first_node.url)
                    #find all links to other pages on the same website
                    print(f"adding node {this_node.url} with relevance {this_node.relevance}\n {len(links)} links found")

                    
                    if (self.current_frame == "Loading"):
                        self.show_frame("Gathering")
                        self.current_frame = "GatherFrame"
                    
                    for linkFound in links:

                        if(self.current_frame == "OnStartFrame"):
                             break
                        #for each link 
                        process_link = False
                        with self.lock:
                            if linkFound not in self.seen:
                            #if we haven't processed this URL already
                                self.seen.add(linkFound)
                                process_link = True

                        if process_link:
                            child = node.Node(linkFound, this_node)
                            #create a new node corresponding to URL 
                            first_node.add_child(child)
                            #add node to previous node's list of children
                            future = self.executor.submit(worker, child)  # Submit task
                            self.futures.add(future)
                            
                logging.debug("node complete")
            except TypeError:
                 print("invalid URL")
                 self.show_frame("OnStart")
            except Exception as e:
                print(f"Gathering error {e}")
                self.show_frame("OnStart")

        first_future = self.executor.submit(worker, first_node)
        self.futures.add(first_future)
        self.check_if_finished()

    def on_closing(self):
        #cleanup when closing window

        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id) 
        self.executor.shutdown(wait=False)
        self.unbind_all("<Destroy>")
        self.quit()

app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()