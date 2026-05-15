import json, os, logging
from datetime import datetime
from io import BytesIO
from minio import Minio

logger = logging.getLogger(__name__)

class BronzeWriter:
    def __init__(self):
        endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000").replace("http://", "").replace("https://", "")
        self.client = Minio(endpoint,
                            access_key=os.getenv("MINIO_ROOT_USER", "admin"),
                            secret_key=os.getenv("MINIO_ROOT_PASSWORD", "admin12345"),
                            secure=False)
        self._ensure("bronze")

    def _ensure(self, bucket):
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def write(self, article):
        now = datetime.utcnow()
        source = article.get("source", "unknown").replace(" ", "_")
        aid = article.get("id", "unknown")
        path = f"layer=batch/source={source}/year={now.year}/month={now.month:02d}/day={now.day:02d}/{aid}.json"
        data = json.dumps(article, ensure_ascii=False).encode("utf-8")
        self.client.put_object("bronze", path, BytesIO(data), len(data), "application/json")
        return path

    def list_all(self):
        return list(self.client.list_objects("bronze", recursive=True))
