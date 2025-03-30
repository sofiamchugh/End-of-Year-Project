import argparse
import json
import time
from playwright.sync_api import sync_playwright
from azure.storage.blob import BlobServiceClient
from bs4 import BeautifulSoup
from gather import find_links, get_relevance, link_exists
from node import Node
from main import load_config 

config = load_config()
blob_service_client = BlobServiceClient.from_connection_string(config["azure-storage-connection-string"])

def upload_to_blob(file_name, node):
    """Uploads scraped data to Azure Blob Storage"""
    blob_client = blob_service_client.get_blob_client(container=config["container-name"], blob=file_name)
    blob_client.upload_blob(node.node_as_json(), overwrite=True)
    print(f"Uploaded {file_name} to Azure Blob Storage\n")

def scrape(node_url, keywords, homepage_url, node_parent):
    node = Node.node(node_url, node_parent)
    with sync_playwright() as p:
        print("gathering...\n")
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(node.url)
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_load_state()
        text = page.content()
        browser.close()

        soup = BeautifulSoup(text, 'html.parser')
        node.set_relevance(get_relevance(soup, keywords) if keywords else 0)
        node.set_content(soup)
        links = find_links(soup, homepage_url)

        file_name = f"{node.url.replace('https://', '').replace('/', '_')}.html"
        upload_to_blob(file_name, node)

        return node, links

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("node_url")
    parser.add_argument("node_parent")
    parser.add_argument("keywords")
    parser.add_argument("homepage_url")
    args = parser.parse_args()

    node = Node.from_json(args.node)  # Convert string to Node object
    scraped_node, links = scrape(args.node_url, args.node_parent, args.keywords, args.homepage_url)