from tkinter import *
import customtkinter as ctk
from on_start import OnStartFrame
from visuals import GatherFrame
from node import Node
import json
import time
from queue import Queue
import azure.batch as batch
from azure.storage.blob import BlobServiceClient
import azure.batch.batch_auth as batch_auth
import azure.batch.models as batch_models
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, TimeoutError
import threading
from urllib.parse import urlparse, urlunparse, urljoin
from concurrent.futures import ThreadPoolExecutor
from util import get_relevance, process_url, get_base_homepage, url_is_valid
import logging
from collections import defaultdict
logging.basicConfig(filename="log.txt",
                    filemode='w',
                    format='%(asctime)s: %(message)s',
                    level=logging.DEBUG)
logging.getLogger('matplotlib').setLevel(logging.WARNING)
logging.getLogger('customtkinter').setLevel(logging.WARNING)
logging.getLogger('PIL').setLevel(logging.WARNING)
ctk.set_appearance_mode("light")
WORKER_COUNT = 5

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
            self.executor = ThreadPoolExecutor(max_workers = WORKER_COUNT)
            self.init_frames()
            self.rules = defaultdict(lambda: {
                "disallow": [],
                "allow": [],
                "crawl_delay": 3 #default value if none specified
            })
            self.job_start_time = 0
            self.batch_client = self.init_batch_client()
    
    
    def get_robot_rules(self, url):
        #we need the homepage of the website
        url = get_base_homepage(url)
        with sync_playwright() as p:
            new_request = p.request.new_context()

            if not url.endswith("/"):
                url += "/"
            robots_url = url + "robots.txt"

            response = new_request.get(robots_url)
            if response.ok:
                text = response.text()
                for line in text.splitlines():
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue

                    if ':' not in line:
                        continue

                    key, value = map(str.strip, line.split(':', 1))
                    key = key.lower()

                    if key == "user-agent":
                        current_user_agents = [value]
                    elif key in ("disallow", "allow", "crawl-delay"):
                        for agent in current_user_agents:
                            if key == "disallow":
                                self.rules[agent]["disallow"].append(value)
                            elif key == "allow":
                                self.rules[agent]["allow"].append(value)
                            elif key == "crawl-delay":
                                try:
                                    self.rules[agent]["crawl_delay"] = float(value)
                                except ValueError:
                                    pass  # skip bad crawl-delay value
            else:
                print(f"Failed to fetch robots.txt. Status: {response.status}")

            new_request.dispose()

    def url_is_allowed(self, url):
        url = urlparse(url)
        path = url.path

        rules = self.rules.get("*")
        if not rules:
            return True
        
        allow_matches = [rule for rule in rules["allow"] if path.startswith(rule)]
        disallow_matches = [rule for rule in rules["disallow"] if path.startswith(rule)]

        longest_allow = max((len(rule) for rule in allow_matches), default=0)
        longest_disallow = max((len(rule) for rule in disallow_matches), default=0)

        return longest_allow >= longest_disallow

    def check_if_finished(self):
        all_done = all(f.done() for f in self.futures.copy())
        if all_done:
            job_end_time = time.time()
            print(f"Job took {job_end_time - self.job_start_time} seconds. Processed {len(self.seen)}")
        # Do any post-processing here
        else:
            self.after(500, self.check_if_finished)

    def init_frames(self):
        """Each frame is a class that defines a Custom TKInter layout and the relevant functions."""
        self.frames["OnStart"] = OnStartFrame(parent=self.container, controller=self, data_queue=self.data_queue, seen=self.seen)
        self.frames["Gathering"] = GatherFrame(parent=self.container, controller=self, data_queue=self.data_queue)
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        self.show_frame("OnStart")

    def show_frame(self, frame_name):
        """Change which layout is active."""
        frame = self.frames[frame_name]
        frame.tkraise()
        self.current_frame = frame_name

    def gather(self, first_node, keywords):
        self.show_frame("Gathering")
        self.job_start_time = time.time()
        user_agent = "*"
        retry_attempts = 3  
        dropped_pages = 0
        def worker(this_node):
            crawl_delay = self.rules[user_agent]["crawl_delay"]
            for attempt in range(retry_attempts):
                try:
                    thread_name = threading.current_thread().name
                    index = int(thread_name.split('_')[-1])  
                    offset = index * (1 / WORKER_COUNT)
                    time.sleep(crawl_delay + offset)

                    with sync_playwright() as p:

                        logging.debug(f"Loading node {this_node.url} after {crawl_delay + offset}s")
                        browser = p.chromium.launch(headless=True)  # Launch browser in headless mode
                        page = browser.new_page()
                        response = page.goto(this_node.url, timeout=20000)
                        if response is None:
                            continue

                        content_type = response.headers.get('content-type', '')

                        if not 'text/html' in content_type:
                            print(f"{this_node.url} not HTML")
                            continue
                        
                        status_code = response.status if response else None

                        if status_code and status_code >= 400:  # Flag errors
                            logging.warning(f"Warning: HTTP {status_code} \n")

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
                    
                        self.data_queue.put(this_node)
                        logging.debug(f"Node {this_node.url} added to data queue")
                        #run keyword search through soup
                        #links = find_links(soup, this_node.url, first_node.url)
                        #find all links to other pages on the same website

                        for link in soup.find_all('a'):
                            l = link.get('href')
                            if l:
                                l = urljoin(this_node.url, l)
                                if '#' in l:
                                    continue
                                if "pdf" in l:
                                    continue
                                if "doc" in l:
                                    continue
                                l = process_url(l)
                                if get_base_homepage(l) != get_base_homepage(this_node.url):
                                    continue
                                if not url_is_valid(l):
                                    continue
                                if(self.current_frame == "OnStartFrame"):
                                    break
                            
                                process_link = False
                                with self.lock:
                                    if l not in self.seen:
                                    #if we haven't processed this URL already
                                        logging.info(f"Adding {l} to self.seen")
                                        self.seen.add(l)
                                        process_link = True

                                if process_link:
                                    if self.url_is_allowed(l):
                                        child = node.Node(l, this_node)
                                        #create a new node corresponding to URL 
                                        first_node.add_child(child)
                                        #add node to previous node's list of children
                                        future = self.executor.submit(worker, child)  # Submit task
                                        self.futures.add(future)
                                    else: 
                                        logging.debug("This URL is disallowed by robots.txt")
                            
                    logging.debug("node complete")

                except TimeoutError as e:
                    with self.lock:
                        current_delay = self.rules[user_agent]["crawl_delay"]
                        if current_delay == crawl_delay:
                            self.rules[user_agent]["crawl_delay"] = crawl_delay + 1
                            logging.debug(f"Current crawl delay is insufficient - incrementing...")
                            logging.debug(f"New crawl delay: {crawl_delay + 1}")
                            continue
                    if attempt + 1 == retry_attempts:
                        logging.debug(f"Abandoning node {this_node.url} due to too many failed attempts.")
                        dropped_pages +=1
                        print(f"dropped {dropped_pages} pages\n")
                        
                        break
                except Exception as e:
                    if "ERR_NETWORK_CHANGED" in str(e) and attempt +1 < retry_attempts:
                        continue
                    else:
                        print(f"Gathering error {e}")
                        self.show_frame("OnStart")
                        break

        self.seen.add(first_node.url)
        first_future = self.executor.submit(worker, first_node)
        self.futures.add(first_future)
        self.check_if_finished()

    def on_closing(self):
        """Cleanup when closing window."""
        job_list = list(self.batch_client.job.list())  # Get all jobs

        for job in job_list:
            print(f"Deleting job: {job.id}") 
            self.batch_client.job.delete(job.id) #delete job when done

        for after_id in self.tk.call('after', 'info'):
            self.after_cancel(after_id) 
        self.unbind_all("<Destroy>") 
        self.quit()

"""App runs here"""
app = App()
app.protocol("WM_DELETE_WINDOW", app.on_closing)
app.mainloop()