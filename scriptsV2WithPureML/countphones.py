import json

yelp_path = "../data/raw/yelp_academic_dataset_business.json"

total = 0
with_phone = 0

with open(yelp_path, "r", encoding="utf-8") as f:
    for line in f:
        total += 1
        try:
            obj = json.loads(line)
            if "phone" in obj and obj["phone"].strip():
                with_phone += 1
        except:
            continue

print(f"Total records: {total}")
print(f"Records with phone: {with_phone}")
print(f"Percentage with phone: {with_phone / total * 100:.2f}%")

