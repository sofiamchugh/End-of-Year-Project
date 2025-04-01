"""   
import time
from playwright.sync_api import sync_playwright
import threading
from gather import find_links, get_relevance, link_exists
from concurrent.futures import ThreadPoolExecutor
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
                    
                    this_node.set_content(soup)
                    #run keyword search through soup
                    links = find_links(soup, homepage_url)
                    #find all links to other pages on the same website
                    print(f"adding node {this_node.url} with relevance {this_node.relevance}\n")
                """
"""
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
        self.executor.submit(worker, first_node)"""

#C:\Windows\System32\cmd.exe /c "python C:\batch\worker\worker.py"
