#!/usr/bin/env python3
import json, sys, re, os
import pandas as pd
from pathlib import Path

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


def extract_facts(in_path: str, output_dir: str):
    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entity_name = data.get("entityName", "Entity")
    filename_base = sanitize_entity_name(entity_name)
    out_path = os.path.join(output_dir, f"{filename_base}.csv")

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


def main():
    facts_dir = "facts"
    output_dir = "factCsv"
    
    # Ensure output directory exists
    Path(output_dir).mkdir(exist_ok=True)
    
    # Process all JSON files in facts directory
    json_files = list(Path(facts_dir).glob("*.json"))
    
    print(f"Found {len(json_files)} JSON files to process...")
    
    processed = 0
    failed = 0
    
    for json_file in json_files:
        try:
            output_csv = extract_facts(str(json_file), output_dir)
            print(f"Processed: {json_file.name} -> {output_csv}")
            processed += 1
        except Exception as e:
            print(f"Failed to process {json_file.name}: {e}")
            failed += 1
    
    print(f"\nProcessing complete!")
    print(f"Successfully processed: {processed} files")
    print(f"Failed: {failed} files")


if __name__ == "__main__":
    main()
