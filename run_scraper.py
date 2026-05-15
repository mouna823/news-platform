"""Lance un scraper specifique - appelé par Airflow"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datalake.bronze.writer import BronzeWriter
from ingestion.kafka.producer import KafkaArticleProducer

source = sys.argv[1] if len(sys.argv) > 1 else "all"

if source == "hespress":
    from scrapers.hespress_scraper import HespressScraper
    scrapers = [HespressScraper()]
elif source == "aljazeera":
    from scrapers.aljazeera_scraper import AlJazeeraScraper
    scrapers = [AlJazeeraScraper("ar"), AlJazeeraScraper("en")]
elif source == "bbc":
    from scrapers.bbc_scraper import BBCScraper
    scrapers = [BBCScraper()]
else:
    from scrapers.hespress_scraper import HespressScraper
    from scrapers.aljazeera_scraper import AlJazeeraScraper
    from scrapers.bbc_scraper import BBCScraper
    scrapers = [HespressScraper(), AlJazeeraScraper("ar"), AlJazeeraScraper("en"), BBCScraper()]

writer   = BronzeWriter()
producer = KafkaArticleProducer()
total    = 0

for scraper in scrapers:
    print(f"Scraping: {scraper.source_name}")
    articles = scraper.scrape()
    for article in articles:
        writer.write(article)
        producer.send(article)
    total += len(articles)
    print(f"  {len(articles)} articles collectés")

producer.close()
print(f"Total: {total} articles")
