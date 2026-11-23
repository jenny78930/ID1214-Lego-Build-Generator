
import csv
import gzip
import sqlite3
from pathlib import Path
from collections import Counter

BASE = Path(__file__).resolve().parent.parent
DATA = BASE / "dataset"
OUT = BASE / "filtered_bricks"
OUT.mkdir(exist_ok=True)
MIN_SETS = 5 # Minimum number of sets the brick has to be in to be added to the db

def read_csv(name):
    path = DATA / name
    if not path.exists():
        path = DATA / (name + ".gz")
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8-sig", newline="") as f:
        yield from csv.DictReader(f)

# Load brick categories and parts
categories = {r["id"]: r["name"] for r in read_csv("part_categories.csv")}
parts = {
    r["part_num"]: (r["name"], categories[r["part_cat_id"]])
    for r in read_csv("parts.csv")
    if categories.get(r["part_cat_id"], "").lower().startswith("bricks")
}

# Find latest inventory for each set
latest = {}
for r in read_csv("inventories.csv"):
    key, version = r["set_num"], int(r["version"])
    if key not in latest or version > latest[key][0]:
        latest[key] = (version, r["id"])

valid_ids = {v[1] for v in latest.values()}

# Count sets containing each brick
set_count = Counter()
usage = Counter()
seen = set()

for r in read_csv("inventory_parts.csv"):
    pid, inv = r["part_num"], r["inventory_id"]
    if pid not in parts or inv not in valid_ids:
        continue
    if r["is_spare"].lower() in ("t", "true", "1"):
        continue

    qty = int(r["quantity"])
    if qty <= 0:
        continue

    usage[pid] += qty
    if (pid, inv) not in seen:
        set_count[pid] += 1
        seen.add((pid, inv))

# Filter and sort bricks by popularity
ranked = sorted(
    [
        (pid, *info, set_count[pid], usage[pid])
        for pid, info in parts.items()
        if set_count[pid] >= MIN_SETS
    ],
    key=lambda r: (-r[3], -r[4], r[0])
)

# Save CSV
with open(OUT / "common_bricks.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["part_id", "name", "category", "set_count", "usage_count"])
    writer.writerows(ranked)

db_path = OUT / "bricks.db"

if db_path.exists():
    print(f"Database already exists: {db_path}")
    print("No changes were made to the database.")
else:
    with sqlite3.connect(db_path) as db:
        db.execute("""
            CREATE TABLE bricks (
                part_id TEXT PRIMARY KEY,
                name TEXT,
                category TEXT,
                set_count INTEGER,
                usage_count INTEGER
            )
        """)
        db.executemany(
            "INSERT INTO bricks VALUES (?, ?, ?, ?, ?)",
            ranked
        )
    print(f"Database created: {db_path}")

# Results
print(f"\nFound {len(ranked)} LEGO brick types\n")
for i, r in enumerate(ranked[:30], 1):
    print(f"{i}. {r[1]} | Sets: {r[3]:,}")

print(f"\nCSV saved to: {OUT / 'common_bricks.csv'}")
