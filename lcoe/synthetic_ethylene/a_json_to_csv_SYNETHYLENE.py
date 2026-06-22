import json
import csv
import io

# change this manual file path!
manual_file_path = "/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/9Zone_US/allethylene_168hr"

def json_to_csv_transforms(json_data, output_path=None, field_map=None):
    """
    Parse JSON and extract fields per instance, with customizable field mapping.

    Args:
        json_data: dict (already parsed JSON) or str (path to JSON file)
        output_path: optional path to write CSV. If None, prints to stdout.
        field_map: list of (output_col_name, source, json_key) tuples.
                   source options:
                     "id"        → instance.get(json_key)
                     "transforms"→ instance["transforms"].get(json_key)
                     "edge:<name>"→ instance["edges"]["<name>"].get(json_key)
                   If None, uses the default mapping below.
    """

    # ── DEFAULT FIELD MAP ──────────────────────────────────────────────────────
    # Each entry: (output column name, source, json key)
    # source = "id" | "transforms" | "edge:<edge_name>"
    DEFAULT_FIELD_MAP = [
        ("id",                                          "id",                          "id"),
        ("h2_consumption",             "transforms",                  "h2_consumption"),
        ("elec_consumption",           "transforms",                  "elec_consumption"),
        ("ethylene_production", "transforms",                  "ethylene_production"),
        ("natgas_production",          "transforms",                  "natgas_production"),
        ("gasoline_production",          "transforms",                  "gasoline_production"),
        ("emission_rate",            "transforms",                  "emission_rate"),
        ("investment_cost",        "edge:co2_captured_edge", "investment_cost"),
        ("fixed_om_cost",          "edge:co2_captured_edge", "fixed_om_cost"),
        ("variable_om_cost",             "edge:co2_captured_edge", "variable_om_cost"),
    ]
    # ──────────────────────────────────────────────────────────────────────────

    if field_map is None:
        field_map = DEFAULT_FIELD_MAP

    if isinstance(json_data, str):
        with open(json_data) as f:
            json_data = json.load(f)

    output_cols = [col for col, _, _ in field_map]
    rows = []

    for asset_type, asset_list in json_data.items():
        for asset in asset_list:
            for instance in asset.get("instance_data", []):
                row = {}
                transforms = instance.get("transforms", {})
                edges = instance.get("edges", {})

                for col_name, source, json_key in field_map:
                    if source == "id":
                        row[col_name] = instance.get(json_key)
                    elif source == "transforms":
                        row[col_name] = transforms.get(json_key)
                    elif source.startswith("edge:"):
                        edge_name = source[len("edge:"):]
                        row[col_name] = edges.get(edge_name, {}).get(json_key)
                    else:
                        raise ValueError(f"Unknown source '{source}' for column '{col_name}'")

                rows.append(row)

    if output_path:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=output_cols)
            writer.writeheader()
            writer.writerows(rows)
        print(f"Written to {output_path}")
    else:
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=output_cols)
        writer.writeheader()
        writer.writerows(rows)
        print(output.getvalue())

    return rows

# Default mapping
with open(f"{manual_file_path}/assets/synthetic_ethylene.json") as f:
    data = json.load(f)
rows = json_to_csv_transforms(data, output_path=f"{manual_file_path}/assets/synthetic_ethylene.csv")

print("DONE JSON TURNED TO CSV")