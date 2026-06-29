import json
import csv
import io
import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
sys.path.append(REPO_ROOT)
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_input_paths


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
    # For assets whose fields are nested under "transforms"/"edges"
    # (e.g. existing_drymill.json, drymill_ccs_retrofit_option.json).
    # Each entry: (output column name, source, json key)
    # source = "id" | "transforms" | "edge:<edge_name>"
    DEFAULT_FIELD_MAP = [
        ("id",                                          "id",                          "id"),
        ("commodity",                                   "edge:biomass_consumption_edge", "commodity"),
        ("elec_production",             "transforms",                  "elec_production"),
        ("elec_consumption",              "transforms",                  "elec_consumption"),
        ("ethanol_production", "transforms",                  "ethanol_production"),
        ("natgas_consumption",         "transforms",                  "natgas_consumption"),
        ("co2_biomass_content",         "transforms",                  "co2_biomass_content"),
        ("process_capture_rate",     "transforms",                  "process_capture_rate"),
        ("process_emission_rate",    "transforms",                  "process_emission_rate"),
        ("fuel_capture_rate",        "transforms",                  "fuel_capture_rate"),
        ("fuel_emission_rate",       "transforms",                  "fuel_emission_rate"),
        ("investment_cost",        "edge:biomass_consumption_edge", "investment_cost"),
        ("fixed_om_cost",          "edge:biomass_consumption_edge", "fixed_om_cost"),
        ("variable_om_cost",             "edge:biomass_consumption_edge", "variable_om_cost"),
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


# For cellulosic_ethanol.json: fields live directly on the instance dict
# (no "transforms"/"edges" nesting), and the commodity key is named differently.
CELLULOSIC_FIELD_MAP = [
    ("id",                      "id", "id"),
    ("commodity",                "id", "biomass_consumption_commodity"),
    ("elec_production",          "id", "elec_production"),
    ("elec_consumption",         "id", "elec_consumption"),
    ("ethanol_production",       "id", "ethanol_production"),
    ("natgas_consumption",       "id", "natgas_consumption"),
    ("co2_biomass_content",      "id", "co2_biomass_content"),
    ("process_capture_rate",     "id", "process_capture_rate"),
    ("process_emission_rate",    "id", "process_emission_rate"),
    ("fuel_capture_rate",        "id", "fuel_capture_rate"),
    ("fuel_emission_rate",       "id", "fuel_emission_rate"),
    ("investment_cost",          "id", "investment_cost"),
    ("fixed_om_cost",            "id", "fixed_om_cost"),
    ("variable_om_cost",         "id", "variable_om_cost"),
]

# (json filename in <scenario>/assets/, output csv filename, field_map override)
ASSET_FILES = [
    ("cellulosic_ethanol.json", "cellulosic_ethanol.csv", CELLULOSIC_FIELD_MAP),
    ("existing_drymill.json", "existing_drymill.csv", None),
    ("drymill_ccs_retrofit_option.json", "drymill_ccs_retrofit_option.csv", None),
]


if __name__ == "__main__":
    for label in scenario_names:
        assets_dir = os.path.join(macro_base_dir, macro_input_paths[label], "assets")
        out_dir = os.path.join(SCRIPT_DIR, label)
        os.makedirs(out_dir, exist_ok=True)

        for json_name, csv_name, field_map in ASSET_FILES:
            json_path = os.path.join(assets_dir, json_name)
            if not os.path.exists(json_path):
                print(f"Warning: asset file not found for scenario {label}: {json_path}")
                continue
            with open(json_path) as f:
                data = json.load(f)
            json_to_csv_transforms(data, output_path=os.path.join(out_dir, csv_name), field_map=field_map)

    print("DONE JSON TURNED TO CSV FOR ALL SCENARIOS")
