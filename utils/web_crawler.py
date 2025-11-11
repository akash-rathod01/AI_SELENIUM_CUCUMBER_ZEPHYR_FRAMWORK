import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class WebCrawler:
    def __init__(self, base_url, max_depth=2):
        self.base_url = base_url
        self.max_depth = max_depth
        self.visited = set()
        self.broken_links = []
        self.page_data = {}

    def crawl(self):
        self._crawl(self.base_url, 0)
        return {
            'visited': self.visited,
            'broken_links': self.broken_links,
            'page_data': self.page_data
        }

    def _crawl(self, url, depth):
        if depth > self.max_depth or url in self.visited:
            return
        self.visited.add(url)
        try:
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                self.broken_links.append(url)
                return
            soup = BeautifulSoup(response.text, 'html.parser')
            self.page_data[url] = {
                'title': soup.title.string if soup.title else '',
                'links': []
            }
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                if self._is_valid_url(full_url):
                    self.page_data[url]['links'].append(full_url)
                    self._crawl(full_url, depth + 1)
        except Exception:
            self.broken_links.append(url)

    def _is_valid_url(self, url):
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and self.base_url in url

    def scan_broken_links(self):
        return self.broken_links

    def get_page_data(self):
        return self.page_data

# Example usage:
# crawler = WebCrawler('https://example.com', max_depth=2)
# result = crawler.crawl()
# print(result)
