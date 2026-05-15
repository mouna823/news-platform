from .base_scraper import BaseScraper
from datetime import datetime

class BBCScraper(BaseScraper):
    def __init__(self):
        super().__init__("BBC News", "https://www.bbc.com")

    def get_article_urls(self):
        urls = []
        for section in ["/news/world", "/news/technology", "/news/business"]:
            soup = self.fetch_page(self.base_url + section)
            if not soup: continue
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if "/news/" in href and len(href) > 20:
                    full = "https://www.bbc.com" + href if href.startswith("/") else href
                    if full not in urls and "bbc.com" in full:
                        urls.append(full)
        return list(set(urls))[:30]

    def parse_article(self, url, soup):
        try:
            title = soup.find("h1")
            blocks = soup.select("div[data-component='text-block'] p")
            content = " ".join(p.get_text(strip=True) for p in blocks)
            if not content:
                article = soup.find("article")
                content = article.get_text(" ", strip=True) if article else ""
            date_tag = soup.find("time")
            return {
                "title": title.get_text(strip=True) if title else None,
                "content": content,
                "author": "BBC News",
                "published_at": date_tag.get("datetime") if date_tag else datetime.utcnow().isoformat(),
                "category": "world",
                "language": "en",
                "country": "GB",
            }
        except:
            return None
