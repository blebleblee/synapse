#!/usr/bin/env python3
"""
Topic Reorganization Script
Restructures topics into 6 primary domains, sets up GEMINI.md personas,
generates comprehensive SYLLABUS.md files, and removes legacy flat folders.
"""

import os
import shutil
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"

DOMAINS = {
    "business_and_economics": {
        "title": "Business and Economics",
        "persona_title": "AI Instructions for Business and Economics Topics",
        "persona_role": "Senior Economist & Quantitative Financial Analyst",
        "directives": [
            "**Analytical Rigor:** Break down economic models, corporate valuation, and market dynamics into first principles. Emphasize incentives, marginal trade-offs, and equilibrium.",
            "**Dual Perspective:** Seamlessly connect macroeconomic fiscal/monetary policy with microeconomic firm behavior and quantitative asset pricing.",
            "**Artifacts:** Generate structured financial models, balance sheet breakdowns, and LaTeX formula blocks for economic and financial relationships."
        ],
        "subtopics": {
            "macro_and_policy": [
                ("Agricultural Economics", "agricultural"),
                ("Development Economics", "development"),
                ("Econometrics", "econometrics"),
                ("Environmental Economics", "environmental"),
                ("Growth Theory", "growth"),
                ("Health Economics", "health"),
                ("Economic History", "history"),
                ("International Trade", "international_trade"),
                ("Macroeconomics", "macroeconomics"),
                ("Monetary Policy", "monetary"),
                ("Political Economy", "political_economy"),
                ("Public Economics", "public"),
                ("Urban Economics", "urban"),
                ("Welfare Economics", "welfare")
            ],
            "micro_and_behavioral": [
                ("Behavioral Economics", "behavioral_economics"),
                ("Behavioral Finance", "behavioral_finance"),
                ("Experimental Economics", "experimental"),
                ("Game Theory", "game_theory"),
                ("Industrial Organization", "industrial_organization"),
                ("Labor Economics", "labor"),
                ("Microeconomics", "microeconomics")
            ],
            "markets_and_trading": [
                ("Algorithmic Trading", "algorithmic_trading"),
                ("Cryptocurrency & Web3", "crypto"),
                ("Derivatives Pricing", "derivatives"),
                ("Equities Analysis", "equities"),
                ("Financial Economics", "financial_economics"),
                ("Fixed Income", "fixed_income"),
                ("Foreign Exchange (Forex)", "forex"),
                ("Hedge Funds & Strategies", "hedge_funds"),
                ("Options Trading", "options"),
                ("Quantitative Methods", "quant")
            ],
            "corporate_finance": [
                ("Financial Accounting", "accounting"),
                ("Corporate Finance Fundamentals", "corporate_finance"),
                ("Financial Modeling", "financial_modeling"),
                ("Investment Banking", "investment_banking"),
                ("Mergers and Acquisitions", "m_and_a"),
                ("Private Equity", "private_equity"),
                ("Risk Management", "risk_management"),
                ("Company Valuation", "valuation"),
                ("Venture Capital", "venture_capital")
            ],
            "personal_wealth": [
                ("Asset Management", "asset_management"),
                ("Mutual Funds & ETFs", "mutual_funds"),
                ("Personal Finance", "personal_finance"),
                ("Real Estate Investing", "real_estate"),
                ("Taxation Strategy", "taxation"),
                ("Wealth Management", "wealth_management")
            ],
            "economic_schools": [
                ("Austrian School", "austrian_school"),
                ("Keynesian Economics", "keynesian"),
                ("Neoclassical Synthesis", "neoclassical"),
                ("Socialist & Heterodox Economics", "socialist")
            ]
        }
    },
    "computing_and_engineering": {
        "title": "Computing and Engineering",
        "persona_title": "AI Instructions for Computing and Engineering Topics",
        "persona_role": "Principal Systems Architect and Senior Staff Engineer",
        "directives": [
            "**Architectural Depth:** Explain the underlying mechanisms (OS kernels, CPU caches, network packets, semiconductor physics) behind code and circuits. Prioritize the 'why' over superficial syntax.",
            "**Infrastructure as Code:** Always provide deployable, reproducible manifests (Kubernetes YAML, Dockerfiles, Terraform, KiCad netlists, Verilog) rather than ambiguous instructions.",
            "**Safety & Validation:** Provide explicit verification commands (CLI outputs, test suites, oscilloscope measurements) and highlight destructive risks.",
            "**Tools:** Assume standard Linux CLI utilities, Docker, and container tooling are accessible."
        ],
        "subtopics": {
            "hardware_and_circuits": [
                ("Active Components", "active_components"),
                ("Analog Circuit Design", "analog_design"),
                ("Battery Technologies", "battery_tech"),
                ("Circuit Theory", "circuit_theory"),
                ("Consumer Electronics", "consumer_electronics"),
                ("Digital Logic", "digital_logic"),
                ("FPGA & HDLs", "fpga"),
                ("Industrial Control Systems", "industrial_control"),
                ("Motor Control", "motor_control"),
                ("Optoelectronics", "optoelectronics"),
                ("Passive Components", "passive_components"),
                ("PCB Design", "pcb_design"),
                ("Power Electronics", "power_electronics"),
                ("Renewable Energy Systems", "renewable_energy"),
                ("RF & Microwave Engineering", "rf_microwave"),
                ("Schematic Capture", "schematics"),
                ("Semiconductor Physics", "semiconductors"),
                ("Sensors & Transducers", "sensors"),
                ("Signal Processing", "signal_processing"),
                ("Soldering & Fabrication", "soldering"),
                ("Test & Measurement", "test_measurement"),
                ("Hardware Troubleshooting", "troubleshooting")
            ],
            "software_engineering": [
                ("Software Architecture", "architecture"),
                ("Compiler Design", "compilers"),
                ("Computer Graphics & Shaders", "computer_graphics"),
                ("Game Development", "game_development"),
                ("Software Methodologies", "methodologies"),
                ("Mobile App Development", "mobile_development"),
                ("Open Source Stewardship", "open_source"),
                ("Performance Engineering", "performance_engineering"),
                ("Programming Paradigms", "programming"),
                ("Software Testing & QA", "software_testing"),
                ("UI/UX Engineering", "ui_ux"),
                ("Modern Web Development", "web_development")
            ],
            "infrastructure_and_ops": [
                ("Infrastructure Automation", "automation"),
                ("Cloud Native & HCI", "cloud_native_and_hci"),
                ("DevSecOps", "devsecops"),
                ("Distributed Systems", "distributed_systems"),
                ("Core Infrastructure", "infrastructure"),
                ("Kubernetes Ecosystem", "kubernetes"),
                ("Linux Kernel & Systems", "linux"),
                ("Computer Networking", "networking"),
                ("Observability & Telemetry", "observability"),
                ("Operating System Theory", "os_theory"),
                ("Site Reliability Engineering (SRE)", "sre")
            ],
            "data_and_ai": [
                ("Artificial Intelligence & LLMs", "ai"),
                ("Big Data Architecture", "big_data"),
                ("Data Engineering", "data"),
                ("Database Internals & Storage Engines", "database_internals"),
                ("MLOps & Model Lifecycle", "mlops")
            ],
            "security": [
                ("Applied Cryptography", "cryptography"),
                ("Ethical Hacking & Penetration Testing", "ethical_hacking"),
                ("Identity & Access Management (IAM)", "iam"),
                ("Reverse Engineering & Binaries", "reverse_engineering"),
                ("Application & Network Security", "security")
            ],
            "robotics_and_embedded": [
                ("Augmented & Virtual Reality", "ar_vr"),
                ("Blockchain & Distributed Ledgers", "blockchain"),
                ("Embedded Systems Design", "embedded_systems"),
                ("Internet of Things (IoT)", "iot"),
                ("Microcontrollers & Firmware", "microcontrollers"),
                ("Quantum Computing", "quantum_computing"),
                ("Robotics & Kinematics", "robotics")
            ]
        }
    },
    "formal_sciences": {
        "title": "Formal Sciences",
        "persona_title": "AI Instructions for Formal Sciences Topics",
        "persona_role": "Professor of Mathematics and Formal Logic",
        "directives": [
            "**Proof and Intuition:** Cultivate deep mathematical intuition alongside rigorous formal proofs. Explain why theorems hold before demonstrating formal derivation.",
            "**Step-by-Step Exposition:** Break down equations, algebraic manipulations, and logical deductions into clear, deliberate steps.",
            "**Artifacts:** Structure mathematical output using clean LaTeX blocks and standard mathematical notation."
        ],
        "subtopics": {
            "pure_math": [
                ("Abstract Algebra", "abstract_algebra"),
                ("Linear Algebra", "linear_algebra"),
                ("Elementary Algebra", "algebra"),
                ("Arithmetic Foundations", "arithmetic"),
                ("Calculus & Analysis", "calculus"),
                ("Category Theory", "category_theory"),
                ("Complex Analysis", "complex_analysis"),
                ("Differential Equations", "differential_equations"),
                ("Dynamical Systems & Chaos", "dynamical_systems"),
                ("Euclidean & Non-Euclidean Geometry", "geometry"),
                ("Number Theory", "number_theory"),
                ("Real Analysis", "real_analysis"),
                ("Topology", "topology"),
                ("Trigonometry", "trigonometry")
            ],
            "applied_math": [
                ("Mathematical Cryptography", "cryptography"),
                ("Game Theory", "game_theory"),
                ("Graph Theory", "graph_theory"),
                ("Numerical Analysis", "numerical_analysis"),
                ("Optimization Theory", "optimization"),
                ("Probability Theory", "probability"),
                ("Mathematical Statistics", "statistics")
            ],
            "logic_and_discrete": [
                ("Combinatorics", "combinatorics"),
                ("Discrete Mathematics", "discrete_math"),
                ("Mathematical Logic & Model Theory", "logic"),
                ("Axiomatic Set Theory", "set_theory")
            ]
        }
    },
    "natural_sciences": {
        "title": "Natural Sciences",
        "persona_title": "AI Instructions for Natural Sciences Topics",
        "persona_role": "Research Scientist and Natural Philosophy Scholar",
        "directives": [
            "**First Principles:** Ground natural phenomena in empirical observation, physical laws, and the scientific method.",
            "**Quantitative & Qualitative Models:** Pair mathematical formulas with intuitive conceptual diagrams and experimental setups.",
            "**Interdisciplinary Connections:** Highlight how atomic chemistry informs cellular biology, and how physical laws govern molecular interactions."
        ],
        "subtopics": {
            "physics": [
                ("Astrophysics & Cosmology", "astrophysics"),
                ("Classical Mechanics", "classical_mechanics"),
                ("Electromagnetism", "electromagnetism"),
                ("Optics & Wave Physics", "optics"),
                ("Quantum Mechanics", "quantum_mechanics"),
                ("Special & General Relativity", "relativity"),
                ("Thermodynamics & Statistical Mechanics", "thermodynamics")
            ],
            "chemistry": [
                ("Analytical Chemistry", "analytical_chemistry"),
                ("Biochemistry", "biochemistry"),
                ("Inorganic Chemistry", "inorganic_chemistry"),
                ("Organic Chemistry", "organic_chemistry"),
                ("Physical Chemistry", "physical_chemistry")
            ],
            "biology": [
                ("Cellular & Molecular Biology", "cellular_biology"),
                ("Ecology & Ecosystems", "ecology"),
                ("Evolutionary Biology", "evolutionary_biology"),
                ("Genetics & Genomics", "genetics"),
                ("Microbiology & Virology", "microbiology"),
                ("Neuroscience", "neuroscience")
            ]
        }
    },
    "arts_and_humanities": {
        "title": "Arts and Humanities",
        "persona_title": "AI Instructions for Arts and Humanities Topics",
        "persona_role": "Polymath Scholar, Master Musician, and Humanities Mentor",
        "directives": [
            "**Craft, Expression, & History:** Seamlessly connect technical execution (scales, brushwork, composition) with aesthetic theory and cultural history.",
            "**Disciplined Practice:** Break artistic skills down into focused, repeatable exercises with clear incremental milestones.",
            "**Critical Inquiry:** Examine philosophical traditions and historical narratives with nuanced context, cross-cultural perspective, and primary source analysis.",
            "**Artifacts:** Generate sheet music / ABC notation / LilyPond blocks for music, and structured analytical essays for philosophy and history."
        ],
        "subtopics": {
            "music": [
                ("Acoustics & Psychoacoustics", "acoustics"),
                ("Audio Engineering & Recording", "audio_engineering"),
                ("Bass Guitar", "bass_guitar"),
                ("Beatmaking & Sampling", "beatmaking"),
                ("Brass Instruments", "brass"),
                ("Choral Music", "choral"),
                ("Classical Guitar", "classical_guitar"),
                ("Musical Composition", "composition"),
                ("Conducting", "conducting"),
                ("Music Copyright & Royalties", "copyright"),
                ("Counterpoint", "counterpoint"),
                ("DJing & Performance", "djing"),
                ("Drums & Rhythm", "drums"),
                ("Ear Training & Solfege", "ear_training"),
                ("Electric Guitar", "electric_guitar"),
                ("Ethnomusicology", "ethnomusicology"),
                ("Film Scoring & Media Composition", "film_scoring"),
                ("Guitar Fundamentals", "guitar"),
                ("Music History", "history"),
                ("Improvisation", "improvisation"),
                ("Jazz Harmony & Theory", "jazz_theory"),
                ("Live Performance Setup", "live_performance"),
                ("Mastering Engineering", "mastering"),
                ("Advanced Mixing", "mixing_advanced"),
                ("Music Business & Marketing", "music_business"),
                ("Notation & Score Prep", "notation"),
                ("Orchestral Repertoire", "orchestral"),
                ("Orchestration Techniques", "orchestration"),
                ("Organ & Keyboards", "organ"),
                ("Percussion", "percussion"),
                ("Piano Performance", "piano"),
                ("Music Production (DAWs)", "production"),
                ("Songwriting", "songwriting"),
                ("Sound Design", "sound_design"),
                ("String Instruments", "strings"),
                ("Advanced Sound Synthesis", "synthesis_advanced"),
                ("Synthesizer Programming", "synthesizers"),
                ("Music Theory", "theory"),
                ("Vocal Technique", "vocals"),
                ("Woodwind Instruments", "woodwinds")
            ],
            "visual_arts": [
                ("Art History & Movements", "art_history"),
                ("Color Theory", "color_theory"),
                ("Digital Painting & Illustration", "digital_painting"),
                ("Drawing & Perspective", "drawing"),
                ("Photography & Composition", "photography"),
                ("Sculpture & 3D Form", "sculpture"),
                ("Typography & Graphic Design", "typography")
            ],
            "history": [
                ("Ancient Civilizations", "ancient_history"),
                ("Medieval World History", "medieval_history"),
                ("Early Modern Era", "early_modern_history"),
                ("Modern World History", "modern_history"),
                ("Global Intellectual History", "world_history")
            ],
            "philosophy": [
                ("Aesthetics & Art Philosophy", "aesthetics"),
                ("Epistemology & Theory of Knowledge", "epistemology"),
                ("Ethics & Moral Philosophy", "ethics"),
                ("Philosophical Logic", "logic"),
                ("Metaphysics & Ontology", "metaphysics"),
                ("Political Philosophy", "political_philosophy")
            ]
        }
    },
    "hobbies_and_crafts": {
        "title": "Hobbies and Crafts",
        "persona_title": "AI Instructions for Hobbies and Crafts Topics",
        "persona_role": "Master Builder, Woodworker, and Fabrication Craftsman",
        "directives": [
            "**Physical Mechanics & Structural Integrity:** Teach building techniques through balance, stress distribution, gear ratios, and material properties.",
            "**Craft Precision:** Emphasize tolerances, safety with tools, proper maintenance, and precision measuring.",
            "**Artifacts:** Generate detailed step-by-step assembly guides, cut-lists, parts manifests, and slicing parameter profiles."
        ],
        "subtopics": {
            "lego": [
                ("Lego Architecture", "architecture"),
                ("Bionicle & Constraction", "bionicle"),
                ("Custom Decals & Printing", "custom_decals"),
                ("Digital Brick Design (Studio)", "digital_design"),
                ("Display & Diarama Techniques", "display_techniques"),
                ("Gear Ratios & Mechanical Advantage", "gear_ratios"),
                ("Great Ball Contraption (GBC)", "great_ball_contraption"),
                ("History of the Lego System", "history"),
                ("Illegal Build Techniques", "illegal_builds"),
                ("Instruction Book Authoring", "instructions"),
                ("Lego Investing & Secondary Market", "investing"),
                ("Lighting Systems & LEDs", "lighting"),
                ("Kinematic Mechanisms", "mechanisms"),
                ("Microscale Building", "microscale"),
                ("Mindstorms & Spike Prime", "mindstorms"),
                ("Minifigure Scale Environments", "minifigure_scale"),
                ("MOC (My Own Creation) Design", "moc_building"),
                ("Motorized Systems (Power Functions/Powered Up)", "motorized"),
                ("Pneumatics", "pneumatics"),
                ("Brick Robotics", "robotics"),
                ("Official Set Design Philosophy", "set_design"),
                ("SNOT (Studs Not On Top) Techniques", "snot_techniques"),
                ("Sorting & Storage Systems", "sorting_storage"),
                ("Brickfilm Stop Motion Animation", "stop_motion"),
                ("System Brick Geometry", "system_bricks"),
                ("Technic Chassis & Linkages", "technic")
            ],
            "woodworking": [
                ("Finishing & Staining", "finishing"),
                ("Hand Tool Fundamentals", "hand_tools"),
                ("Joinery Techniques (Dovetails, Mortise & Tenon)", "joinery"),
                ("Lumber Selection & Milling", "lumber_selection"),
                ("Power Tool Safety & Techniques", "power_tools"),
                ("Wood Turning on Lathe", "turning")
            ],
            "3d_printing": [
                ("CAD Modeling for 3D Printing", "cad_modeling"),
                ("FDM Printer Tuning & Mechanics", "fdm_printers"),
                ("Materials & Filaments (PLA, PETG, ABS, TPU)", "materials_and_filaments"),
                ("Post-Processing & Finishing", "post_processing"),
                ("Resin (SLA/MSLA) Printing", "resin_printers"),
                ("Slicing Optimization (Supports, Infill, Walls)", "slicing_techniques")
            ]
        }
    }
}

LEGACY_TOPICS = ["economics", "electronics", "finance", "lego", "math", "music", "tech"]

def generate_domain(domain_key, config):
    domain_dir = TOPICS_DIR / domain_key
    domain_dir.mkdir(parents=True, exist_ok=True)
    (domain_dir / "artifacts").mkdir(exist_ok=True)
    (domain_dir / "sessions").mkdir(exist_ok=True)

    # 1. Write GEMINI.md
    gemini_lines = [
        f"# {config['persona_title']}\n",
        f"When operating within the `topics/{domain_key}/` directory, you must assume the persona of a **{config['persona_role']}**.\n",
        "## Core Directives"
    ]
    for idx, directive in enumerate(config["directives"], 1):
        gemini_lines.append(f"{idx}. {directive}")

    gemini_content = "\n".join(gemini_lines) + "\n"
    (domain_dir / "GEMINI.md").write_text(gemini_content, encoding="utf-8")

    # 2. Create subtopics and build SYLLABUS.md
    syllabus_lines = [
        f"# Syllabus: {config['title']}\n",
        "Here are all the available subtopics in this learning module organized by category:\n"
    ]

    for category_key, subtopics in config["subtopics"].items():
        cat_title = category_key.replace("_", " ").title()
        syllabus_lines.append(f"### {cat_title}\n")

        for display_name, folder_name in subtopics:
            subtopic_rel_path = f"{category_key}/{folder_name}"
            subtopic_full_path = domain_dir / subtopic_rel_path
            subtopic_full_path.mkdir(parents=True, exist_ok=True)

            syllabus_lines.append(f"- **{display_name}** (`{subtopic_rel_path}/`)")

        syllabus_lines.append("")

    syllabus_content = "\n".join(syllabus_lines).strip() + "\n"
    (domain_dir / "SYLLABUS.md").write_text(syllabus_content, encoding="utf-8")
    print(f"[✔] Configured domain: {domain_key}")

def main():
    print("Reorganizing topics into broad domains...")

    for domain_key, config in DOMAINS.items():
        generate_domain(domain_key, config)

    # Remove legacy topic folders if empty
    for legacy in LEGACY_TOPICS:
        legacy_dir = TOPICS_DIR / legacy
        if legacy_dir.exists():
            shutil.rmtree(legacy_dir)
            print(f"[✔] Removed legacy topic directory: {legacy}")

    print("\n[✔] Reorganization complete!")

if __name__ == "__main__":
    main()
