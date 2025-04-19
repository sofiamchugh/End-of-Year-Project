import argparse
import json
import time
from playwright.sync_api import sync_playwright
from azure.storage.blob import BlobServiceClient
from bs4 import BeautifulSoup
from util import find_links, get_relevance
from node import Node
import logging
import nltk
from azure_config import config, blob_service_client

nltk.download('punkt') #Download this before calling get_relevance as we are working inside a VM

#logging.basicConfig(filename='C:\\batch\\repo\\worker_log.txt', level=logging.DEBUG) #Configure logging
#logger = logging.getLogger()

def upload_to_blob(file_name, node, links, crawl_delay):
    """Uploads node data to Azure Blob Storage"""
    try:
        blob_client = blob_service_client.get_blob_client(container=config["container-name"], blob=file_name)
        node_data = json.dumps(node.node_as_json(links, crawl_delay))
        blob_client.upload_blob(node_data, overwrite=True)
        print(f"Uploaded {file_name} to Azure Blob Storage\n")

    except Exception as e:
        print(f"Error uploading blob: {e}")


def scrape(node_url, node_parent, keywords, crawl_delay):
    """
    Scrapes the data from a webpage, 
    calculates its importance for the given keywords
    and uploads everything to Azure to be downloaded by main.py.
    """
    retry_attempts = 3
    print(f"Processing {node_url}")
    node = Node(node_url, node_parent) #initialize node
    for attempt in range(retry_attempts):
        try:
            """Visit website and harvest data"""
            time.sleep(crawl_delay)
            with sync_playwright() as p: 
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                response = page.goto(node.url, timeout=20000)
                if response is None:
                    return 0
        
                content_type = response.headers.get('content-type', '')

                if not 'text/html' in content_type:
                    print(f"{node.url} not HTML")
                    return 0
                        
                status_code = response.status if response else None

                if status_code and status_code >= 400:  # Flag errors
                    logging.warning(f"Warning: HTTP {status_code} \n")


                page.wait_for_load_state() #wait for all content to load
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                text = page.content() #get the web text
                browser.close() #then exit

            """Compute a relevance value (if keywords provided)"""
            soup = BeautifulSoup(text, 'html.parser') #we turn the web text into a beautiful soup object
            node.set_relevance(get_relevance(soup, keywords) if keywords else 0) #compute relevance (optional)
           
            links = find_links(soup, node_url) #get a list of links to turn into children

            """Upload to Azure"""
            file_name = f"{node.url.replace('https://', '').replace('/', '_')}.html"
            upload_to_blob(file_name, node, links, crawl_delay)


        except TimeoutError as e:
            if(attempt + 1 == retry_attempts):
                crawl_delay = crawl_delay + 1
            else:
                print("Dropped {node.url} after 3 timeouts.")

            

    return node, links

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("node_url")
    parser.add_argument("node_parent")
    parser.add_argument("keywords")
    parser.add_argument("crawl_delay")
    args = parser.parse_args()

    scraped_node, links = scrape(args.node_url, args.node_parent, args.keywords, args.crawl_delay)
