from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import uvicorn
from util import find_links
import os
import signal
import time
import multiprocessing
import threading

browser_lock = threading.Lock()


app = FastAPI()
playwright = sync_playwright().start()
browser = playwright.chromium.launch(headless=True)


class ScrapeRequest(BaseModel):
    url: str
    keywords: Optional[List[str]] = []
    crawl_delay: Optional[int] = 0

@app.post("/shutdown")
def shutdown():
    browser.close()
    os.kill(os.getpid(), signal.SIGINT)

@app.post("/scrape")
def scrape(req: ScrapeRequest):
    with browser_lock:
        try:
            time.sleep(req.crawl_delay)
            page = browser.new_page()
            response = page.goto(req.url, timeout=20000)
            content_type = response.headers.get('content-type', '')

            if not 'text/html' in content_type:
                print(f"{req.url} not HTML")
                return 0
                        
            status_code = response.status if response else None

            if status_code and status_code >= 400:  # Flag errors
                print(f"Warning: HTTP {status_code} \n")

            page.wait_for_load_state()
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            text = page.content()

        
            soup = BeautifulSoup(text, 'html.parser')
            # relevance = get_relevance(soup, req.keywords) if req.keywords else 0
            links = find_links(soup, req.url)
            page.close()

            return {
                "url": req.url,
           # "relevance": relevance,
                "links": links
           # "html": soup.prettify()
            }
        except Exception as e:
            return {"error": str(e)}

# Run the server
def start_daemon():

    config = uvicorn.Config(app=app, host="0.0.0.0", port=8080, log_level="info")
    server = uvicorn.Server(config)
    # Run the server in a separate process to avoid the asyncio event loop conflict
    process = multiprocessing.Process(target=server.run)
    process.start()
    process.join()  # Wait for the server to finish

if __name__ == "__main__":
    start_daemon()