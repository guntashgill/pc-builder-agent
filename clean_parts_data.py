#!/usr/bin/env python3
"""
Clean parts database by removing items with price "0.00"
"""
import json
from pathlib import Path

def clean_parts_data(input_file: str, output_file: str):
    """Remove all parts with price of "0.00" from the database"""
    
    print(f"Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    cleaned_data = {}
    total_before = 0
    total_after = 0
    
    for category, parts in data.items():
        if not isinstance(parts, list):
            cleaned_data[category] = parts
            continue
            
        total_before += len(parts)
        
        # Filter out parts with price ["USD", "0.00"] or ["CAD", "0.00"], etc.
        cleaned_parts = [
            part for part in parts
            if not (
                isinstance(part.get('price'), list) and 
                len(part.get('price', [])) >= 2 and
                part['price'][1] == "0.00"
            )
        ]
        
        total_after += len(cleaned_parts)
        cleaned_data[category] = cleaned_parts
        
        removed = len(parts) - len(cleaned_parts)
        if removed > 0:
            print(f"  {category}: removed {removed} items ({len(parts)} → {len(cleaned_parts)})")
    
    print(f"\nTotal: {total_before} → {total_after} parts (removed {total_before - total_after})")
    
    print(f"Writing to {output_file}...")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(cleaned_data, f, indent=2)
    
    print("✓ Done!")

if __name__ == "__main__":
    input_file = "app/data/pc_parts_data_20251215_104914.json"
    output_file = "app/data/parts_db.json"
    
    clean_parts_data(input_file, output_file)
