"""
Scraper Hespress — RSS + fallback HTML avec anti-blocking
"""
import time, random, xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
from .base_scraper import BaseScraper
import logging

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15",
]

RSS_FEEDS = [
    "https://www.hespress.com/feed",
    "https://www.hespress.com/?feed=rss2",
    "https://www.hespress.com/category/politique/feed",
    "https://www.hespress.com/category/sport/feed",
]

class HespressScraper(BaseScraper):
    def __init__(self):
        super().__init__("Hespress", "https://www.hespress.com")
        self._rotate_agent()

    def _rotate_agent(self):
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ar,fr-FR;q=0.9,fr;q=0.8,en;q=0.7",
            "Referer": "https://www.google.com/search?q=hespress+maroc",
            "Cache-Control": "max-age=0",
        })

    def _fetch_rss(self, url):
        try:
            self._rotate_agent()
            r = self.session.get(url, timeout=15)
            if r.status_code != 200:
                return []
            root = ET.fromstring(r.content)
            ns = {"content": "http://purl.org/rss/1.0/modules/content/"}
            articles = []
            for item in root.findall(".//item"):
                title   = item.findtext("title", "").strip()
                link    = item.findtext("link", "").strip()
                pub     = item.findtext("pubDate", "")
                desc    = item.findtext("description", "")
                content = item.findtext("content:encoded", "", ns) or desc
                clean   = BeautifulSoup(content, "html.parser").get_text(" ", strip=True)
                if title and link and len(clean) > 50:
                    articles.append({
                        "title": title, "content": clean, "author": "Hespress",
                        "published_at": pub, "category": "actualite",
                        "language": "ar", "country": "MA",
                        "id": self.generate_id(link), "url": link,
                        "source": self.source_name,
                        "scraped_at": datetime.utcnow().isoformat(),
                    })
            logger.info(f"[Hespress RSS] {len(articles)} articles depuis {url}")
            return articles
        except Exception as e:
            logger.warning(f"[Hespress RSS] {url}: {e}")
            return []

    def get_article_urls(self):
        urls = []
        try:
            self._rotate_agent()
            time.sleep(random.uniform(1, 3))
            soup = self.fetch_page(self.base_url)
            if soup:
                for a in soup.select("h3 a, h2 a, .card-title a, .overlay a"):
                    href = a.get("href", "")
                    if len(href) > 20:
                        full = href if href.startswith("http") else self.base_url + href
                        if full not in urls:
                            urls.append(full)
        except Exception as e:
            logger.warning(f"get_article_urls: {e}")
        return urls[:20]

    def parse_article(self, url, soup):
        try:
            title = soup.find("h1") or soup.find("h2")
            content_div = (soup.find("div", class_="article-content") or
                          soup.find("div", class_="post-content") or
                          soup.find("article"))
            return {
                "title": title.get_text(strip=True) if title else None,
                "content": content_div.get_text(" ", strip=True) if content_div else "",
                "author": "Hespress", "published_at": datetime.utcnow().isoformat(),
                "category": "actualite", "language": "ar", "country": "MA",
            }
        except:
            return None

    def scrape(self):
        all_articles = []
        # Essayer RSS d'abord
        for feed_url in RSS_FEEDS:
            articles = self._fetch_rss(feed_url)
            for a in articles:
                if not any(x["url"] == a["url"] for x in all_articles):
                    all_articles.append(a)
            time.sleep(random.uniform(0.5, 1.5))

        if all_articles:
            logger.info(f"[Hespress] {len(all_articles)} articles via RSS")
            return all_articles

        # Fallback HTML
        logger.info("[Hespress] Fallback HTML...")
        time.sleep(random.uniform(2, 4))
        return super().scrape()
