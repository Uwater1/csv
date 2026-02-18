#!/usr/bin/env python3
import json, sys, re
import pandas as pd

def sanitize_entity_name(name: str) -> str:
    """
    Convert entityName to a safe CSV filename:
    - Stop at first non-alphanumeric character
    - Replace spaces with underscores
    - Capitalize first letter of each word
    - Remove any remaining non-alphanumeric characters
    """
    # Stop at first non-alphanumeric (except space)
    m = re.search(r"[^A-Za-z0-9 ]", name)
    if m:
        name = name[:m.start()]
    # Normalize spaces and underscores
    parts = [p.capitalize() for p in name.strip().split() if p]
    safe = "_".join(parts)
    return safe


def extract_facts(in_path: str):
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entity_name = data.get("entityName", "Entity")
    filename_base = sanitize_entity_name(entity_name)
    out_path = f"{filename_base}.csv"

    facts = data.get("facts", {}) or {}
    rows = []

    for taxonomy, fact_group in facts.items():
        for fact_name, fact_obj in fact_group.items():
            units = fact_obj.get("units", {}) or {}
            for unit_name, observations in units.items():
                if isinstance(observations, dict):
                    observations = [observations]
                for obs in observations:
                    rows.append({
                        "taxonomy": taxonomy,
                        "fact_name": fact_name,
                        "unit": unit_name,
                        "value": obs.get("val"),
                        "start": obs.get("start"),
                        "end": obs.get("end"),
                        "fy": obs.get("fy"),
                        "fp": obs.get("fp"),
                        "form": obs.get("form"),
                        "filed": obs.get("filed"),
                        "frame": obs.get("frame"),
                        "decimals": obs.get("decimals"),
                    })

    df = pd.DataFrame(rows)
    columns = [
        "taxonomy",
        "fact_name",
        "unit",
        "value",
        "start",
        "end",
        "fy",
        "fp",
        "form",
        "filed",
        "frame",
        "decimals",
    ]
    df = df[columns]
    df.to_csv(out_path, index=False)
    return out_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract.py <CIKxxxxx.json>")
        sys.exit(1)

    input_json = sys.argv[1]
    output_csv = extract_facts(input_json)
    print(f"Wrote {output_csv}")
