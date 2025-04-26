from azure_config import config, vm_blob_service_client
import sys, os, json, requests, logging, argparse
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from util.util import url_as_blob_name
from app.node import Node
from requests.exceptions import ConnectionError, Timeout, RequestException
MAX_RETRIES = 3

def upload_to_blob(file_name, node, links, crawl_delay):
    """Uploads node data to Azure Blob Storage"""
    try:
        blob_client = vm_blob_service_client.get_blob_client(container=config["container-name"], blob=file_name)
        node_data = json.dumps(node.node_as_json(links, crawl_delay))
        blob_client.upload_blob(node_data, overwrite=True)
        print(f"Uploaded {file_name} to Azure Blob Storage\n")

    except Exception as e:
        print(f"Error uploading blob: {e}")

def send_scrape_request(node_url, crawl_delay):
    """Sends a request via the daemon server to scrape a URL and return links."""
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.post("http://localhost:8080/scrape",  json={
                "url": node_url,
                "crawl_delay": crawl_delay,
                "timeout_ms": 15000
            }, timeout=20)
           
            result = response.json()

            if "error" in result:
                print(f"Scrape error: {result['error']}")
                return

            return result["links"]
        
        except requests.exceptions.JSONDecodeError:
            print("Raw response from daemon:\n", response.text)
            raise  

        except TimeoutError as e:
            crawl_delay +=1
            print(f"Timeout error: {e}")

        except ConnectionError as ce:
            crawl_delay +=1
            print(f"[Attempt {attempt}] ConnectionError: Cannot connect to scrape daemon. Retrying...")
        
        except Timeout as te:
            crawl_delay +=1
            print(f"[Attempt {attempt}] TimeoutError: Scrape daemon did not respond. Retrying...")
        
        except RequestException as re:
            crawl_delay
            print(f"[Attempt {attempt}] RequestException: {str(re)}. Retrying...")

    raise Exception("Failed to connect.")


def worker(node_url, node_parent, crawl_delay):
    """Sends a scrape request to the daemon, retrieves the results and uploads them to Azure."""
    node = Node(node_url, node_parent) #initialize node
    links = send_scrape_request(node_url, crawl_delay) #get links by scraping via daemon
    file_name = url_as_blob_name(node.url)
    upload_to_blob(file_name, node, links, crawl_delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("node_url")
    parser.add_argument("node_parent")
    parser.add_argument("crawl_delay")
    args = parser.parse_args()

    worker(args.node_url, args.node_parent, int(args.crawl_delay))
