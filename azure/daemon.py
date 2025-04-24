from fastapi import FastAPI, Request
from pydantic import BaseModel
from typing import List, Optional
from playwright.async_api import async_playwright, Browser
from bs4 import BeautifulSoup
import uvicorn
from util.util import find_links
import asyncio
from contextlib import asynccontextmanager

class ScrapeRequest(BaseModel):
    url: str
    keywords: Optional[List[str]] = []
    crawl_delay: Optional[int] = 0

"""Playwright persists in lifespan between different workers"""
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting Playwright...")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    # Store it in app state
    app.state.playwright = playwright
    app.state.browser = browser

    yield #app runs here

    print("Shutting down Playwright...")
    await browser.close()
    await playwright.stop()


app = FastAPI(lifespan=lifespan)


@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    """Uses playwright to load a webpage and get links."""
    try:
        await asyncio.sleep(req.crawl_delay)

        browser: Browser = app.state.browser
        page = await browser.new_page()

        response = await page.goto(req.url, timeout=20000)
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type:
            return {"error": "Not HTML content"}

        await page.wait_for_load_state()
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        html = await page.content()
        await page.close()

        soup = BeautifulSoup(html, "html.parser")
        links = find_links(soup, req.url)

        return {
            "url": req.url,
            "links": links
        }

    except Exception as e:
        return {"error": str(e)}
