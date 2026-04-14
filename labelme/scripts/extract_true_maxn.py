import os
import json
import csv
from collections import defaultdict

# Higher-level keywords
HIGHER_LEVEL_KEYWORDS = {
    "CLASS",
    "FAMILY LEVEL",
    "INFRAORDER",
    "SUBCLASS",
    "SUBPHYLUM"
}


def extract_time_from_imagepath(image_path):
    """Extract time in seconds from image filename, e.g., '_12.3s'"""
    import re
    match = re.search(r'_(\d+\.?\d*)s', image_path)
    if match:
        return float(match.group(1))
    return None


def clean_family_name(name):
    """Remove trailing 'sp.' or 'sp' from family names."""
    import re
    name = name.strip().lower()
    name = re.sub(r'\s*sp\.?$', '', name)
    return name


def parse_label(label):
    """
    Parse a LabelMe label into species and higher taxon.
    Handles exact labels for 'other;;;;;' and 'unknown_1;;;;;' to 'unknown_9;;;;;'.
    """

    # Clean the label of whitespace
    label_clean = label.strip().lower()

    # List of special labels we want to handle
    special_labels = ["other;;;;;"] + [f"unknown_{i};;;;;" for i in range(1, 10)]

    if label_clean in special_labels:
        return label_clean, label_clean

    # Otherwise, proceed with normal parsing
    parts = [p.strip() for p in label.split(";") if p.strip()]
    if not parts:
        return None, None

    # Detect higher-level labels
    for part in parts:
        if part.upper() in HIGHER_LEVEL_KEYWORDS:
            # First meaningful name after keyword
            for p in parts:
                if p and p.upper() not in HIGHER_LEVEL_KEYWORDS:
                    species_name = p.lower()
                    return species_name, clean_family_name(species_name)

    # Normal species entry
    if len(parts) >= 4:
        species_name = parts[0].lower()
        higher_taxon = clean_family_name(parts[3])
        return species_name, higher_taxon

    return None, None


def process_json_folder(folder_path):
    """Process all JSON files in a folder and compute True MaxN"""

    json_files = [f for f in os.listdir(folder_path) if f.endswith(".json")]
    print(f"Found {len(json_files)} json files.")

    true_maxn = {}
    time_of_max = {}

    for filename in json_files:
        filepath = os.path.join(folder_path, filename)

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        image_path = data.get("imagePath", "")
        time_sec = extract_time_from_imagepath(image_path)

        shapes = data.get("shapes", [])
        frame_counts = defaultdict(int)

        for shape in shapes:
            label = shape.get("label", "")
            species, higher_taxon = parse_label(label)

            if not species or not higher_taxon:
                continue

            frame_counts[(species, higher_taxon)] += 1

        for key, frame_maxn in frame_counts.items():
            if key not in true_maxn:
                true_maxn[key] = frame_maxn
                time_of_max[key] = time_sec
            else:
                if frame_maxn > true_maxn[key]:
                    true_maxn[key] = frame_maxn
                    time_of_max[key] = time_sec

    folder_name = os.path.basename(os.path.normpath(folder_path))
    output_csv = os.path.join(
        folder_path,
        f"{folder_name}_extracted_true_maxN.csv"
    )

    with open(output_csv, "w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["higher_taxon", "species", "true_maxn", "time_of_maxn_seconds"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for (species, higher_taxon), maxn in true_maxn.items():
            # Clean special labels for CSV output
            species_csv = species.replace(";;;;;", "")
            higher_taxon_csv = higher_taxon.replace(";;;;;", "")

            writer.writerow({
                "higher_taxon": higher_taxon_csv,
                "species": species_csv,
                "true_maxn": maxn,
                "time_of_maxn_seconds": time_of_max[(species, higher_taxon)]
            })

    print(f"\nTrue MaxN summary saved to:\n{output_csv}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract TRUE MaxN per species or higher taxa from LabelMe JSON files."
    )
    parser.add_argument("--folder", required=True,
                        help="Folder containing JSON files")

    args = parser.parse_args()
    process_json_folder(args.folder)