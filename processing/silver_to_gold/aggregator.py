import json, os, logging
from collections import Counter
from datetime import datetime
from io import BytesIO
from minio import Minio

logger = logging.getLogger(__name__)

STOPWORDS = {"the","a","an","and","or","in","on","at","to","for","of","with","is","are",
             "le","la","les","de","du","des","et","en","un","une","que","qui","dans","sur",
             "par","sur","ce","il","elle","nous","vous","ils","elles","this","that","was",
             "has","have","been","its","are","were","said","will","also","but","not","from"}

def get_minio():
    endpoint = os.getenv("MINIO_ENDPOINT","http://localhost:9000").replace("http://","").replace("https://","")
    return Minio(endpoint,
                 access_key=os.getenv("MINIO_ROOT_USER","admin"),
                 secret_key=os.getenv("MINIO_ROOT_PASSWORD","admin12345"),
                 secure=False)

def get_pg():
    import psycopg2
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST","localhost"),
        port=os.getenv("POSTGRES_PORT","5432"),
        dbname=os.getenv("POSTGRES_DB","newsdb"),
        user=os.getenv("POSTGRES_USER","news_user"),
        password=os.getenv("POSTGRES_PASSWORD","news_pass"),
    )

class SilverToGold:
    def __init__(self):
        self.client = get_minio()
        if not self.client.bucket_exists("gold"):
            self.client.make_bucket("gold")

    def load_silver(self, date):
        date_filter = f"year={date.year}/month={date.month:02d}/day={date.day:02d}/"
        all_objs = list(self.client.list_objects("silver", recursive=True))
        objs = [o for o in all_objs if date_filter in o.object_name]
        articles = []
        for obj in objs:
            try:
                resp = self.client.get_object("silver", obj.object_name)
                articles.append(json.loads(resp.read().decode("utf-8")))
            except Exception as e:
                logger.error(f"Erreur lecture silver: {e}")
        logger.info(f"Silver chargé: {len(articles)} articles")
        return articles

    def write_gold(self, name, data, date):
        path = f"{name}/year={date.year}/month={date.month:02d}/day={date.day:02d}/{name}_{date.strftime('%Y%m%d')}.json"
        payload = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.client.put_object("gold", path, BytesIO(payload), len(payload), "application/json")
        logger.info(f"Gold MinIO écrit: {path}")

    def write_to_postgres(self, aggregations, date):
        """Insère les agrégations dans PostgreSQL pour Grafana"""
        try:
            conn = get_pg()
            cur = conn.cursor()
            d = date.date()

            # Articles par source
            for row in aggregations["per_source"]:
                cur.execute("""
                    INSERT INTO articles_per_source (date, source, count)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (date, source) DO UPDATE SET count = EXCLUDED.count
                """, (d, row["source"], row["count"]))

            # Top keywords
            for row in aggregations["keywords"][:30]:
                cur.execute("""
                    INSERT INTO top_keywords (date, keyword, frequency)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (date, keyword) DO UPDATE SET frequency = EXCLUDED.frequency
                """, (d, row["keyword"], row["frequency"]))

            # Articles individuels
            for article in aggregations["articles"]:
                cur.execute("""
                    INSERT INTO articles (id, url, title, content, author, published_at,
                                         category, source, language, country, word_count,
                                         scraped_at, created_at)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
                    ON CONFLICT (id) DO NOTHING
                """, (
                    article.get("id"),
                    article.get("url",""),
                    article.get("title",""),
                    article.get("content","")[:2000],
                    article.get("author",""),
                    article.get("published_at"),
                    article.get("category",""),
                    article.get("source",""),
                    article.get("language",""),
                    article.get("country",""),
                    article.get("word_count",0),
                    article.get("scraped_at"),
                ))

            conn.commit()
            cur.close()
            conn.close()
            logger.info(f"PostgreSQL mis à jour: {len(aggregations['per_source'])} sources, {len(aggregations['keywords'])} keywords, {len(aggregations['articles'])} articles")

        except Exception as e:
            logger.error(f"Erreur PostgreSQL: {e}")

    def run(self, date=None):
        date = date or datetime.now()
        articles = self.load_silver(date)
        if not articles:
            logger.warning(f"Aucun article Silver pour {date.date()}")
            return None

        per_source  = [{"source": s, "count": c}
                       for s, c in Counter(a.get("source","?") for a in articles).most_common()]
        per_category= [{"category": c, "count": n}
                       for c, n in Counter(a.get("category","?") for a in articles).most_common(20)]

        word_counter = Counter()
        for a in articles:
            words = (a.get("title","") + " " + a.get("content","")).lower().split()
            word_counter.update(w.strip(".,!?;:'\"()[]") for w in words
                                if len(w) > 3 and w not in STOPWORDS)
        keywords = [{"keyword": w, "frequency": f} for w, f in word_counter.most_common(50)]

        aggregations = {
            "per_source": per_source,
            "per_category": per_category,
            "keywords": keywords,
            "articles": articles,
        }

        # 1. Écriture dans MinIO Gold
        self.write_gold("per_source", per_source, date)
        self.write_gold("per_category", per_category, date)
        self.write_gold("keywords", keywords, date)

        # 2. Écriture dans PostgreSQL (pour Grafana)
        self.write_to_postgres(aggregations, date)

        logger.info(f"Pipeline Gold terminé: {len(articles)} articles")
        return {"articles": len(articles), "sources": len(per_source)}
