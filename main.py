import tkinter as tk
from tkinter import *
import customtkinter as ctk
from on_start import OnStartFrame
from visuals import GatherFrame
import node
from queue import Queue
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import threading
from concurrent.futures import ThreadPoolExecutor
from gather import link_exists, get_relevance, find_links

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
            self.current_frame = "OnStart"
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
      self.current_frame = frame_name


    def gather(self, first_node, keywords, homepage_url):
    
        def worker(this_node):
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)  # Launch browser in headless mode
                    page = browser.new_page()
                    page.goto(this_node.url)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Scroll to the bottom
                    page.wait_for_load_state()
                    text = page.content()
                    browser.close()
                    soup = BeautifulSoup(text, 'html.parser')
                    #fetch web content and turn into beautiful soup object

                    if keywords: 
                        this_node.set_relevance(get_relevance(soup, keywords))

                    else:
                        this_node.set_relevance(0.5)
                    
                    this_node.set_content(soup)
                    #run keyword search through soup
                    links = find_links(soup, homepage_url)
                    #find all links to other pages on the same website
                    print(f"adding node {this_node.url} with relevance {this_node.relevance}\n")

                    self.data_queue.put(this_node)
                    self.seen.add(this_node.url)
                    print("finding links")
                    for linkFound in links:
                        if(self.current_frame == "OnStartFrame"):
                             break
                        #for each link 
                        with self.lock:
                            if(link_exists(linkFound, self.seen)==False):
                            #if we haven't processed this URL already
                                child = node.Node(linkFound, this_node)
                                #create a new node corresponding to URL 
                                first_node.add_child(child)
                                #add node to previous node's list of children
                                self.executor.submit(worker, child)
                                #submit node for processing
                            

            except TypeError:
                 print("invalid URL")
                 self.show_frame("OnStart")
            except Exception as e:
                print(f"Gathering error {e}")
                self.show_frame("OnStart")
        self.executor.submit(worker, first_node)

    def on_closing(self):
        #cleanup when closing window

        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id) 
        self.unbind_all("<Destroy>")
        self.quit()

app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()