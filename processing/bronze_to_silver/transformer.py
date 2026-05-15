import re, json, hashlib, os, logging
from datetime import datetime
from io import BytesIO
from minio import Minio

logger = logging.getLogger(__name__)

def get_minio():
    endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000").replace("http://","").replace("https://","")
    return Minio(endpoint,
                 access_key=os.getenv("MINIO_ROOT_USER", "admin"),
                 secret_key=os.getenv("MINIO_ROOT_PASSWORD", "admin12345"),
                 secure=False)

class BronzeToSilver:
    def __init__(self):
        self.client = get_minio()
        for b in ["silver"]:
            if not self.client.bucket_exists(b):
                self.client.make_bucket(b)
        self._seen = set()

    def clean(self, text):
        if not text: return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&[a-zA-Z]+;", " ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def transform(self, raw):
        title = self.clean(raw.get("title", ""))
        content = self.clean(raw.get("content", ""))
        if not title or len(content) < 100:
            return None
        h = hashlib.md5(content.encode()).hexdigest()
        if h in self._seen:
            return None
        self._seen.add(h)
        return {**raw, "title": title, "content": content,
                "word_count": len(content.split()),
                "content_hash": h,
                "processed_at": datetime.utcnow().isoformat(),
                "raw_html": None}

    def run(self, date=None):
        date = date or datetime.now()
        date_filter = f"year={date.year}/month={date.month:02d}/day={date.day:02d}/"
        all_objs = list(self.client.list_objects("bronze", recursive=True))
        objs = [o for o in all_objs if date_filter in o.object_name]
        logger.info(f"Bronze→Silver: {len(objs)} articles à traiter")

        success = skipped = errors = 0
        for obj in objs:
            try:
                resp = self.client.get_object("bronze", obj.object_name)
                raw = json.loads(resp.read().decode("utf-8"))
                silver = self.transform(raw)
                if not silver:
                    skipped += 1
                    continue
                now = datetime.now()
                src = silver.get("source","unknown").replace(" ","_")
                path = f"source={src}/year={now.year}/month={now.month:02d}/day={now.day:02d}/{silver['id']}.json"
                data = json.dumps(silver, ensure_ascii=False).encode("utf-8")
                self.client.put_object("silver", path, BytesIO(data), len(data), "application/json")
                success += 1
            except Exception as e:
                logger.error(f"Erreur: {e}")
                errors += 1

        logger.info(f"Résultat: {success} OK | {skipped} ignorés | {errors} erreurs")
        return {"success": success, "skipped": skipped, "errors": errors}
