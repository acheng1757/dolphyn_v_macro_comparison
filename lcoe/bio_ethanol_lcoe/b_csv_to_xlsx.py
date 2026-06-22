import sys
import json
import pandas as pd
from openpyxl import load_workbook

# change this manual file path!
manual_file_path = "/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/9Zone_US/allethylene_168hr"

sys.path.append("/Users/abbie/MacroEnergy-Abbie.jl")
from MacroEnergyExamples.lcoe_plots.bio_ethanol_lcoe.a_json_to_csv import json_to_csv_transforms

ASSETS_PATH = f'{manual_file_path}/assets/'
XLSX_PATH = "/Users/abbie/MacroEnergy-Abbie.jl/MacroEnergyExamples/lcoe_plots/bio_ethanol_lcoe/LCOE_BIOETHANOL.xlsx"

json_files = [
    "bioethanol.json",
    "drymillethanol.json",
    "drymillccsethanol_retrofit_option.json",
]

CSV_TO_XLSX_MAP = {
    "id":                  "id",
    "commodity":           "commodity",
    "elec_consumption":    "elec_consumption (MWh/t-bio)",
    "elec_production":     "elec_production (MWh/t-bio)",
    "ethanol_production": "ethanol_production (MWh-ethanol/t-bio)",
    "natgas_consumption":  "natgas_consumption (MWh/t-bio)",
    "co2_biomass_content":  "co2_biomass_content (t-CO2/t-bio)",
    "capture_rate":        "capture_rate (t-CO2/t-bio)",
    "emission_rate":       "emission_rate (t-CO2/t-bio)",
    "investment_cost":     "investment_cost ($/yr per t-bio/hr)",
    "fixed_om_cost":       "fixed_om_cost ($/yr per t-bio/hr)",
    "variable_om_cost":    "variable_om_cost ($/t-bio)",
}

FIELDS = list(CSV_TO_XLSX_MAP.keys())

all_rows = []
for json_file in json_files:
    with open(ASSETS_PATH + json_file) as f:
        data = json.load(f)
    rows = json_to_csv_transforms(data)
    all_rows.extend(rows)

combined_df = pd.DataFrame(all_rows)

wb = load_workbook(XLSX_PATH)
ws = wb.active

HEADER_ROW = 3
DATA_START_ROW = 4

xlsx_header_to_idx = {}
for cell in ws[HEADER_ROW]:
    if cell.value is not None:
        xlsx_header_to_idx[cell.value] = cell.column

csv_field_to_col_idx = {}
for csv_field, xlsx_header in CSV_TO_XLSX_MAP.items():
    if xlsx_header in xlsx_header_to_idx:
        csv_field_to_col_idx[csv_field] = xlsx_header_to_idx[xlsx_header]

for r_offset, row_data in enumerate(combined_df.itertuples(index=False)):
    for csv_field, col_idx in csv_field_to_col_idx.items():
        value = getattr(row_data, csv_field, None)
        ws.cell(row=DATA_START_ROW + r_offset, column=col_idx, value=value)

wb.save(XLSX_PATH)
print(f"Done! {len(combined_df)} rows written.")
print("DONE CSV POPULATED INTO XLSX")