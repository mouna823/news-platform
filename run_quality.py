import sys, os, json, logging
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from datetime import datetime

logging.basicConfig(level=logging.INFO)

os.environ.setdefault("MINIO_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("MINIO_ROOT_USER", "admin")
os.environ.setdefault("MINIO_ROOT_PASSWORD", "admin12345")

from minio import Minio

endpoint = os.getenv("MINIO_ENDPOINT","http://localhost:9000").replace("http://","")
client = Minio(endpoint, access_key=os.getenv("MINIO_ROOT_USER","admin"),
               secret_key=os.getenv("MINIO_ROOT_PASSWORD","admin12345"), secure=False)

date = datetime.now()
date_filter = f"year={date.year}/month={date.month:02d}/day={date.day:02d}/"
all_objs = list(client.list_objects("silver", recursive=True))
objs = [o for o in all_objs if date_filter in o.object_name]

total = valid = invalid = 0
for obj in objs:
    try:
        resp = client.get_object("silver", obj.object_name)
        article = json.loads(resp.read().decode("utf-8"))
        total += 1
        issues = []
        if not article.get("title"): issues.append("titre manquant")
        if not article.get("published_at"): issues.append("date manquante")
        if len(article.get("content","")) < 100: issues.append("contenu trop court")
        if issues:
            invalid += 1
        else:
            valid += 1
    except Exception as e:
        invalid += 1

error_rate = invalid / total if total > 0 else 0
print(f"\n=== RAPPORT QUALITÉ ===")
print(f"Total     : {total}")
print(f"Valides   : {valid}")
print(f"Invalides : {invalid}")
print(f"Taux erreur: {error_rate:.1%}")

if error_rate > 0.5:
    print("ATTENTION: taux d'erreur élevé!")
    sys.exit(1)

print("Qualité OK ✓")
