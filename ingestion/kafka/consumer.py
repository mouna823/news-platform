"""
Consumer Kafka — lit les articles en temps réel et les écrit dans MinIO Bronze
Tourne en continu comme un service
"""
import json, os, sys, signal, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from datalake.bronze.writer import BronzeWriter

KAFKA_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
TOPIC         = os.getenv("KAFKA_TOPIC_RAW", "articles-raw")
GROUP_ID      = "news-consumer-group"

running = True

def shutdown(sig, frame):
    global running
    logger.info("Arrêt du consumer...")
    running = False

signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

def start():
    from kafka import KafkaConsumer

    writer = BronzeWriter()
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=KAFKA_SERVERS,
        group_id=GROUP_ID,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
    )

    logger.info(f"Consumer démarré → topic: {TOPIC} | group: {GROUP_ID}")
    count = 0

    while running:
        messages = consumer.poll(timeout_ms=1000)
        for tp, records in messages.items():
            for record in records:
                try:
                    article = record.value
                    if article.get("title") and article.get("url"):
                        writer.write(article, )
                        count += 1
                        if count % 10 == 0:
                            logger.info(f"Consumer: {count} articles traités")
                except Exception as e:
                    logger.error(f"Erreur traitement message: {e}")

    consumer.close()
    logger.info(f"Consumer arrêté. Total: {count} articles")

if __name__ == "__main__":
    start()
