import tkinter as tk
from tkinter import *
import customtkinter as ctk
from on_start import OnStartFrame
from visuals import GatherFrame
from concurrent.futures import ThreadPoolExecutor
import node
from queue import Queue
from bs4 import BeautifulSoup
from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options
from playwright.sync_api import sync_playwright
import threading
from gather import findLinks, getRelevance, linkExists


#setup for selenium to open URLs in chrome
"""chrome_options = Options()
chrome_options.add_argument("--headless=new")  
chrome_options.add_argument("--disable-dev-shm-usage") 
chrome_options.add_argument("--no-sandbox")  
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("disable-infobars")
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_argument(
     "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)"""


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
                print(f"processing URL {thisNode.url}\n")
                """ with webdriver.Chrome(options=chrome_options) as driver:

                    driver.get(thisNode.url)
                    time.sleep(3) 
                    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
                    text = driver.page_source"""
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)  # Launch browser in headless mode
                    page = browser.new_page()

               #     page.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")

                    page.goto(thisNode.url)
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")  # Scroll to the bottom
                    page.wait_for_load_state()
                    text = page.content()
                    browser.close()
                    soup = BeautifulSoup(text, 'html.parser')
                    #fetch web content and turn into beautiful soup object

                    if keywords: 
                        print("computing relevance....\n")
                        thisNode.set_relevance(getRelevance(soup, keywords))
                    #run keyword search through soup
                    links = findLinks(soup, homepage_url)
                    #find all links to other pages on the same website
                    self.data_queue.put(thisNode)
                    self.seen.add(thisNode.url)
                    print("finding links")
                    for linkFound in links:
                        #for each link 
                        with self.lock:
                            if(linkExists(linkFound, self.seen)==False):
                            #if we haven't processed this URL already
                                child = node.Node(linkFound, thisNode)
                                #create a new node corresponding to URL 
                                firstNode.add_child(child)
                                #add node to previous node's list of children
                                self.executor.submit(worker, child)
                                #submit node for processing

            except TypeError:
                 print("invalid URL")
                 self.show_frame("OnStart")
            except Exception as e:
                print(f"Gathering error {e}")
                self.show_frame("OnStart")
        self.executor.submit(worker, firstNode)

    def on_closing(self):
        #cleanup when closing window
        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id) 
        self.unbind_all("<Destroy>")
        self.quit()

app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()