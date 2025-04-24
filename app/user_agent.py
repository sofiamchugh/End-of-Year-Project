from playwright.sync_api import sync_playwright
from util.util import get_base_homepage 

ANCHOR_TAG = "#"
ALLOW = "allow"
DISALLOW = "disallow"
CRAWL_DELAY = "crawl-delay"
USER_AGENT = "user-agent"

class UserAgent:
    def __init__(self):
        self.disallow = []
        self.allow = []
        self.crawl_delay = 3

    def parse_robots_txt(self, text):
        """Read robots.txt file and add rules, if any"""
        for line in text.splitlines():
            line = line.strip()
            
            if not line or line.startswith(ANCHOR_TAG):
                continue

            if ':' not in line:
                continue

            key, value = map(str.strip, line.split(':', 1))
            key = key.lower()
            if key == USER_AGENT:
                parsing = (value == "*")
            elif parsing:
                if key == DISALLOW:
                    self.disallow.append(value)
                elif key == ALLOW:
                    self.allow.append(value)
                elif key == CRAWL_DELAY:
                    self.crawl_delay = float(value)
   
    def init_from_url(self, url):
        """Looks for a robots.txt file in a website"""
        print("Looking for robots.txt\n")
        url = get_base_homepage(url)
        with sync_playwright() as p:
            new_request = p.request.new_context()

            if not url.endswith("/"):
                url += "/"
            robots_url = url + "robots.txt"

            response = new_request.get(robots_url)
            if response.ok:
                text = response.text()
                print("Found robots.txt. Parsing now \n")
                self.parse_robots_txt(text)           
            
            else:
                print(f"Failed to fetch robots.txt. Status: {response.status}")

            new_request.dispose()

    def url_is_allowed(self, url):
        """Checks if the user agent is allowed to crawl a certain URL"""
        matched_rule = None
        matched_type = None  # "allow" or "disallow"

        for rule in self.allow:
            if url.startswith(rule):
                if matched_rule is None or len(rule) > len(matched_rule):
                    matched_rule = rule
                    matched_type = ALLOW

        for rule in self.disallow:
            if url.startswith(rule):
                if matched_rule is None or len(rule) > len(matched_rule):
                    matched_rule = rule
                    matched_type = DISALLOW

        return matched_type != DISALLOW