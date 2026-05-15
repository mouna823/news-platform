from .base_scraper import BaseScraper
from datetime import datetime

class AlJazeeraScraper(BaseScraper):
    def __init__(self, lang="ar"):
        self.lang = lang
        base = "https://www.aljazeera.net" if lang == "ar" else "https://www.aljazeera.com"
        super().__init__(f"AlJazeera-{lang.upper()}", base)

    def get_article_urls(self):
        urls = []
        sections = ["/news", "/economy"] if self.lang == "ar" else ["/news", "/economy", "/technology"]
        for section in sections:
            soup = self.fetch_page(self.base_url + section)
            if not soup: continue
            for a in soup.select("a[href]"):
                href = a.get("href", "")
                if any(s in href for s in ["/news/", "/economy/", "/technology/"]):
                    full = self.base_url + href if href.startswith("/") else href
                    if full not in urls and len(href) > 20:
                        urls.append(full)
        return list(set(urls))[:30]

    def parse_article(self, url, soup):
        try:
            title = soup.find("h1")
            content_div = soup.select_one("div.wysiwyg, div.article-body")
            content = content_div.get_text(" ", strip=True) if content_div else ""
            date_tag = soup.find("time")
            return {
                "title": title.get_text(strip=True) if title else None,
                "content": content,
                "author": "Al Jazeera",
                "published_at": date_tag.get("datetime") if date_tag else datetime.utcnow().isoformat(),
                "category": "news",
                "language": self.lang,
                "country": "QA",
            }
        except:
            return None
