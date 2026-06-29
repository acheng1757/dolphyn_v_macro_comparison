import os
import re
import pandas as pd

macro_base_dir = "/Users/abbie/MacroEnergyExamples.jl/macro"
dolphyn_base_dir = "/Users/abbie/Desktop/Dolphyn_to_Macro/Chaitanya_5_23/dolphyn"
dolphyn_results_folder = "Results_1"

_scenarios = [
    ("1", "6_29_SCENARIODEMONSTRATION/1_ethanol/results_001/results", "system"),
    ("2", "6_29_SCENARIODEMONSTRATION/2_ethanol/results_001/results", "system"),
    ("3", "6_29_SCENARIODEMONSTRATION/3_ethanol/results_001/results", "system"),
    ("4", "6_29_SCENARIODEMONSTRATION/4_ethanol/results_001/results", "system"),
    ("5", "6_29_SCENARIODEMONSTRATION/5_lf/results_001/results", "system"),
    ("5a", "6_29_SCENARIODEMONSTRATION/5a_lf/results_001/results", "system"),
    ("5b", "6_29_SCENARIODEMONSTRATION/5b_lf/results_001/results", "system"),
    ("6", "6_29_SCENARIODEMONSTRATION/6_ethylene/results_001/results", "system"),
    ("6a", "6_29_SCENARIODEMONSTRATION/6a_ethylene/results_001/results", "system"),
    #("6b", "6_29_SCENARIODEMONSTRATION/6b_ethylene/results_001/results", "system"),
    #("6c", "6_29_SCENARIODEMONSTRATION/6c_ethylene/results_001/results", "system"),
    #("6d", "6_29_SCENARIODEMONSTRATION/6d_ethylene/results_001/results", "system"),
    #("6e", "6_29_SCENARIODEMONSTRATION/6e_ethylene/results_001/results", "system"),
    #("6f", "6_29_SCENARIODEMONSTRATION/6f_ethylene/results_001/results", "system"),
    #("6g", "6_29_SCENARIODEMONSTRATION/6g_ethylene/results_001/results", "system"),
]

carbon_end_use_dict = { # tonne CO2/MWh fuel using molar ratios
    "gasoline" : 0.243968185,
    "jetfuel" : 0.246356685,
    "diesel" : 0.249427613,
    "naturalgas" : 0.1828908353,
    "ethanol" : 0.230374912051, #t-CO2/MWh-ethanol (calculated)
}

scenario_names          = [label  for label, _,    _   in _scenarios]
scenario_folders        = [path   for _,     path, _   in _scenarios]
scenario_labels         = {path:  label for label, path, _   in _scenarios}
macro_scenario_paths    = {label: path  for label, path, _   in _scenarios}
scenario_system_folders = {path:  sys   for _,     path, sys in _scenarios}
macro_input_paths       = {
    label: re.sub(r"/results_\d+/results$", "", path)
    for label, path, _ in _scenarios
}

chunk_size = 50_000
annual_flow_tolerance = 1e-8

sector_definitions = {
    "Power": {
        "categories": [
            ("NG CCS", [
                r"^NG CCS$",
                r"naturalgas_ccccsavgcf",
                r"naturalgas_ccccs",
                r"natural.*ccs",
            ]),
            ("NG", [
                r"^NG$",
                r"naturalgas_ccavgcf",
                r"naturalgas_ctavgcf",
                r"natural_gas",
                r"natural(?!.*ccs)",
            ]),
            ("H2 CCGT", [r"ccgt[-_]?h2"]),
            ("H2 OCGT", [r"ocgt[-_]?h2"]),
            ("Nuclear", [
                r"^Nuclear$",
                r"nuclear",
            ]),
            ("Hydro Pumped Storage", [
                r"hydroelectric_pumped_storage",
                r"pumped.*storage",
            ]),
            ("Hydro", [
                r"^Hydro$",
                r"conventional_hydroelectric",
                r"small_hydroelectric",
            ]),
            ("Battery", [
                r"battery",
            ]),
            ("Solar", [
                r"^Solar$",
                r"solar",
                r"photovoltaic",
                r"utilitypv",
                r"(^|_)pv($|_)",
            ]),
            ("Wind", [
                r"^Wind$",
                r"wind",
            ]),
        ],
    },

    "Hydrogen": {
        "categories": [
            ("Electrolyzer", [
                r"^Electrolyzer$",
                r"electrolyzer",
            ]),
            ("NG CCS H2", [
                r"^NG CCS H2$",
                r"atr",
                r"smr",
            ]),
            ("H2 Stor Comp", [
                r"^ground_storage$",
                r"ground_storage",
                r"above_ground_storage",
            ]),
        ],
    },

    "CO2": {
        "categories": [
            ("Solvent w/ NGCC DAC", [
                r"^Solvent_wNGCC_DAC$",
                r"solvent_wngcc_dac",
            ]),
            ("Sorbent DAC", [
                r"^Sorbent_DAC$",
                r"sorbent_dac",
            ]),
            ("Sorbent w/ NGCC DAC", [
                r"^Sorbent_wNGCC_DAC$",
                r"sorbent_wngcc_dac",
            ]),
        ],
    },

    "CO2 Storage": {
        "categories": [
            ("CO2 Injection", [
                r"co2_injection",
            ]),
        ],
    },

    "Liquid fuels": {
        "categories": [
            ("Fossil Petroleum Refinery", [
                r"global_fossil_petroleum",
            ]),
            ("Fossil Liquid Fuels", [
                r"Global_Gasoline_Fossil_Upstream",
                r"Global_Diesel_Fossil_Upstream",
                r"Global_Jetfuel_Fossil_Upstream",
            ]),
            ("Gasoline Use", [
                r"global_gasoline_use_co2",
                r"global_gasoline_use_fuel_edge",
            ]),
            ("Gasoline 1a Use", [
                r"global_gasoline_1a_use_co2",
                r"global_gasoline_1a_use_fuel_edge",
            ]),
            ("Gasoline 1b Use", [
                r"global_gasoline_1b_use_co2",
                r"global_gasoline_1b_use_fuel_edge",
            ]),
            ("Diesel Use", [
                r"global_diesel_use_co2",
                r"global_diesel_use_fuel_edge",
            ]),
            ("Diesel 1a Use", [
                r"global_diesel_1a_use_co2",
                r"global_diesel_1a_use_fuel_edge",
            ]),
            ("Diesel 1b Use", [
                r"global_diesel_1b_use_co2",
                r"global_diesel_1b_use_fuel_edge",
            ]),
            ("Jetfuel Use", [
                r"global_jetfuel_use_co2",
                r"global_jetfuel_use_fuel_edge",
            ]),
            ("Jetfuel 1 Use", [
                r"global_jetfuel_1_use_co2",
                r"global_jetfuel_1_use_fuel_edge",
            ]),
        ],
    },

    # Ethanol-upgrading plants get their own sector rather than being
    # folded into "Transmission" (which is reserved for real zone-to-zone
    # electricity/NG/H2 transfers) or "Liquid fuels" (whose category match
    # would otherwise grab every edge of the plant, not just its fuel
    # output). Must be checked before "Transmission" below, since that
    # sector's catch-all r"_to_" pattern would otherwise match first.
    "Ethanol Upgrading": {
        "categories": [
            ("Ethanol Upgrading", [
                r"Ethanol_to_",
            ]),
        ],
    },

    "Transmission": {
        "categories": [
            ("Transmission", [
                r"_to_",
            ]),
        ],
    },

    "NG": {
        "categories": [
            ("NG End Use", [
                r"ng_end_use",
                r"natgas_end_use",
                r"NG_End_Use",
            ]),
            ("NG Fossil Upstream", [
                r"ng_fossil_upstream",
                r"natgas_fossil_upstream",
                r"NG_Fossil_Upstream",
            ]),
        ],
    },

    "Bioenergy": {
        "categories": [
            ("B-G", [
                r"^Gasification_Non_CCS$",
                r"(^|_)B-G($|_)",
                r"Gasification.*Non.*CCS",
            ]),
            ("B-G-CC31", [
                r"^Gasification_CCS_31$",
                r"(^|_)B-G-CC31($|_)",
                r"Gasification.*CCS.*31",
            ]),
            ("B-G-CC99", [
                r"^Gasification_CCS_99$",
                r"(^|_)B-G-CC99($|_)",
                r"Gasification.*CCS.*99",
            ]),

            ("B-NG", [
                r"^Bio_NG$",
                r"(^|_)B-NG($|_)",
                r"(^|_)Bio_NG(?!_CCS)($|_)",
            ]),
            ("B-NG-CC40", [
                r"^Bio_NG_CCS_40$",
                r"(^|_)B-NG-CC40($|_)",
                r"Bio_NG_CCS_40",
            ]),
            ("B-NG-CC99", [
                r"^Bio_NG_CCS_99$",
                r"(^|_)B-NG-CC99($|_)",
                r"Bio_NG_CCS_99",
            ]),

            ("B-D", [
                r"^High_Diesel$",
                r"(^|_)B-D($|_)",
                r"High_Diesel(?!_CCS)",
                r"Diesel.*Non",
            ]),
            ("B-D-CC53", [
                r"^High_Diesel_CCS_53$",
                r"(^|_)B-D-CC53($|_)",
                r"Diesel.*CCS.*53",
            ]),
            ("B-D-CC99", [
                r"^High_Diesel_CCS_99$",
                r"(^|_)B-D-CC99($|_)",
                r"Diesel.*CCS.*99",
            ]),

            ("B-J-CC75", [
                r"^High_Jetfuel_CCS_75$",
                r"(^|_)B-J-CC75($|_)",
                r"Jet.*CCS.*75",
            ]),
            ("B-J-CC84", [
                r"^High_Jetfuel_CCS_84$",
                r"(^|_)B-J-CC84($|_)",
                r"Jet.*CCS.*84",
            ]),
            ("B-J-CC99", [
                r"^High_Jetfuel_CCS_99$",
                r"(^|_)B-J-CC99($|_)",
                r"Jet.*CCS.*99",
            ]),

            ("B-H2", [
                r"^Bio_H2$",
                r"(^|_)B-H2($|_)",
                r"(^|_)Bio_H2(?!_CCS)($|_)",
                r"Bio.*Hydrogen(?!.*CCS)",
            ]),
            ("B-H2-CC99", [
                r"^Bio_H2_CCS_99$",
                r"(^|_)B-H2-CC99($|_)",
                r"Bio_H2_CCS_99",
                r"Bio.*H2.*CCS.*99",
                r"Bio.*Hydrogen.*CCS.*99",
            ]),
            ("B-E-CC93", [
                r"^Bio_Electricity$",
                r"(^|_)B-E-CC93($|_)",
                r"Bio_Electricity",
                r"Bio.*Electricity.*CCS.*93",
            ]),
        ],
    },
    "Synthetic fuels": {
        "categories": [
            ("S-J", [
                r"^Synfuel_Plant$",
                r"(^|_)S-J($|_)",
                r"(^|_)Synfuel_Plant(?!_wCCS)($|_)",
                r"Synfuel_Plant(?!.*CCS)",
            ]),
            ("S-J-CC99", [
                r"^Synfuel_Plant_wCCS$",
                r"(^|_)S-J-CC99($|_)",
                r"Synfuel_Plant_wCCS",
                r"Synfuel.*wCCS.*99",
            ]),
            ("S-NG", [
                r"^Syn_NG_Plant$",
                r"(^|_)S-NG($|_)",
                r"(^|_)Syn_NG_Plant($|_)",
            ]),
        ],
    },
    "Ethylene": {
    "categories": [
        ("Ethylene Use", [r"Global_Ethylene_Use"]),
        ("TSC", [
            r"_F(-|_)NGin_ethylene",           # F-NGin without H2out (the underscore after prevents matching F-NGin-H2out)
        ]),
        ("Ret-TSC", [
            r"_F(-|_)NGin_RETROFIT_ethylene",
        ]),
        ("Existing TSC:H2", [
            r"Existing_.*F(-|_)NGin(-|_)H2out_ethylene",
        ]),
        ("TSC:H2", [
            r"_F(-|_)NGin(-|_)H2out_ethylene",
        ]),
        ("Ret-TSC:H2", [
            r"_F(-|_)NGin(-|_)H2out_RETROFIT_ethylene",  # in case separator varies
        ]),
        ("TSC+CC90", [
            r"_F(-|_)CC90(-|_)NGin_ethylene",
            r"TSC+CC90",
        ]),
        ("Ret-TSC+CC90", [
            r"_F(-|_)CC90(-|_)NGin_RETROFIT_ethylene",
            r"Ret-TSC+CC90",
        ]),
        ("TSC+CC90:H2", [
            r"_F(-|_)CC90(-|_)NGin(-|_)H2out_ethylene",
        ]),
        ("Ret-TSC+CC90:H2", [
            r"_F(-|_)CC90(-|_)NGin(-|_)H2out_RETROFIT_ethylene",
        ]),
        ("TSC+H2in", [
            r"_F(-|_)H2in_ethylene",
        ]),
        ("Ret-TSC+H2in", [
            r"_F(-|_)H2in_RETROFIT_ethylene",
        ]),
        ("TSC+H2in:CH4", [
            r"_F(-|_)H2in(-|_)CH4out_ethylene",
            r"TSC+H2in:CH4",
        ]),
        ("Ret-TSC+H2in:CH4", [
            r"_F(-|_)H2in(-|_)CH4out_RETROFIT_ethylene",
            r"RET-TSC+H2in:CH4",
        ]),
        ("ESC", [
            r"(-|_)F(-|_)Ein_ethylene",
            r"ESC",
        ]),
        ("Ret-ESC", [
            r"(-|_)F(-|_)Ein_RETROFIT_ethylene",
        ]),
        ("MS+MTO", [
            r"_S(-|_)H2in_ethylene",           # S-H2in without CC90
        ]),
        ("MS+MTO+CC90", [
            r"_S(-|_)CC90(-|_)H2in_ethylene",
        ]),
        ("Dehydration NGfuel", [
            r"_B(-|_)NGin_ethylene",
            r"Bio-eth+CC88:NG",
        ]),
        ("Dehydration H2fuel", [
            r"_B(-|_)H2in_ethylene",
            r"Bio-eth+CC88:H2",
        ]),
        ("Dehydration NGfuel Ethanol", [
            r"_B(-|_)NGin_ethanol_consumption_edge",
        ]),
        ("Dehydration H2fuel Ethanol", [
            r"_B(-|_)H2in_ethanol_consumption_edge",
        ]),
        ("Ethylene Aux", [
            # All auxiliary (non-ethylene-production) edges for every
            # ethylene technology. Negative lookaheads prevent overlap
            # with the production-edge patterns above.
            r"_F(-|_)NGin[_-](?!ethylene)",
            r"_F(-|_)CC90(-|_)NGin[_-](?!ethylene)",
            r"_F(-|_)H2in[_-](?!ethylene|ethanol)",
            r"_F(-|_)Ein[_-](?!ethylene)",
            r"_S(-|_)H2in[_-](?!ethylene)",
            r"_S(-|_)CC90(-|_)H2in[_-](?!ethylene)",
            r"_B(-|_)NGin[_-](?!ethylene|ethanol)",
            r"_B(-|_)H2in[_-](?!ethylene|ethanol)",
        ]),
    ],
},
"Ethanol": {
    "categories": [
        ("DryMill_CCS_Fermentation_RETROFIT", [       # must come before DryMill_CCS_60
            r"_DryMill_CCS_60_RETROFIT",
            r"_DryMill_CCS_Fermentation_RETROFIT",
        ]),
        ("DryMill_CCS_Fermentation_Exhaust_RETROFIT", [       # must come before DryMill_CCS_90
            r"_DryMill_CCS_90_RETROFIT",
            r"_DryMill_CCS_Fermentation_Exhaust_RETROFIT",
        ]),
        ("DryMill_Existing_Non_CCS", [
            r"_DryMill_Existing_Non_CCS",
        ]),
        ("DryMill_CCS_Fermentation", [               # safe now — RETROFIT already caught above
            r"_DryMill_CCS_60",
            r"_DryMill_CCS_Fermentation",
        ]),
        ("DryMill_CCS_Fermentation_Exhaust", [               # add this if you have it
            r"_DryMill_CCS_90",
            r"_DryMill_CCS_Fermentation_Exhaust",
        ]),
        ("Bio_Ethanol_CCS_20", [           # must come before plain Bio_Ethanol_
            r"_Bio_Ethanol_CCS_20",
        ]),
        ("Bio_Ethanol_CCS_86", [           # must come before plain Bio_Ethanol_
            r"_Bio_Ethanol_CCS_86",
        ]),
        ("Bio_Ethanol_Non_CCS", [          # catch-all for plain bio ethanol — last
            r"_Bio_Ethanol_(?!CCS)",       # negative lookahead to be extra safe
        ]),
        ("Ethanol End Use", [
            r"_ethanol_end_use",
        ]),
        ("Gasoline Blending", [
            r"_Global_Gasoline_Blending",
        ]),
    ],
},
}

# ---------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------

def match_sector_and_category(edge_name, sector_definitions):
    """
    Return sector and category for an edge/resource name.
    If no match is found, return ("NA", "NA").
    """
    edge_name = str(edge_name)

    for sector_name, sector_info in sector_definitions.items():
        for category_name, patterns in sector_info["categories"]:
            for pattern in patterns:
                if re.search(pattern, edge_name, flags=re.IGNORECASE):
                    return sector_name, category_name

    return "NA", "NA"


def safe_filename(name):
    return (
        str(name)
        .strip()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
    )


def get_scenario_root_from_results_scenario(scenario):
    """
    Convert:
        NineZones_X_Biomass_X_CO2/results_006/results
    to:
        NineZones_X_Biomass_X_CO2
    """
    return re.split(r'/results_\d+/results', scenario)[0]


def get_demand_path_for_scenario(scenario):
    """
    Demand file is located in:
        <macro_base_dir>/<scenario_root>/<system_folder>/demand.csv
    """
    scenario_root = get_scenario_root_from_results_scenario(scenario)
    system_folder = scenario_system_folders.get(scenario, "system")

    return os.path.join(
        macro_base_dir,
        scenario_root,
        system_folder,
        "demand.csv",
    )


def compute_annual_flows_in_batches(flows_path, time_weights_path, chunk_size=50_000):
    """
    Compute annual weighted flow for every flow column without loading the full
    flows.csv into memory at once.
    """
    if not os.path.exists(flows_path):
        raise FileNotFoundError(f"flows.csv not found: {flows_path}")

    if not os.path.exists(time_weights_path):
        raise FileNotFoundError(f"time_weights.csv not found: {time_weights_path}")

    time_weights = pd.read_csv(time_weights_path)
    time_weights.columns = time_weights.columns.str.strip()

    if "time" not in time_weights.columns:
        raise ValueError("time_weights.csv must contain a column named 'time'.")

    if "weight" not in time_weights.columns:
        raise ValueError("time_weights.csv must contain a column named 'weight'.")

    time_weights["time"] = pd.to_numeric(time_weights["time"], errors="coerce")
    time_weights["weight"] = pd.to_numeric(time_weights["weight"], errors="coerce")

    if time_weights["time"].isna().any():
        raise ValueError("Some time values in time_weights.csv could not be parsed as numeric.")

    if time_weights["weight"].isna().any():
        raise ValueError("Some weight values in time_weights.csv could not be parsed as numeric.")

    weight_map = dict(zip(time_weights["time"], time_weights["weight"]))

    annual_sums = None
    flow_cols = None
    total_rows = 0

    for chunk_id, chunk in enumerate(pd.read_csv(flows_path, chunksize=chunk_size), start=1):
        chunk.columns = chunk.columns.str.strip()

        if "time" not in chunk.columns:
            raise ValueError("flows.csv must contain a column named 'time'.")

        chunk["time"] = pd.to_numeric(chunk["time"], errors="coerce")

        if chunk["time"].isna().any():
            raise ValueError(
                f"Some time values in flows.csv chunk {chunk_id} could not be parsed as numeric."
            )

        if flow_cols is None:
            flow_cols = [c for c in chunk.columns if c != "time"]
            annual_sums = pd.Series(0.0, index=flow_cols, dtype="float64")
        else:
            current_flow_cols = [c for c in chunk.columns if c != "time"]

            if current_flow_cols != flow_cols:
                raise ValueError(
                    f"Column mismatch in flows.csv chunk {chunk_id}. "
                    "All chunks must have the same columns."
                )

        weights = chunk["time"].map(weight_map)

        if weights.isna().any():
            missing_times = chunk.loc[
                weights.isna(),
                "time",
            ].drop_duplicates().tolist()

            raise ValueError(f"Missing time weights for time steps: {missing_times}")

        flow_data = chunk[flow_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)
        weighted_sum = flow_data.mul(weights, axis=0).sum(axis=0)

        annual_sums = annual_sums.add(weighted_sum, fill_value=0.0)

        total_rows += len(chunk)
        print(f"  Processed chunk {chunk_id}: {len(chunk)} rows")

    if flow_cols is None:
        raise ValueError(f"No data found in flows.csv: {flows_path}")

    print(f"  Total flow rows processed: {total_rows}")

    return annual_sums


def build_nonzero_annual_flow_table(annual_sums, scenario, scenario_label):
    """
    Convert annual sums into long-format nonzero annual-flow table with
    Sector and Category tags.
    """
    records = []

    for edge, annual_flow in annual_sums.items():
        if abs(annual_flow) <= annual_flow_tolerance:
            continue

        sector, category = match_sector_and_category(edge, sector_definitions)

        records.append({
            "Scenario": scenario,
            "ScenarioLabel": scenario_label,
            "Edge": edge,
            "Annual_Flow": annual_flow,
            "Sector": sector,
            "Category": category,
        })

    df = pd.DataFrame(records)

    if len(df) == 0:
        return pd.DataFrame(
            columns=[
                "Scenario",
                "ScenarioLabel",
                "Edge",
                "Annual_Flow",
                "Sector",
                "Category",
            ]
        )

    df = (
        df
        .sort_values(
            ["Sector", "Category", "Annual_Flow"],
            ascending=[True, True, False],
        )
        .reset_index(drop=True)
    )

    return df


def compute_annual_demand_rows(demand_path, time_weights_path, scenario, scenario_label):
    """
    Compute annual electricity and hydrogen demand rows.

    Electricity_MW_* columns are assigned to:
        Sector   = Demand
        Category = Electricity Demand
        Balance  = Power

    Hydrogen_MW_* columns are assigned to:
        Sector   = Demand
        Category = Hydrogen Demand
        Balance  = H2

    Annual demand is stored as negative Annual_Flow.
    """
    if not os.path.exists(demand_path):
        raise FileNotFoundError(f"demand.csv not found: {demand_path}")

    if not os.path.exists(time_weights_path):
        raise FileNotFoundError(f"time_weights.csv not found: {time_weights_path}")

    demand = pd.read_csv(demand_path)
    time_weights = pd.read_csv(time_weights_path)

    demand.columns = demand.columns.str.strip()
    time_weights.columns = time_weights.columns.str.strip()

    if "Time_Index" not in demand.columns:
        raise ValueError("demand.csv must contain a column named 'Time_Index'.")

    if "time" not in time_weights.columns:
        raise ValueError("time_weights.csv must contain a column named 'time'.")

    if "weight" not in time_weights.columns:
        raise ValueError("time_weights.csv must contain a column named 'weight'.")

    demand["Time_Index"] = pd.to_numeric(demand["Time_Index"], errors="coerce")
    time_weights["time"] = pd.to_numeric(time_weights["time"], errors="coerce")
    time_weights["weight"] = pd.to_numeric(time_weights["weight"], errors="coerce")

    if demand["Time_Index"].isna().any():
        raise ValueError("Some Time_Index values in demand.csv could not be parsed as numeric.")

    if time_weights["time"].isna().any():
        raise ValueError("Some time values in time_weights.csv could not be parsed as numeric.")

    if time_weights["weight"].isna().any():
        raise ValueError("Some weight values in time_weights.csv could not be parsed as numeric.")

    demand_weighted = demand.merge(
        time_weights[["time", "weight"]],
        left_on="Time_Index",
        right_on="time",
        how="left",
        validate="one_to_one",
    )

    if demand_weighted["weight"].isna().any():
        missing_times = demand_weighted.loc[
            demand_weighted["weight"].isna(),
            "Time_Index",
        ].tolist()

        raise ValueError(
            f"Missing time weights for demand time steps: {missing_times}"
        )

    electricity_cols = [
        c for c in demand.columns
        if c.lower().startswith("electricity_mw_")
    ]

    hydrogen_cols = [
        c for c in demand.columns
        if c.lower().startswith("hydrogen_mw_")
    ]

    ethylene_cols = [
        c for c in demand.columns
        if c.lower().startswith("ethylene_")
    ]

    ethanol_cols = [
        c for c in demand.columns
        if c.lower().startswith("ethanol_mw")
    ]

    naturalgas_cols = [
        c for c in demand.columns
        if c.lower().startswith("naturalgas_mw_")
    ]

    gasoline_cols = [
        c for c in demand.columns
        if c.lower().startswith("gasoline_mw_")
    ]

    diesel_cols = [
        c for c in demand.columns
        if c.lower().startswith("diesel_mw_")
    ]

    jetfuel_cols = [
        c for c in demand.columns
        if c.lower().startswith("jetfuel_mw_")
    ]

    if len(electricity_cols) == 0:
        print(f"  Warning: no electricity demand columns found in {demand_path}")

    if len(hydrogen_cols) == 0:
        print(f"  Warning: no hydrogen demand columns found in {demand_path}")

    if len(ethylene_cols) == 0:
        print(f"  Warning: no ethylene demand columns found in {demand_path}")

    if len(ethanol_cols) == 0:
        print(f"  Warning: no ethanol demand columns found in {demand_path}")

    if len(naturalgas_cols) == 0:
        print(f"  Warning: no natural gas demand columns found in {demand_path}")

    if len(gasoline_cols) == 0:
        print(f"  Warning: no gasoline demand columns found in {demand_path}")

    if len(diesel_cols) == 0:
        print(f"  Warning: no diesel demand columns found in {demand_path}")

    if len(jetfuel_cols) == 0:
        print(f"  Warning: no jetfuel demand columns found in {demand_path}")

    rows = []

    def add_demand_rows(cols, balance_name, category_name):
        for col in cols:
            demand_weighted[col] = pd.to_numeric(
                demand_weighted[col],
                errors="coerce",
            ).fillna(0.0)

            annual_demand = -(
                demand_weighted[col] * demand_weighted["weight"]
            ).sum()

            if abs(annual_demand) <= annual_flow_tolerance:
                continue

            rows.append({
                "Scenario": scenario,
                "ScenarioLabel": scenario_label,
                "Edge": col,
                "Annual_Flow": annual_demand,
                "Sector": "Demand",
                "Category": category_name,
                "Balance": balance_name,
            })

    add_demand_rows(
        electricity_cols,
        balance_name="Power",
        category_name="Electricity Demand",
    )

    add_demand_rows(
        hydrogen_cols,
        balance_name="H2",
        category_name="Hydrogen Demand",
    )

    add_demand_rows(
        ethylene_cols,
        balance_name="Ethylene",
        category_name="Ethylene Demand",
    )

    add_demand_rows(
        ethanol_cols,
        balance_name="Ethanol",
        category_name="Ethanol Demand",
    )

    add_demand_rows(
        naturalgas_cols,
        balance_name="NG",
        category_name="NaturalGas Demand",
    )

    add_demand_rows(
        gasoline_cols,
        balance_name="Gasoline",
        category_name="Liquid Fuels Demand",
    )

    add_demand_rows(
        diesel_cols,
        balance_name="Diesel",
        category_name="Liquid Fuels Demand",
    )

    add_demand_rows(
        jetfuel_cols,
        balance_name="Jetfuel",
        category_name="Liquid Fuels Demand",
    )

    return pd.DataFrame(
        rows,
        columns=[
            "Scenario",
            "ScenarioLabel",
            "Edge",
            "Annual_Flow",
            "Sector",
            "Category",
            "Balance",
        ],
    )

def add_balance_labels(df):
    """
    Add Balance column to annual flow table.
    """
    df = df.copy()

    df["Balance"] = "NA"

    edge_lower = df["Edge"].astype(str).str.lower()
    sector_lower = df["Sector"].astype(str).str.strip().str.lower()

    # -----------------------------------------------------------------
    # Power sector
    # -----------------------------------------------------------------

    is_power = sector_lower == "power"

    exclude_power_balance = (
        edge_lower.str.contains("spill", na=False) |
        edge_lower.str.contains("inflow", na=False)
    )

    is_power_captured_co2 = (
        is_power &
        (~exclude_power_balance) &
        edge_lower.str.contains("co2_captured", na=False)
    )
    df.loc[is_power_captured_co2, "Balance"] = "Captured_CO2"

    is_power_co2 = (
        is_power &
        (~exclude_power_balance) &
        edge_lower.str.contains("co2", na=False) &
        (~edge_lower.str.contains("captured", na=False))
    )
    df.loc[is_power_co2, "Balance"] = "CO2"

    is_power_h2_fuel = (
        is_power &
        (~exclude_power_balance) &
        edge_lower.str.contains("fuel_edge", na=False) &
        (
            edge_lower.str.contains("ocgt-h2", na=False) |
            edge_lower.str.contains("ccgt-h2", na=False) |
            edge_lower.str.contains("ocgt_h2", na=False) |
            edge_lower.str.contains("ccgt_h2", na=False)
        )
    )
    df.loc[is_power_h2_fuel, "Balance"] = "H2"

    is_power_ng = (
        is_power &
        (~exclude_power_balance) &
        (~is_power_h2_fuel) &
        edge_lower.str.contains("fuel", na=False) &
        edge_lower.str.contains("gas", na=False)
    )
    df.loc[is_power_ng, "Balance"] = "NG"

    is_power_nuclear_fuel = (
        is_power &
        (~exclude_power_balance) &
        edge_lower.str.contains("fuel", na=False) &
        edge_lower.str.contains("nuclear", na=False)
    )
    df.loc[is_power_nuclear_fuel, "Balance"] = "NA"

    is_power_remaining = (
        is_power &
        (~exclude_power_balance) &
        (df["Balance"] == "NA") &
        (~is_power_nuclear_fuel)
    )
    df.loc[is_power_remaining, "Balance"] = "Power"

    # -----------------------------------------------------------------
    # Hydrogen sector
    # -----------------------------------------------------------------

    is_hydrogen = sector_lower == "hydrogen"

    is_hydrogen_storage = (
        is_hydrogen &
        edge_lower.str.contains("storage", na=False)
    )
    df.loc[is_hydrogen_storage, "Balance"] = "NA"

    is_hydrogen_captured_co2 = (
        is_hydrogen &
        (~is_hydrogen_storage) &
        edge_lower.str.contains("co2_captured", na=False)
    )
    df.loc[is_hydrogen_captured_co2, "Balance"] = "Captured_CO2"

    is_hydrogen_co2 = (
        is_hydrogen &
        (~is_hydrogen_storage) &
        edge_lower.str.contains("co2", na=False) &
        (~edge_lower.str.contains("captured", na=False))
    )
    df.loc[is_hydrogen_co2, "Balance"] = "CO2"

    is_hydrogen_h2 = (
        is_hydrogen &
        (~is_hydrogen_storage) &
        edge_lower.str.contains("h2_edge", na=False)
    )
    df.loc[is_hydrogen_h2, "Balance"] = "H2"

    is_hydrogen_power = (
        is_hydrogen &
        edge_lower.str.contains("elec_edge", na=False)
    )
    df.loc[is_hydrogen_power, "Balance"] = "Power"

    is_hydrogen_ng = (
        is_hydrogen &
        (~is_hydrogen_storage) &
        edge_lower.str.contains("fuel", na=False)
    )
    df.loc[is_hydrogen_ng, "Balance"] = "NG"

    # -----------------------------------------------------------------
    # CO2 sector
    # -----------------------------------------------------------------

    is_co2_sector = sector_lower == "co2"

    is_co2_sector_captured_co2 = (
        is_co2_sector &
        edge_lower.str.contains("co2_captured_edge", na=False)
    )
    df.loc[is_co2_sector_captured_co2, "Balance"] = "Captured_CO2"

    is_co2_sector_power = (
        is_co2_sector &
        edge_lower.str.contains("elec_edge", na=False)
    )
    df.loc[is_co2_sector_power, "Balance"] = "Power"

    is_co2_sector_co2 = (
        is_co2_sector &
        (
            edge_lower.str.contains("co2_edge", na=False) |
            edge_lower.str.contains("co2_emission_edge|co2_process_emission_edge|co2_fuel_emission_edge", na=False)
        ) &
        (~edge_lower.str.contains("captured", na=False))
    )
    df.loc[is_co2_sector_co2, "Balance"] = "CO2"

    is_co2_sector_ng = (
        is_co2_sector &
        edge_lower.str.contains("natgas", na=False)
    )
    df.loc[is_co2_sector_ng, "Balance"] = "NG"

    # -----------------------------------------------------------------
    # Bioenergy sector
    # -----------------------------------------------------------------

    is_bioenergy = sector_lower == "bioenergy"

    is_bioenergy_biomass = (
        is_bioenergy &
        edge_lower.str.contains("biomass_edge", na=False)
    )
    df.loc[is_bioenergy_biomass, "Balance"] = "Biomass"

    is_bioenergy_diesel = (
        is_bioenergy &
        edge_lower.str.contains("diesel_edge", na=False)
    )
    df.loc[is_bioenergy_diesel, "Balance"] = "Diesel"

    is_bioenergy_jetfuel = (
        is_bioenergy &
        edge_lower.str.contains("jetfuel_edge", na=False)
    )
    df.loc[is_bioenergy_jetfuel, "Balance"] = "Jetfuel"

    is_bioenergy_gasoline = (
        is_bioenergy &
        edge_lower.str.contains("gasoline_edge", na=False)
    )
    df.loc[is_bioenergy_gasoline, "Balance"] = "Gasoline"

    is_bioenergy_captured_co2 = (
        is_bioenergy &
        edge_lower.str.contains("co2_captured", na=False)
    )
    df.loc[is_bioenergy_captured_co2, "Balance"] = "Captured_CO2"

    is_bioenergy_co2 = (
        is_bioenergy &
        (
            edge_lower.str.contains("co2_emission_edge|co2_process_emission_edge|co2_fuel_emission_edge", na=False) |
            edge_lower.str.contains("co2_edge", na=False) |
            edge_lower.str.contains("co2_content_edge", na=False) |
            edge_lower.str.contains("co2_edgedgee", na=False)
        ) &
        (~edge_lower.str.contains("captured", na=False))
    )
    df.loc[is_bioenergy_co2, "Balance"] = "CO2"

    is_bioenergy_power = (
        is_bioenergy &
        (
            edge_lower.str.contains("elec_edge", na=False) |
            edge_lower.str.contains("elec_consumption", na=False) |
            edge_lower.str.contains("elec_production", na=False)
        )
    )
    df.loc[is_bioenergy_power, "Balance"] = "Power"

    is_bioenergy_ng = (
        is_bioenergy &
        edge_lower.str.contains("natgas", na=False)
    )
    df.loc[is_bioenergy_ng, "Balance"] = "NG"

    is_bioenergy_h2 = (
        is_bioenergy &
        edge_lower.str.contains("h2_edge", na=False)
    )
    df.loc[is_bioenergy_h2, "Balance"] = "H2"

    # -----------------------------------------------------------------
    # Synthetic fuels sector
    # -----------------------------------------------------------------

    is_synthetic_fuels = sector_lower == "synthetic fuels"

    is_synthetic_fuels_diesel = (
        is_synthetic_fuels &
        edge_lower.str.contains("diesel_edge", na=False)
    )
    df.loc[is_synthetic_fuels_diesel, "Balance"] = "Diesel"

    is_synthetic_fuels_jetfuel = (
        is_synthetic_fuels &
        edge_lower.str.contains("jetfuel_edge", na=False)
    )
    df.loc[is_synthetic_fuels_jetfuel, "Balance"] = "Jetfuel"

    is_synthetic_fuels_gasoline = (
        is_synthetic_fuels &
        edge_lower.str.contains("gasoline_edge", na=False)
    )
    df.loc[is_synthetic_fuels_gasoline, "Balance"] = "Gasoline"

    is_synthetic_fuels_captured_co2 = (
        is_synthetic_fuels &
        (
            edge_lower.str.contains("co2_captured_edge", na=False) |
            edge_lower.str.contains("co2_captured_return_edge", na=False)
        )
    )
    df.loc[is_synthetic_fuels_captured_co2, "Balance"] = "Captured_CO2"

    is_synthetic_fuels_co2 = (
        is_synthetic_fuels &
        edge_lower.str.contains("co2_emission_edge|co2_process_emission_edge|co2_fuel_emission_edge", na=False)
    )
    df.loc[is_synthetic_fuels_co2, "Balance"] = "CO2"

    is_synthetic_fuels_h2 = (
        is_synthetic_fuels &
        edge_lower.str.contains("h2_edge", na=False)
    )
    df.loc[is_synthetic_fuels_h2, "Balance"] = "H2"

    is_synthetic_fuels_power = (
        is_synthetic_fuels &
        edge_lower.str.contains("elec_edge", na=False)
    )
    df.loc[is_synthetic_fuels_power, "Balance"] = "Power"

    is_synthetic_fuels_ng = (
        is_synthetic_fuels &
        edge_lower.str.contains("natgas", na=False)
    )
    df.loc[is_synthetic_fuels_ng, "Balance"] = "NG"

    # -----------------------------------------------------------------
    # CO2 Storage sector
    # -----------------------------------------------------------------

    is_co2_storage = sector_lower == "co2 storage"

    is_co2_storage_captured_co2 = (
        is_co2_storage &
        edge_lower.str.contains("co2_captured_edge", na=False)
    )
    df.loc[is_co2_storage_captured_co2, "Balance"] = "Captured_CO2"

    # -----------------------------------------------------------------
    # Liquid fuels sector
    # -----------------------------------------------------------------

    is_lf_sector = sector_lower == "liquid fuels"

    is_lf_gasoline = (
        is_lf_sector &
        (
            edge_lower.str.contains("global_gasoline_use_fuel_edge", na=False) |
            edge_lower.str.contains("global_fossil_petroleum_refinery_gasoline_edge", na=False) |
            edge_lower.str.contains("global_gasoline_fossil_upstream", na=False) |

            edge_lower.str.contains("global_gasoline_1a_use_fuel_edge", na=False) |
            edge_lower.str.contains("global_gasoline_1b_use_fuel_edge", na=False)
        )
    )
    df.loc[is_lf_gasoline, "Balance"] = "Gasoline"

    is_lf_jetfuel = (
        is_lf_sector &
        (
            edge_lower.str.contains("global_jetfuel_use_fuel_edge", na=False) |
            edge_lower.str.contains("global_fossil_petroleum_refinery_jetfuel_edge", na=False) |
            edge_lower.str.contains("global_jetfuel_fossil_upstream", na=False) |

            edge_lower.str.contains("global_jetfuel_1_use_fuel_edge", na=False)
        )
    )
    df.loc[is_lf_jetfuel, "Balance"] = "Jetfuel"

    is_lf_diesel = (
        is_lf_sector &
        (
            edge_lower.str.contains("global_diesel_use_fuel_edge", na=False) |
            edge_lower.str.contains("global_fossil_petroleum_refinery_diesel_edge", na=False) |
            edge_lower.str.contains("global_diesel_fossil_upstream", na=False) |

            edge_lower.str.contains("global_diesel_1a_use_fuel_edge", na=False) |
            edge_lower.str.contains("global_diesel_1b_use_fuel_edge", na=False)
        )
    )
    df.loc[is_lf_diesel, "Balance"] = "Diesel"

    is_lf_co2 = (
        is_lf_sector &
        (
            edge_lower.str.contains("global_gasoline_use_co2_edge", na=False) |
            edge_lower.str.contains("global_gasoline_1a_use_co2_edge", na=False) |
            edge_lower.str.contains("global_gasoline_1b_use_co2_edge", na=False) |

            edge_lower.str.contains("global_jetfuel_use_co2_edge", na=False) |
            edge_lower.str.contains("global_jetfuel_1_use_co2_edge", na=False) |
            edge_lower.str.contains("global_diesel_use_co2_edge", na=False) |
            edge_lower.str.contains("global_diesel_1a_use_co2_edge", na=False) |
            edge_lower.str.contains("global_diesel_1b_use_co2_edge", na=False)
        )
    )
    df.loc[is_lf_co2, "Balance"] = "CO2"

    # -----------------------------------------------------------------
    # NG sector
    # -----------------------------------------------------------------

    is_ng_sector = sector_lower == "ng"

    is_ng_sector_co2 = (
        is_ng_sector &
        edge_lower.str.contains("natgas_end_use_co2_edge", na=False) |
        edge_lower.str.contains("ng_end_use_co2_edge", na=False)
    )
    df.loc[is_ng_sector_co2, "Balance"] = "CO2"

    is_ng_sector_ng = (
        is_ng_sector &
        (
            edge_lower.str.contains("natgas_end_use_fuel_edge", na=False) |
            edge_lower.str.contains("ng_end_use_fuel_edge", na=False) |
            edge_lower.str.contains("ng_fossil_upstream_fuel_edge", na=False)
        )
    )
    df.loc[is_ng_sector_ng, "Balance"] = "NG"

    # -----------------------------------------------------------------
    # Transmission sector
    # -----------------------------------------------------------------

    is_transmission = sector_lower == "transmission"

    is_transmission_power = (
        is_transmission &
        (
            edge_lower.str.contains("elec_edge", na=False) |
            edge_lower.str.contains("transmission_edge", na=False)
        )
    )
    df.loc[is_transmission_power, "Balance"] = "Power"

    # -----------------------------------------------------------------
    # Ethanol Upgrading sector
    # -----------------------------------------------------------------
    # Assign Balance purely by edge suffix (not by asset-name substring)
    # so every Ethanol_to_X variant — including combo plants like
    # Ethanol_to_Gasoline_Diesel — is covered without enumerating each
    # asset name individually.

    is_ethanol_upgrading = sector_lower == "ethanol upgrading"

    is_eth_upg_h2 = (
        is_ethanol_upgrading &
        edge_lower.str.contains("h2_consumption_edge", na=False)
    )
    df.loc[is_eth_upg_h2, "Balance"] = "H2"

    # Ethanol consumed by upgrading plants (shows as negative in Ethanol balance)
    is_eth_upg_ethanol = (
        is_ethanol_upgrading &
        edge_lower.str.contains("ethanol_consumption_edge", na=False)
    )
    df.loc[is_eth_upg_ethanol, "Balance"] = "Ethanol"

    is_eth_upg_elec = (
        is_ethanol_upgrading &
        (
            edge_lower.str.contains("elec_consumption_edge", na=False) |
            edge_lower.str.contains("elec_production_edge", na=False)
        )
    )
    df.loc[is_eth_upg_elec, "Balance"] = "Power"

    is_eth_upg_co2 = (
        is_ethanol_upgrading &
        edge_lower.str.contains("co2_emission_edge", na=False)
    )
    df.loc[is_eth_upg_co2, "Balance"] = "CO2"

    is_eth_upg_gasoline = (
        is_ethanol_upgrading &
        edge_lower.str.contains("gasoline_production_edge", na=False)
    )
    df.loc[is_eth_upg_gasoline, "Balance"] = "Gasoline"

    is_eth_upg_diesel = (
        is_ethanol_upgrading &
        edge_lower.str.contains("diesel_production_edge", na=False)
    )
    df.loc[is_eth_upg_diesel, "Balance"] = "Diesel"

    is_eth_upg_jetfuel = (
        is_ethanol_upgrading &
        edge_lower.str.contains("jetfuel_production_edge", na=False)
    )
    df.loc[is_eth_upg_jetfuel, "Balance"] = "Jetfuel"

    # -----------------------------------------------------------------
    # Ethylene sector
    # -----------------------------------------------------------------
    
    is_ethylene = sector_lower == "ethylene"

    is_ethylene_power = (
        is_ethylene &
        edge_lower.str.contains("elec_consumption_edge", na=False)
    )
    df.loc[is_ethylene_power, "Balance"] = "Power"

    is_ethylene_ng = (
        is_ethylene &
        edge_lower.str.contains("natgas_consumption_edge", na=False)
    )
    df.loc[is_ethylene_ng, "Balance"] = "NG"

    is_ethylene_ng = (
        is_ethylene &
        edge_lower.str.contains("natgas_production_edge", na=False)
    )
    df.loc[is_ethylene_ng, "Balance"] = "NG"

    is_ethylene_h2 = (
        is_ethylene &
        edge_lower.str.contains("h2_consumption_edge", na=False)
    )
    df.loc[is_ethylene_h2, "Balance"] = "H2"

    is_ethylene_h2 = (
        is_ethylene &
        edge_lower.str.contains("h2_production_edge", na=False)
    )
    df.loc[is_ethylene_h2, "Balance"] = "H2"

    is_ethylene_co2 = (
        is_ethylene &
        edge_lower.str.contains("co2_emission_edge|co2_process_emission_edge|co2_fuel_emission_edge", na=False)
    )
    df.loc[is_ethylene_co2, "Balance"] = "CO2"

    is_ethylene_gasoline = (
        is_ethylene &
        edge_lower.str.contains("gasoline_production_edge", na=False)
    )
    df.loc[is_ethylene_gasoline, "Balance"] = "Gasoline"

    is_ethylene_captured_co2 = (
        is_ethylene &
        edge_lower.str.contains("co2_captured_edge", na=False)
    )
    df.loc[is_ethylene_captured_co2, "Balance"] = "Captured_CO2"

    is_ethylene_ethylene = (
        is_ethylene &
        edge_lower.str.contains("ethylene_production_edge", na=False)
    )
    df.loc[is_ethylene_ethylene, "Balance"] = "Ethylene"

    is_ethylene_ethanol_consumption = (
        is_ethylene &
        edge_lower.str.contains("ethanol_consumption_edge", na=False)
        )
    df.loc[is_ethylene_ethanol_consumption, "Balance"] = "Ethanol"

    is_ethylene_sector_ethylene = (
        is_ethylene &
        (
            edge_lower.str.contains("global_ethylene_use_fuel_demand_edge", na=False) # positive value
        )
    )
    df.loc[is_ethylene_sector_ethylene, "Balance"] = "Ethylene"

    is_ethylene_sector_co2 = (
        is_ethylene &
        (
            edge_lower.str.contains("global_ethylene_use_co2_edge", na=False)
        )
    )
    df.loc[is_ethylene_sector_co2, "Balance"] = "CO2"

# -----------------------------------------------------------------
# Ethanol sector
# -----------------------------------------------------------------

    is_ethanol = sector_lower == "ethanol"

    is_lf_ethanol_consumption = (
            is_ethanol &
            edge_lower.str.contains("ethanol_consumption_edge", na=False)
        )
    df.loc[is_lf_ethanol_consumption, "Balance"] = "Ethanol"

    is_ethanol_ethanol_production = (
        is_ethanol &
        edge_lower.str.contains("ethanol_production_edge", na=False)
    )
    df.loc[is_ethanol_ethanol_production, "Balance"] = "Ethanol"

    is_ethanol_biomass = (
        is_ethanol &
        edge_lower.str.contains("biomass_consumption_edge", na=False)
    )
    df.loc[is_ethanol_biomass, "Balance"] = "Biomass"

    is_ethanol_power_consumption = (
        is_ethanol &
        edge_lower.str.contains("elec_consumption_edge", na=False)
    )
    df.loc[is_ethanol_power_consumption, "Balance"] = "Power"

    is_ethanol_power_production = (
        is_ethanol &
        edge_lower.str.contains("elec_production_edge", na=False)
    )
    df.loc[is_ethanol_power_production, "Balance"] = "Power"

    # NG: consumption AND production (was duplicated before — now distinct names)
    is_ethanol_ng_consumption = (
        is_ethanol &
        edge_lower.str.contains("natgas_consumption_edge", na=False)
    )
    df.loc[is_ethanol_ng_consumption, "Balance"] = "NG"

    # H2: consumption AND production (same fix)
    is_ethanol_h2_consumption = (
        is_ethanol &
        edge_lower.str.contains("h2_consumption_edge", na=False)
    )
    df.loc[is_ethanol_h2_consumption, "Balance"] = "H2"

    is_ethanol_co2 = (
        is_ethanol &
        (
            edge_lower.str.contains("co2_emission_edge", na=False) |
            edge_lower.str.contains("co2_content_edge", na=False) |
            edge_lower.str.contains("co2_edgedgee", na=False)
        )&
        (~edge_lower.str.contains("captured", na=False))
    )
    df.loc[is_ethanol_co2, "Balance"] = "CO2"

    is_ethanol_captured_co2 = (
        is_ethanol &
        edge_lower.str.contains("co2_captured_edge", na=False)
    )
    df.loc[is_ethanol_captured_co2, "Balance"] = "Captured_CO2"

    is_ethanol_gasoline = (
        is_ethanol &
        edge_lower.str.contains("gasoline_production_edge", na=False)
    )
    df.loc[is_ethanol_gasoline, "Balance"] = "Gasoline"

    is_ethanol_diesel = (
        is_ethanol &
        edge_lower.str.contains("diesel_production_edge", na=False)
    )
    df.loc[is_ethanol_diesel, "Balance"] = "Diesel"

    is_ethanol_jetfuel = (
        is_ethanol &
        edge_lower.str.contains("jetfuel_production_edge", na=False)
    )
    df.loc[is_ethanol_jetfuel, "Balance"] = "JetFuel"

    is_ethanol_h2 = (
        is_ethanol &
        edge_lower.str.contains("h2_consumption_edge", na=False)
    )
    df.loc[is_ethanol_h2, "Balance"] = "H2"

    #is_ethanol_gasoline_blending = (
    #    is_ethanol &
    #    edge_lower.str.contains("gasoline_blending_ethanol_edge", na=False)
    #)
    #df.loc[is_ethanol_gasoline_blending, "Balance"] = "Ethanol"

    return df


def export_balance_specific_files(df, output_dir):
    """
    Save one CSV file per balance type.

    Gasoline, Diesel, and Jetfuel are grouped into one Liquid_Fuels file.
    Demand rows are included because they already have Balance = Power or H2.
    Old balance-specific CSVs are removed first to avoid stale outputs.
    """
    balance_output_dir = os.path.join(output_dir, "balance_specific_flows")
    os.makedirs(balance_output_dir, exist_ok=True)

    # -----------------------------------------------------------------
    # Remove old balance-specific files first
    # -----------------------------------------------------------------

    for filename in os.listdir(balance_output_dir):
        if filename.startswith("annual_flows_balance_") and filename.endswith(".csv"):
            old_path = os.path.join(balance_output_dir, filename)
            os.remove(old_path)

    # -----------------------------------------------------------------
    # Create temporary balance grouping
    # -----------------------------------------------------------------

    liquid_fuel_balances = ["Gasoline", "Diesel", "Jetfuel"]

    export_df = df.copy()
    export_df["Balance_File_Group"] = export_df["Balance"]

    export_df.loc[
        export_df["Balance"].isin(liquid_fuel_balances),
        "Balance_File_Group",
    ] = "Liquid_Fuels"

    balance_groups = sorted(
        export_df.loc[
            export_df["Balance_File_Group"] != "NA",
            "Balance_File_Group",
        ].dropna().unique()
    )

    # -----------------------------------------------------------------
    # Export one file per balance group
    # -----------------------------------------------------------------

    for balance_name in balance_groups:
        balance_df = export_df[
            export_df["Balance_File_Group"] == balance_name
        ].copy()

        balance_df = balance_df.drop(columns=["Balance_File_Group"])

        # Put demand rows at the bottom so they are easy to inspect.
        balance_df["Demand_Row_Order"] = (
            balance_df["Sector"].astype(str).str.lower() == "demand"
        ).astype(int)

        balance_df = (
            balance_df
            .sort_values(
                ["Demand_Row_Order", "Sector", "Category", "Annual_Flow"],
                ascending=[True, True, True, False],
            )
            .drop(columns=["Demand_Row_Order"])
            .reset_index(drop=True)
        )

        balance_output_path = os.path.join(
            balance_output_dir,
            f"annual_flows_balance_{safe_filename(balance_name)}.csv",
        )

        balance_df.to_csv(balance_output_path, index=False)

        demand_count = (
            balance_df["Sector"].astype(str).str.lower() == "demand"
        ).sum()

        print(
            f"  Saved {balance_name} balance file "
            f"({len(balance_df)} rows, {demand_count} demand rows): "
            f"{balance_output_path}"
        )


def process_macro_scenario(scenario):
    scenario_dir = os.path.join(macro_base_dir, scenario)
    flows_path = os.path.join(scenario_dir, "flows.csv")
    time_weights_path = os.path.join(scenario_dir, "time_weights.csv")
    demand_path = get_demand_path_for_scenario(scenario)

    output_dir = os.path.join(scenario_dir, "annual_flow_results")
    os.makedirs(output_dir, exist_ok=True)

    scenario_label = scenario_labels.get(scenario, scenario)

    print("\n" + "-" * 90)
    print(f"Processing MACRO scenario: {scenario}")
    print(f"Scenario folder: {scenario_dir}")
    print(f"Demand file:     {demand_path}")
    print(f"Output folder:   {output_dir}")

    # -----------------------------------------------------------------
    # 1. Process flows in batches
    # -----------------------------------------------------------------

    annual_sums = compute_annual_flows_in_batches(
        flows_path=flows_path,
        time_weights_path=time_weights_path,
        chunk_size=chunk_size,
    )

    df = build_nonzero_annual_flow_table(
        annual_sums=annual_sums,
        scenario=scenario,
        scenario_label=scenario_label,
    )

    df = add_balance_labels(df)

    # -----------------------------------------------------------------
    # 2. Add annual demand rows directly into the universal table
    # -----------------------------------------------------------------

    demand_rows = compute_annual_demand_rows(
        demand_path=demand_path,
        time_weights_path=time_weights_path,
        scenario=scenario,
        scenario_label=scenario_label,
    )

    if len(demand_rows) > 0:
        df = pd.concat(
            [df, demand_rows],
            ignore_index=True,
        )

    df = (
        df
        .sort_values(
            ["Balance", "Sector", "Category", "Annual_Flow"],
            ascending=[True, True, True, False],
        )
        .reset_index(drop=True)
    )

    # -----------------------------------------------------------------
    # 3. Save universal file
    # -----------------------------------------------------------------

    universal_output_path = os.path.join(
        output_dir,
        "all_nonzero_annual_flows_with_categories.csv",
    )

    df.to_csv(universal_output_path, index=False)

    print(
        "  Saved universal annual-flow file with categories, balances, "
        f"and demand rows: {universal_output_path}"
    )

    # -----------------------------------------------------------------
    # 4. Diagnostics before balance-specific export
    # -----------------------------------------------------------------

    print("\n  Demand rows in universal df before balance-specific export:")
    demand_in_df = df[df["Sector"].astype(str).str.lower() == "demand"]

    if len(demand_in_df) > 0:
        print(
            demand_in_df[
                ["Edge", "Annual_Flow", "Sector", "Category", "Balance"]
            ].to_string(index=False)
        )
    else:
        print("  No demand rows found in universal df.")

    # -----------------------------------------------------------------
    # 5. Save balance-specific files
    # -----------------------------------------------------------------

    export_balance_specific_files(
        df=df,
        output_dir=output_dir,
    )

    # -----------------------------------------------------------------
    # 6. Diagnostics
    # -----------------------------------------------------------------

    print("\n  Sector counts:")
    print(df["Sector"].value_counts(dropna=False))

    print("\n  Balance counts:")
    print(df["Balance"].value_counts(dropna=False))

    if len(demand_rows) > 0:
        print("\n  Annual electricity demand rows:")
        print(
            demand_rows[demand_rows["Balance"] == "Power"][
                ["Edge", "Annual_Flow"]
            ].to_string(index=False)
        )

        print("\n  Annual hydrogen demand rows:")
        print(
            demand_rows[demand_rows["Balance"] == "H2"][
                ["Edge", "Annual_Flow"]
            ].to_string(index=False)
        )

        print("\n  Annual ethylene demand rows:")
        print(
            demand_rows[demand_rows["Balance"] == "Ethylene"][
                ["Edge", "Annual_Flow"]
            ].to_string(index=False)
        )

        print("\n  Annual ethanol demand rows:")
        print(
            demand_rows[demand_rows["Balance"] == "Ethanol"][
                ["Edge", "Annual_Flow"]
            ].to_string(index=False)
        )

        print("\n  Annual liquid fuels demand rows:")
        lf_demand = demand_rows[
            demand_rows["Balance"].isin(["Gasoline", "Diesel", "Jetfuel"])
        ]
        print(
            lf_demand[["Edge", "Annual_Flow", "Balance"]].to_string(index=False)
            if len(lf_demand) > 0 else "  (none)"
        )

    unmatched = df[df["Sector"] == "NA"].copy()

    if len(unmatched) > 0:
        print("\n  First 50 unmatched annual flows:")
        print(unmatched[["Edge", "Annual_Flow"]].head(50).to_string(index=False))

    return df


# ---------------------------------------------------------------------
# Non-served demand helper
# ---------------------------------------------------------------------

def load_annual_nsd(scen_path, col_prefixes):
    """
    Return the TDR-weighted annual non-served demand (MWh) for a scenario,
    summed across all NSD columns whose names start with any entry in col_prefixes.

    scen_path    : results path relative to macro_base_dir
    col_prefixes : str or list of str — column name prefix(es) to match

    Returns 0.0 if the file is absent or has no matching columns.
    """
    if isinstance(col_prefixes, str):
        col_prefixes = [col_prefixes]

    nsd_path = os.path.join(macro_base_dir, scen_path, "non_served_demand.csv")
    tw_path  = os.path.join(macro_base_dir, scen_path, "time_weights.csv")

    if not os.path.exists(nsd_path) or not os.path.exists(tw_path):
        return 0.0

    nsd = pd.read_csv(nsd_path)
    tw  = pd.read_csv(tw_path)
    nsd.columns = nsd.columns.str.strip()
    tw.columns  = tw.columns.str.strip()

    commodity_cols = [
        c for c in nsd.columns
        if any(c.lower().startswith(p.lower()) for p in col_prefixes)
    ]
    if not commodity_cols:
        return 0.0

    weight_map = dict(zip(
        pd.to_numeric(tw["time"],   errors="coerce"),
        pd.to_numeric(tw["weight"], errors="coerce"),
    ))
    weights = pd.to_numeric(nsd["time"], errors="coerce").map(weight_map).fillna(0.0)

    total = 0.0
    for col in commodity_cols:
        vals = pd.to_numeric(nsd[col], errors="coerce").fillna(0.0)
        total += (vals * weights).sum()

    return float(total)


# ---------------------------------------------------------------------
# Main loop: process all 4 MACRO scenarios
# ---------------------------------------------------------------------

all_scenario_tables = []
scenarios_without_ethanol_end_use = []

for scenario in scenario_folders:
    scenario_df = process_macro_scenario(scenario)
    all_scenario_tables.append(scenario_df)

    scenario_label = scenario_labels.get(scenario, scenario)
    input_path = macro_input_paths.get(scenario_label, "")
    ethanol_json_path = os.path.join(macro_base_dir, input_path, "assets", "ethanol_end_use.json")
    if not os.path.exists(ethanol_json_path):
        scenarios_without_ethanol_end_use.append(scenario_label)

print("\n" + "=" * 90)
print("Finished processing all MACRO scenarios.")

combined_df = pd.concat(all_scenario_tables, ignore_index=True)

print("\nCombined balance counts across all scenarios:")
print(combined_df["Balance"].value_counts(dropna=False))

print("\nCombined sector counts across all scenarios:")
print(combined_df["Sector"].value_counts(dropna=False))

if scenarios_without_ethanol_end_use:
    print("\n" + "=" * 90)
    print("Exception: the following scenarios do not have ethanol end use (ethanol_end_use.json not found):")
    for s in scenarios_without_ethanol_end_use:
        print(f"  Scenario {s}")