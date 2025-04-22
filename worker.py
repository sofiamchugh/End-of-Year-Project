import argparse
import json
import time
from playwright.async_api import async_playwright
from azure.storage.blob import BlobServiceClient
from bs4 import BeautifulSoup
from util import find_links, get_relevance
from node import Node
import requests
import logging
#import nltk
from azure_config import config, vm_blob_service_client

#nltk.download('punkt') #Download this before calling get_relevance as we are working inside a VM

#logging.basicConfig(filename='C:\\batch\\repo\\worker_log.txt', level=logging.DEBUG) #Configure logging
#logger = logging.getLogger()

def upload_to_blob(file_name, node, links, crawl_delay):
    """Uploads node data to Azure Blob Storage"""
    try:
        blob_client = vm_blob_service_client.get_blob_client(container=config["container-name"], blob=file_name)
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
    for attempt in range(3):
        try:
            response = requests.post("http://localhost:8080/scrape",  json={
                "url": node_url,
                "keywords": keywords.split(",") if keywords else [],
                "crawl_delay": crawl_delay,
                "timeout_ms": 15000
            }, timeout=20)
           
            result = response.json()
            if "error" in result:
                print(f"Scrape error: {result['error']}")
                return

           
            links = result["links"]

            """Upload to Azure"""
            file_name = f"{node.url.replace('https://', '').replace('http://', '').replace('/', '_').replace(".", "-")}.html"
            upload_to_blob(file_name, node, links, crawl_delay)
            break

        except requests.exceptions.JSONDecodeError:
            print("Raw response from daemon:\n", response.text)
            raise  # or handle gracefully

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

    scraped_node, links = scrape(args.node_url, args.node_parent, args.keywords, int(args.crawl_delay))
