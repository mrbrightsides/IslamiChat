import json
from pathlib import Path

def load_mushaf(path="mushaf_mini.json"):
    with open(Path(path), encoding="utf-8") as f:
        return json.load(f)

MUSHAF = load_mushaf()
