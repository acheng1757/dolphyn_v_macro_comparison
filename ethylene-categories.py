"Ethylene": {
        "categories": [
            ("Thermal Steam Cracker", [
                r"F-NGin(?!.*Ein)",       # all F- variants except F-Ein
                r"F-CC90-NGin",
                r"F-H2in",
                r"F-H2in-CH4out",
                r"F-CC90-NGin-H2out",
                r"F-NGin-H2out",

                r"TSC",
                r"TSC+CC90",
                r"TSC:H2",
                r"TSC+CC90:H2",
                r"TSC+H2in",
                r"TSC+H2in:CH4",
                r"CSC_Plant",
                r"CSC_CCS_Plant",
            ]),
            ("Electric Steam Cracker", [
                r"F-Ein",
                r"ESC",
                r"ESC_Plant",
            ]),
            ("Ethanol Dehydration", [
                r"B-NGin",
                r"B-H2in",
                
                r"Bio-eth+CC88:NG",
                r"Bio-eth+CC88:H2",
                r"Ethanol_Plant",
                r"Ethanol_CCS_Plant"
            ]),
            ("Synthetic Ethylene", [
                r"S-H2in",
                r"S-CC90-H2in",

                r"MS+MTO",
                r"MS+MTO+CC90",
            ]),
        ],
    },