import pandas as pd
import json, re
from collections import Counter
from pathlib import Path

# --- CONFIGURATION ---
BASE_DIR = Path(__file__).resolve().parent.parent

#INPUT_NORMALIZED = "NORMALIZED_SOURCES_SAMPLE_200.csv"
INPUT_NORMALIZED = "NORMALIZED_SOURCES.csv"
OUTPUT_BEST = Path(__file__).resolve().parent / "RULE_BEST_ATTRIBUTES.csv"

# Lower rank = Better source
SOURCE_PRIORITY = {
    "meta": 0, "microsoft": 1, "foursquare": 2,
    "microsoft_structured": 3, "meta_structured": 3, "foursquare_structured": 3
}
BAD_DOMAINS = ["facebook.com", "instagram.com", "youtube.com", "twitter.com", "yelp.com"]

# --- HELPER FUNCTIONS ---
def safe_json(val):
    try: return json.loads(str(val))
    except: return None

def get_rank(src): 
    return SOURCE_PRIORITY.get(str(src).lower().strip().replace("msft","microsoft").replace("four_square","foursquare"), 99)

def clean_str(s): 
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", str(s).lower())).strip()

def extract_domain(url):
    if not url: return ""
    u = str(url).lower().replace("https://", "").replace("http://", "").replace("www.", "")
    return u.split("/")[0].strip()

# --- ATTRIBUTE RULES ---

def rule_name(df):
    """Pick name based on Source Priority. (Simple & effective for clean sources)"""
    # Sort by source rank, return the first non-empty name
    candidates = df[df["name"].notna() & (df["name"] != "")].copy()
    if candidates.empty: return "", ""
    
    candidates["rank"] = candidates["source"].apply(get_rank)
    best = candidates.sort_values("rank").iloc[0]
    return best["name"], best["source"]

def rule_phone(df):
    """Extract digits. Majority vote. Tie-break by Source Rank."""
    candidates = []
    for idx, row in df.iterrows():
        digits = re.sub(r"\D", "", str(row.get("phone", "")))
        if len(digits) >= 10: candidates.append((digits[-10:], idx)) # Keep last 10
    
    if not candidates: return "", ""
    
    # Majority Vote
    counts = Counter(c[0] for c in candidates)
    best_num = max(counts, key=counts.get) # Get most frequent number
    
    # Find source of that number with best rank
    matching_rows = [idx for num, idx in candidates if num == best_num]
    best_idx = min(matching_rows, key=lambda i: get_rank(df.loc[i, "source"]))
    return best_num, df.loc[best_idx, "source"]
'''
def rule_address(df):
    """Parse JSON. Pick longest valid address from highest priority source."""
    candidates = []
    for idx, row in df.iterrows():
        data = safe_json(row.get("address"))
        if not data or not isinstance(data, list): continue
        a = data[0] # taking first address obj
        # Construct full string
        full = f"{a.get('freeform','')} {a.get('locality','')} {a.get('region','')} {a.get('postcode','')}"
        clean_full = clean_str(full)
        if len(clean_full) > 10: # arbitrary 'valid enough' length
            candidates.append((clean_full, idx))
            
    if not candidates: return "", ""
    
    # Sort by: Source Rank (asc), then Length (desc)
    best_idx = sorted(candidates, key=lambda x: (get_rank(df.loc[x[1], "source"]), -len(x[0])))[0][1]
    
    # Return the original formatted string from that index (re-parsing for display)
    raw_data = safe_json(df.loc[best_idx, "address"])[0]
    nice_str = f"{raw_data.get('freeform','')} {raw_data.get('locality','')}, {raw_data.get('region','')} {raw_data.get('postcode','')}"
    return nice_str, df.loc[best_idx, "source"]
'''

def rule_address(df):
    """Pick first non-empty address (already normalized)."""
    candidates = df[df["addr"].notna() & (df["addr"] != "")]
    if candidates.empty: return "", ""
    # pick the first row (or by source rank if you like)
    best = candidates.sort_values("source", key=lambda s: s.apply(get_rank)).iloc[0]
    return best["addr"], best["source"]

def rule_website(df):
    """Pick non-social domain from best source."""
    candidates = []
    for idx, row in df.iterrows():
        urls = safe_json(row.get("website"))
        if not urls: continue
        url_list = urls if isinstance(urls, list) else [urls]
        for u in url_list:
            if not u: continue
            dom = extract_domain(u)
            is_junk = any(bad in dom for bad in BAD_DOMAINS)
            candidates.append((u, dom, is_junk, idx))
            
    if not candidates: return "", ""
    
    # Filter junk unless it's the only option
    clean_cands = [c for c in candidates if not c[2]]
    final_pool = clean_cands if clean_cands else candidates
    
    # Sort by Source Rank
    best_tuple = sorted(final_pool, key=lambda x: get_rank(df.loc[x[3], "source"]))[0]
    return best_tuple[0], df.loc[best_tuple[3], "source"]

def rule_category(df):
    """Pick longest category string from best source."""
    candidates = []
    for idx, row in df.iterrows():
        cat = safe_json(row.get("categories"))
        val = cat.get("primary") if isinstance(cat, dict) else str(cat)
        if val and val != "None": candidates.append((val, idx))
            
    if not candidates: return "", ""
    # Sort by Rank (asc), then Length (desc) - assuming longer is more specific
    best = sorted(candidates, key=lambda x: (get_rank(df.loc[x[1], "source"]), -len(x[0])))[0]
    return best[0], df.loc[best[1], "source"]

# --- MAIN EXECUTION ---
def run_conflation():
    df = pd.read_csv(INPUT_NORMALIZED)
    results = []

    for pid, group in df.groupby("place_id"):
        b_name, src_name = rule_name(group)
        b_phone, src_phone = rule_phone(group)
        b_addr, src_addr = rule_address(group)
        b_web, src_web = rule_website(group)
        b_cat, src_cat = rule_category(group)

        # Determine Best Source (Source that won the most fields)
        srcs = [s for s in [src_name, src_phone, src_addr, src_web, src_cat] if s]
        best_overall = max(set(srcs), key=srcs.count) if srcs else ""

        results.append({
            "place_id": pid,
            "best_source": best_overall,
            "best_name": b_name, "best_phone": b_phone,
            "best_address": b_addr, "best_website": b_web, "best_category": b_cat
        })

    pd.DataFrame(results).to_csv(OUTPUT_BEST, index=False)
    print(f"Done. Wrote {len(results)} rows to {OUTPUT_BEST}")

if __name__ == "__main__":
    run_conflation()
