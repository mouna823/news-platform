import json, os, logging
from datetime import datetime

logger = logging.getLogger(__name__)

class KafkaArticleProducer:
    def __init__(self):
        self.producer = None
        try:
            from kafka import KafkaProducer
            self.producer = KafkaProducer(
                bootstrap_servers=os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092"),
                value_serializer=lambda v: json.dumps(v, ensure_ascii=False).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                request_timeout_ms=5000,
                max_block_ms=5000,
            )
            logger.info("Kafka Producer connecté")
        except Exception as e:
            logger.warning(f"Kafka non disponible (articles sauvegardés quand même dans MinIO): {e}")

    def send(self, article):
        if not self.producer:
            return False
        try:
            article["ingested_at"] = datetime.utcnow().isoformat()
            self.producer.send(
                os.getenv("KAFKA_TOPIC_RAW", "articles-raw"),
                key=article.get("source", "unknown"),
                value=article
            )
            return True
        except Exception as e:
            logger.warning(f"Kafka send error: {e}")
            return False

    def close(self):
        if self.producer:
            try:
                self.producer.flush(timeout=5)
                self.producer.close()
            except:
                pass
