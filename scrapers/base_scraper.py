import requests, hashlib, json, logging
from abc import ABC, abstractmethod
from datetime import datetime
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    def __init__(self, source_name, base_url):
        self.source_name = source_name
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Mozilla/5.0"})

    def fetch_page(self, url):
        try:
            r = self.session.get(url, timeout=30)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            logger.error(f"[{self.source_name}] Erreur {url}: {e}")
            return None

    @abstractmethod
    def get_article_urls(self): pass

    @abstractmethod
    def parse_article(self, url, soup): pass

    def generate_id(self, url):
        return hashlib.md5(url.encode()).hexdigest()

    def scrape(self):
        articles = []
        urls = self.get_article_urls()
        logger.info(f"[{self.source_name}] {len(urls)} URLs trouvées")
        for url in urls:
            soup = self.fetch_page(url)
            if not soup:
                continue
            article = self.parse_article(url, soup)
            if article:
                article.update({
                    "id": self.generate_id(url),
                    "url": url,
                    "source": self.source_name,
                    "scraped_at": datetime.utcnow().isoformat(),
                })
                articles.append(article)
        logger.info(f"[{self.source_name}] {len(articles)} articles collectés")
        return articles
