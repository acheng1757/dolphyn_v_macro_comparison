import json
import csv
import glob
import io
import os
import shutil
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
sys.path.append(REPO_ROOT)
from Step_1_Process_Macro_Flows_and_Balance_Demand import macro_base_dir, scenario_names, macro_input_paths


# ── DEFAULT FIELD MAP ──────────────────────────────────────────────────────
DEFAULT_FIELD_MAP = [
    ("id",                                          "id",                          "id"),
    ("commodity",                                   "edge:ethane_consumption_edge", "commodity"),
    ("h2_consumption",             "transforms",                  "h2_consumption"),
    ("h2_production",              "transforms",                  "h2_production"),
    ("elec_consumption",           "transforms",                  "elec_consumption"),
    ("ethylene_production", "transforms",                  "ethylene_production"),
    ("natgas_consumption",         "transforms",                  "natgas_consumption"),
    ("natgas_production",          "transforms",                  "natgas_production"),
    ("process_capture_rate",             "transforms",                  "process_capture_rate"),
    ("process_emission_rate",            "transforms",                  "process_emission_rate"),
    ("fuel_capture_rate",             "transforms",                  "fuel_capture_rate"),
    ("fuel_emission_rate",            "transforms",                  "fuel_emission_rate"),
    ("investment_cost",        "edge:ethane_consumption_edge", "investment_cost"),
    ("fixed_om_cost",          "edge:ethane_consumption_edge", "fixed_om_cost"),
    ("variable_om_cost",             "edge:ethane_consumption_edge", "variable_om_cost"),
]
# ──────────────────────────────────────────────────────────────────────────

# Zones whose steam-cracker retrofit options should be pulled into the CSV.
RETROFIT_ZONES = {"TX", "NCEN", "CEN", "SE", "MIDAT"}


def retrofit_rows_from_existing(existing_json_data, retrofit_json_data, field_map=None):
    """
    Build one CSV row per retrofit option found in existing_json_data's
    "retrofit_options" lists, restricted to RETROFIT_ZONES.

    Each row reuses the field values of the matching instance in
    retrofit_json_data (matched via "template_id" == that instance's "id"),
    except "investment_cost", which comes from the retrofit option's own
    edges.ethane_consumption_edge.investment_cost in existing_json_data.
    """
    if field_map is None:
        field_map = DEFAULT_FIELD_MAP

    retrofit_templates = {}
    for asset_type, asset_list in retrofit_json_data.items():
        for asset in asset_list:
            for instance in asset.get("instance_data", []):
                retrofit_templates[instance["id"]] = instance

    rows = []
    for asset_type, asset_list in existing_json_data.items():
        for asset in asset_list:
            for instance in asset.get("instance_data", []):
                for option in instance.get("retrofit_options", []):
                    template_id = option["template_id"]
                    zone = template_id.split("_F-")[0]
                    if zone not in RETROFIT_ZONES:
                        continue

                    template = retrofit_templates.get(template_id)
                    if template is None:
                        print(f"Warning: no steamcracker_retrofit_option template found for template_id '{template_id}'")
                        continue

                    transforms = template.get("transforms", {})
                    edges = template.get("edges", {})

                    row = {}
                    for col_name, source, json_key in field_map:
                        if source == "id":
                            row[col_name] = option.get(json_key)
                        elif source == "transforms":
                            row[col_name] = transforms.get(json_key)
                        elif source.startswith("edge:"):
                            edge_name = source[len("edge:"):]
                            row[col_name] = edges.get(edge_name, {}).get(json_key)
                        else:
                            raise ValueError(f"Unknown source '{source}' for column '{col_name}'")

                    row["investment_cost"] = option["edges"]["ethane_consumption_edge"]["investment_cost"]
                    rows.append(row)

    return rows


def json_to_csv_transforms(json_data, output_path=None, field_map=None, extra_rows=None):
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
                   If None, uses DEFAULT_FIELD_MAP.
        extra_rows: optional list of pre-built row dicts to append after the
                    rows extracted from json_data.
    """

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

    if extra_rows:
        rows.extend(extra_rows)

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

# (json filename in <scenario>/assets/, output csv filename, field_map override)
ASSET_FILES = [
    ("steamcracker_retrofit_option.json", "steamcracker_retrofit_option.csv", None),
    ("existing_steam_crackers.json", "existing_steam_crackers.csv", None),
]

if __name__ == "__main__":
    for entry in os.listdir(SCRIPT_DIR):
        if entry == "__pycache__" or entry.startswith("."):
            continue
        entry_path = os.path.join(SCRIPT_DIR, entry)
        if os.path.isdir(entry_path):
            shutil.rmtree(entry_path)

    for pattern in ("LCOE_SC_ESC_*.csv", "LCOE_SC_ESC_*.xlsx"):
        for path in glob.glob(os.path.join(SCRIPT_DIR, pattern)):
            if os.path.basename(path) == "LCOE_SC_ESC_TEMPLATE.xlsx":
                continue
            os.remove(path)

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

            extra_rows = None
            if json_name == "existing_steam_crackers.json":
                retrofit_json_path = os.path.join(assets_dir, "steamcracker_retrofit_option.json")
                if os.path.exists(retrofit_json_path):
                    with open(retrofit_json_path) as f:
                        retrofit_data = json.load(f)
                    extra_rows = retrofit_rows_from_existing(data, retrofit_data, field_map)

            json_to_csv_transforms(data, output_path=os.path.join(out_dir, csv_name), field_map=field_map, extra_rows=extra_rows)

    print("DONE JSON TURNED TO CSV FOR ALL SCENARIOS")
