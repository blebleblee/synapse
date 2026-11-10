"""
Prerequisite Learning Graph (DAG) Engine
Models, resolves, and visualizes cross-domain learning dependencies across 4-level study units.
"""

from typing import Dict, List, Any, Optional
from .topic_manager import get_topic_tree

# Comprehensive Cross-Disciplinary Prerequisite Dependencies
PREREQUISITES_DAG = [
    # AI, Machine Learning & MLOps Pipeline
    ("computing/data/data_analysis", "computing/ai/foundations_of_ml"),
    ("formal_sciences/applied_math/probability", "computing/ai/foundations_of_ml"),
    ("formal_sciences/pure_math/linear_algebra", "computing/ai/foundations_of_ml"),
    ("formal_sciences/pure_math/calculus", "computing/ai/foundations_of_ml"),
    ("computing/ai/foundations_of_ml", "computing/ai/deep_learning"),
    ("computing/ai/deep_learning", "computing/ai/large_language_models"),
    ("computing/ai/large_language_models", "computing/ai/generative_ai"),
    ("computing/ai/large_language_models", "computing/ai/ai_agents"),
    ("computing/ai/large_language_models", "computing/ai/rag_systems"),
    ("computing/ai/large_language_models", "computing/ai/ai_safety_and_alignment"),
    ("computing/ai/large_language_models", "computing/ai/mlops_and_serving"),
    ("computing/data/data_analysis", "computing/data/data_visualisation"),
    ("computing/infrastructure/monitoring_prometheus_grafana", "computing/infrastructure/kubernetes"),

    # Systems, Kernels, eBPF & Rust
    ("computing/software/rust_systems", "computing/infrastructure/linux_device_drivers"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/linux_device_drivers"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/ebpf"),
    ("computing/infrastructure/ebpf", "computing/infrastructure/kubernetes"),
    ("computing/infrastructure/kubernetes", "computing/infrastructure/harvester"),
    ("computing/software/web_development", "computing/software/app_development"),
    ("computing/software/web_development", "computing/security/cybersecurity_operations"),
    ("computing/software/web_development", "computing/software/quality_assurance"),

    # Low-Level Computing, Hardware & Reverse Engineering
    ("engineering/hardware/computer_architecture", "engineering/hardware/assembly_programming"),
    ("engineering/hardware/assembly_programming", "computing/security/reverse_engineering"),
    ("computing/security/reverse_engineering", "computing/security/software_exploitation"),
    ("computing/security/software_exploitation", "computing/security/exploit_defense"),
    ("computing/security/reverse_engineering", "computing/security/hardware_hacking"),
    ("crafts/tactical/lock_picking", "computing/security/hardware_hacking"),

    # Security, Radio (SDR) & Automotive Cyber
    ("computing/infrastructure/networking", "computing/security/web_security"),
    ("engineering/circuits/circuit_theory", "computing/security/hardware_hacking"),
    ("engineering/hardware/software_defined_radio", "computing/security/hardware_hacking"),
    ("motorsports/driving/vehicle_diagnostics", "computing/security/automotive_cybersecurity"),
    ("computing/security/automotive_cybersecurity", "computing/security/exploit_defense"),

    # Mathematics, Game Theory & Quantitative Systems
    ("formal_sciences/pure_math/abstract_algebra", "formal_sciences/applied_math/cryptography"),
    ("formal_sciences/pure_math/algebra", "formal_sciences/pure_math/linear_algebra"),
    ("formal_sciences/pure_math/calculus", "formal_sciences/pure_math/differential_equations"),
    ("formal_sciences/pure_math/linear_algebra", "formal_sciences/applied_math/optimization"),
    ("formal_sciences/pure_math/calculus", "formal_sciences/applied_math/optimization"),
    ("formal_sciences/applied_math/probability", "formal_sciences/applied_math/statistics"),
    ("formal_sciences/applied_math/optimization", "business/trading/quant"),
    ("formal_sciences/applied_math/statistics", "business/trading/quant"),
    ("formal_sciences/applied_math/game_theory", "economics/microeconomics/microeconomic_foundations"),
    ("formal_sciences/applied_math/game_theory", "humanities/games_and_puzzles/card_games"),
    ("humanities/games_and_puzzles/card_games", "humanities/games_and_puzzles/texas_holdem_poker"),
    ("humanities/games_and_puzzles/rubiks_cube", "formal_sciences/pure_math/abstract_algebra"),

    # Quantum Physics, Cosmology & Frontiers
    ("natural_sciences/physics/quantum_mechanics", "natural_sciences/physics/quantum_foundations_and_paradoxes"),
    ("natural_sciences/physics/quantum_foundations_and_paradoxes", "computing/software/technological_frontiers"),
    ("natural_sciences/physics/thermodynamics", "natural_sciences/physics/cosmology_and_thermodynamics"),
    ("natural_sciences/physics/energy_and_frontiers", "natural_sciences/physics/cosmology_and_thermodynamics"),
    ("natural_sciences/space_and_flight/astronomy", "natural_sciences/space_and_flight/cosmic_frontiers_and_astrobiology"),
    ("natural_sciences/physics/classical_mechanics", "natural_sciences/space_and_flight/astronomy"),

    # Extreme Biology, Neurobiology & Health
    ("natural_sciences/biology/molecular_biology", "natural_sciences/biology/extreme_biology_and_genetics"),
    ("natural_sciences/biology/neuroscience", "health_sciences/physiology/neurobiology_and_altered_states"),
    ("health_sciences/physiology/neurobiology_and_altered_states", "computing/software/technological_frontiers"),
    ("health_sciences/physiology/exercise_physiology", "health_sciences/exercise/working_out"),
    ("health_sciences/exercise/working_out", "health_sciences/exercise/yoga"),
    ("health_sciences/physiology/nutrition_and_metabolism", "health_sciences/culinary/culinary_fundamentals"),
    ("health_sciences/culinary/culinary_fundamentals", "health_sciences/culinary/baking_and_fermentation"),
    ("health_sciences/lifestyle/hiking_and_outdoors", "health_sciences/lifestyle/first_aid"),

    # Physics, Aerodynamics, Motorsports & Aviation
    ("natural_sciences/physics/classical_mechanics", "motorsports/driving/aerodynamics"),
    ("natural_sciences/physics/aerodynamics", "natural_sciences/space_and_flight/flying_and_aviation"),
    ("motorsports/driving/aerodynamics", "motorsports/driving/performance_driving"),
    ("natural_sciences/physics/classical_mechanics", "motorsports/driving/vehicle_dynamics"),
    ("motorsports/driving/vehicle_dynamics", "motorsports/driving/performance_driving"),
    ("natural_sciences/space_and_flight/flying_and_aviation", "motorsports/driving/performance_driving"),

    # Maker, Electronics Repair & CAD
    ("crafts/maker/electronic_repair", "engineering/circuits/circuit_theory"),
    ("engineering/circuits/circuit_theory", "crafts/maker/drones_and_fpv"),
    ("crafts/maker/drones_and_fpv", "crafts/maker/rc_cars"),
    ("crafts/maker/cad_3d_modeling", "crafts/3d_printing/cad_modeling"),
    ("crafts/metalworking/metal_fabrication", "crafts/metalworking/welding"),
    ("crafts/metalworking/welding", "crafts/metalworking/cnc_machining"),

    # Creative Software, Visual Media & DAWs
    ("arts/visual_media/graphic_design", "arts/creative_software/adobe_creative_cloud"),
    ("arts/visual_media/photography", "arts/visual_media/video_production"),
    ("arts/visual_media/video_production", "arts/visual_media/content_creation"),
    ("arts/music_performance/piano", "arts/composition/music_theory"),
    ("arts/composition/music_theory", "arts/composition/counterpoint"),
    ("arts/composition/counterpoint", "arts/composition/orchestration"),
    ("arts/composition/orchestration", "arts/composition/orchestral_scoring"),
    ("arts/music_performance/piano", "arts/music_production/synthesizers"),
    ("arts/music_production/synthesizers", "arts/music_production/modular_synthesis"),
    ("formal_sciences/pure_math/calculus", "arts/music_production/audio_dsp"),
    ("arts/music_production/audio_dsp", "arts/music_production/audio_plugins"),
    ("arts/music_production/acoustics", "arts/music_production/audio_engineering"),
    ("arts/creative_software/ableton_live", "arts/music_production/synthesizers"),
    ("arts/creative_software/logic_pro", "arts/music_production/mixing"),
    ("arts/creative_software/cubase", "arts/composition/orchestral_scoring"),

    # Business, Productivity & Management
    ("business/management/project_management", "business/management/risk_management"),
    ("business/management/product_user_experience", "computing/software/web_development"),
    ("business/productivity/excel_mastery", "computing/data/data_analysis"),
    ("business/productivity/excel_mastery", "business/corporate_finance/valuation"),
    ("business/productivity/powerpoint_presentation", "humanities/cognitive_skills/public_speaking"),

    # Cognitive Meta-Skills & Mind Sports
    ("humanities/cognitive_skills/analytical_thinking", "humanities/cognitive_skills/problem_solving"),
    ("humanities/cognitive_skills/problem_solving", "humanities/games_and_puzzles/chess"),
    ("humanities/cognitive_skills/speed_reading", "humanities/cognitive_skills/active_listening"),
    ("humanities/cognitive_skills/public_speaking", "humanities/cognitive_skills/leadership_and_agility"),
    ("humanities/philosophy/epistemology", "humanities/cognitive_skills/psychological_phenomena_and_biases"),

    # Languages & Linguistics
    ("languages/linguistics/general_linguistics", "languages/germanic/english"),
    ("languages/linguistics/general_linguistics", "languages/germanic/german"),
    ("languages/linguistics/general_linguistics", "languages/slavic/czech"),
    ("languages/linguistics/general_linguistics", "languages/slavic/russian"),
    ("languages/linguistics/general_linguistics", "languages/romance/spanish")
]

def find_best_node_match(query: str, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    clean = query.strip("/").lower()
    # 1. Exact match
    for n in nodes:
        if n["id"].lower() == clean:
            return n
    # 2. Starts with course query (e.g. course prefix -> unit 01)
    for n in nodes:
        if n["id"].lower().startswith(clean + "/"):
            return n
    # 3. Substring match
    for n in nodes:
        if clean in n["id"].lower():
            return n
    return None

def get_prerequisite_graph() -> Dict[str, Any]:
    tree = get_topic_tree()

    nodes = []
    DOMAIN_COLORS = {
        "computing": "#4f8fff",
        "engineering": "#10b981",
        "formal_sciences": "#bc8cff",
        "natural_sciences": "#2dd4bf",
        "health_sciences": "#f43f5e",
        "business": "#f59e0b",
        "economics": "#fb923c",
        "arts": "#ec4899",
        "languages": "#38bdf8",
        "humanities": "#fbbf24",
        "crafts": "#60a5fa",
        "motorsports": "#f97316"
    }

    for domain, ddata in tree.items():
        color = DOMAIN_COLORS.get(domain, "#9da2af")
        for disc, disc_data in (ddata.get("disciplines") or {}).items():
            for course, c_data in disc_data.get("courses", {}).items():
                for unit, u_data in c_data.get("units", {}).items():
                    rel = u_data["rel_path"]
                    status = u_data["status"]
                    nodes.append({
                        "id": rel,
                        "label": f"{course.replace('_', ' ').title()}: {u_data['display_name']}",
                        "domain": domain,
                        "category": f"{disc}/{course}",
                        "subtopic": unit,
                        "complete": status["complete"],
                        "color": color
                    })

    # Resolve DAG dependencies to concrete units
    edges = []
    seen_edges = set()

    for src_query, dst_query in PREREQUISITES_DAG:
        src_node = find_best_node_match(src_query, nodes)
        dst_node = find_best_node_match(dst_query, nodes)

        if src_node and dst_node and src_node["id"] != dst_node["id"]:
            edge_key = f"{src_node['id']}->{dst_node['id']}"
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edges.append({
                    "source": src_node["id"],
                    "target": dst_node["id"]
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "edge_count": len(edges),
        "node_count": len(nodes)
    }
