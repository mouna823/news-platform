import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from processing.silver_to_gold.aggregator import SilverToGold
from datetime import datetime

print("Silver → Gold...")
result = SilverToGold().run(date=datetime.now())
print(f"Gold terminé: {result}")
