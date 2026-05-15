import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from processing.bronze_to_silver.transformer import BronzeToSilver
from datetime import datetime

print("Bronze → Silver...")
result = BronzeToSilver().run(date=datetime.now())
print(f"Résultat: {result['success']} OK | {result['skipped']} ignorés | {result['errors']} erreurs")
