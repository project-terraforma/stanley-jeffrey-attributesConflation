import csv
import json



INPUT = "../data/raw/OMF_ALL_COMBINED.csv"
INPUT = "project_b_samples_2k.csv"
OUTPUT = "NORMALIZED_SOURCES.csv"

# --------------------------------------------
# PARSING STATISTICS
# --------------------------------------------
parse_attempts = 0
parse_failures = 0
total_raw_records = 0
normalized_records = 0

# --------------------------------------------
# HELPERS
# --------------------------------------------
def safe_json(val):
    """Safe JSON loader that tracks parsing attempts & failures."""
    global parse_attempts, parse_failures
    if not val or val.strip() == "":
        return None
    parse_attempts += 1
    try:
        return json.loads(val)
    except Exception:
        parse_failures += 1
        return None

def stringify(x):
    """Ensures large integer IDs do not get mangled by Excel."""
    if x is None:
        return ""
    return f"=\"{str(x)}\""

# --------------------------------------------
# MAIN NORMALIZATION PROCESS
# --------------------------------------------
with open(INPUT, encoding="utf-8") as fin, open(OUTPUT, "w", newline="", encoding="utf-8") as fout:
    reader = csv.DictReader(fin)
    writer = csv.writer(fout)

    # Output schema
    writer.writerow([
        "place_id", "source", "record_id", "update_time", "name",
        "categories", "phone", "website", "socials", "address", "confidence"
    ])

    # ----------------------------------------
    # PROCESS EACH OMF ROW
    # ----------------------------------------
    for row in reader:
        total_raw_records += 1
        rows_written_for_this_place = 0

        place_id = row["id"]

        # Extract fields
        sources = safe_json(row["sources"])
        name = safe_json(row["names"])
        cat = safe_json(row["categories"])
        web = safe_json(row["websites"])
        socials = safe_json(row["socials"])
        phone = safe_json(row["phones"])
        addr = safe_json(row["addresses"])
        conf = row["confidence"]

        # =====================================================
        # UNIVERSAL HANDLER FOR ALL DATASETS IN "sources"
        # =====================================================
        if isinstance(sources, list):
            for item in sources:
                dataset = item.get("dataset", "").lower()
                writer.writerow([
                    place_id,
                    dataset,
                    stringify(item.get("record_id")),
                    item.get("update_time", ""),
                    name.get("primary") if isinstance(name, dict) else "",
                    json.dumps(cat) if cat else "",
                    json.dumps(phone) if phone else "",
                    json.dumps(web) if web else "",
                    json.dumps(socials) if socials else "",
                    json.dumps(addr) if addr else "",
                    item.get("confidence", conf)
                ])
                rows_written_for_this_place += 1

        # =====================================================
        # UNIVERSAL HANDLER FOR STRUCTURED DATA (base_*)
        # =====================================================
        struct_sources = safe_json(row["base_sources"])
        struct_name = safe_json(row["base_names"])
        struct_cat = safe_json(row["base_categories"])
        struct_web = safe_json(row["base_websites"])
        struct_socials = safe_json(row["base_socials"])
        struct_phone = safe_json(row["base_phones"])
        struct_addr = safe_json(row["base_addresses"])
        struct_conf = row["base_confidence"]

        if isinstance(struct_sources, list) and len(struct_sources) > 0:
            struct = struct_sources[0]
            dataset = struct.get("dataset", "structured").lower()
            writer.writerow([
                place_id,
                f"{dataset}_structured",
                stringify(struct.get("record_id")),
                struct.get("update_time", ""),
                struct_name.get("primary") if isinstance(struct_name, dict) else "",
                json.dumps(struct_cat) if struct_cat else "",
                json.dumps(struct_phone) if struct_phone else "",
                json.dumps(struct_web) if struct_web else "",
                json.dumps(struct_socials) if struct_socials else "",
                json.dumps(struct_addr) if struct_addr else "",
                struct_conf
            ])
            rows_written_for_this_place += 1

        # =====================================================
        # ENSURE COVERAGE
        # =====================================================
        if rows_written_for_this_place == 0:
            writer.writerow([
                place_id, "missing_all_data", "", "", "", "", "", "", "", "", ""
            ])

        normalized_records += 1

# --------------------------------------------
# PRINT SUMMARY
# --------------------------------------------
coverage = (normalized_records / total_raw_records) * 100
error_rate = (parse_failures / parse_attempts * 100) if parse_attempts else 0

print("=== NORMALIZATION STATS ===")
print("Input OMF records:", total_raw_records)
print("Normalized records produced:", normalized_records)
print(f"Normalization coverage: {coverage:.2f}%")
print()

print("=== PARSING STATS ===")
print("Total parse attempts:", parse_attempts)
print("Total parse failures:", parse_failures)
print(f"Parsing error rate: {error_rate:.2f}%")
print()

if error_rate < 1.0:
    print("Parsing error rate acceptable (<1%)")
else:
    print("WARNING: High parsing error rate!")

