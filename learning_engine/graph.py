"""
Prerequisite Learning Graph (DAG) Engine
Models, resolves, and visualizes comprehensive cross-domain learning dependencies
across all 700+ study units with intra-course sequencing, discipline pathways,
and cross-domain foundational bridges.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict
from .topic_manager import get_topic_tree

# Explicit Cross-Disciplinary & Inter-Course Bridges (source course/disc -> target course/disc)
CROSS_DOMAIN_BRIDGES = [
    # AI, Data Science & MLOps Pipeline
    ("formal_sciences/applied_math/probability", "computing/data/data_analysis"),
    ("formal_sciences/pure_math/linear_algebra", "computing/ai/foundations_of_ml"),
    ("formal_sciences/pure_math/calculus", "computing/ai/foundations_of_ml"),
    ("computing/data/data_analysis", "computing/ai/foundations_of_ml"),
    ("computing/ai/foundations_of_ml", "computing/ai/deep_learning"),
    ("computing/ai/deep_learning", "computing/ai/large_language_models"),
    ("computing/ai/large_language_models", "computing/ai/generative_ai"),
    ("computing/ai/large_language_models", "computing/ai/ai_agents"),
    ("computing/ai/large_language_models", "computing/ai/rag_systems"),
    ("computing/ai/large_language_models", "computing/ai/ai_safety_and_alignment"),
    ("computing/ai/large_language_models", "computing/ai/mlops_and_serving"),
    ("computing/data/data_analysis", "computing/data/data_visualisation"),
    ("computing/data/data_analysis", "business/productivity/excel_mastery"),
    ("computing/infrastructure/monitoring_prometheus_grafana", "computing/infrastructure/kubernetes"),

    # Systems, Low-Level Kernel, Drivers & Hardware
    ("engineering/hardware/computer_architecture", "engineering/hardware/assembly_programming"),
    ("engineering/hardware/assembly_programming", "computing/software/rust_systems"),
    ("computing/software/rust_systems", "computing/infrastructure/linux_device_drivers"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/linux_device_drivers"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/ebpf"),
    ("computing/infrastructure/ebpf", "computing/infrastructure/kubernetes"),
    ("computing/infrastructure/kubernetes", "computing/infrastructure/harvester"),
    ("engineering/circuits/circuit_theory", "crafts/maker/electronic_repair"),
    ("crafts/maker/electronic_repair", "computing/security/hardware_hacking"),
    ("engineering/hardware/software_defined_radio", "computing/security/hardware_hacking"),
    ("engineering/hardware/assembly_programming", "computing/security/reverse_engineering"),
    ("computing/security/reverse_engineering", "computing/security/software_exploitation"),
    ("computing/security/software_exploitation", "computing/security/exploit_defense"),
    ("crafts/tactical/lock_picking", "computing/security/hardware_hacking"),

    # Web, App, QA & Security Ops
    ("computing/infrastructure/networking", "computing/security/web_security"),
    ("computing/software/web_development", "computing/software/app_development"),
    ("computing/software/web_development", "computing/software/quality_assurance"),
    ("computing/software/web_development", "computing/security/cybersecurity_operations"),
    ("business/management/product_user_experience", "computing/software/web_development"),
    ("arts/visual_media/graphic_design", "business/management/product_user_experience"),

    # Automotive Cybersecurity, Vehicle Dynamics & Motorsports
    ("motorsports/driving/vehicle_diagnostics", "computing/security/automotive_cybersecurity"),
    ("computing/security/automotive_cybersecurity", "computing/security/exploit_defense"),
    ("natural_sciences/physics/classical_mechanics", "motorsports/driving/vehicle_dynamics"),
    ("natural_sciences/physics/classical_mechanics", "motorsports/driving/aerodynamics"),
    ("motorsports/driving/aerodynamics", "motorsports/driving/performance_driving"),
    ("motorsports/driving/vehicle_dynamics", "motorsports/driving/performance_driving"),
    ("natural_sciences/physics/aerodynamics", "natural_sciences/space_and_flight/flying_and_aviation"),
    ("natural_sciences/space_and_flight/flying_and_aviation", "motorsports/driving/performance_driving"),

    # Pure & Applied Mathematics, Logic & Game Theory
    ("formal_sciences/pure_math/algebra", "formal_sciences/pure_math/linear_algebra"),
    ("formal_sciences/pure_math/calculus", "formal_sciences/pure_math/differential_equations"),
    ("formal_sciences/pure_math/differential_equations", "natural_sciences/physics/classical_mechanics"),
    ("formal_sciences/pure_math/linear_algebra", "formal_sciences/applied_math/optimization"),
    ("formal_sciences/pure_math/calculus", "formal_sciences/applied_math/optimization"),
    ("formal_sciences/pure_math/abstract_algebra", "formal_sciences/applied_math/cryptography"),
    ("formal_sciences/pure_math/abstract_algebra", "humanities/games_and_puzzles/rubiks_cube"),
    ("formal_sciences/discrete_math/logic", "formal_sciences/discrete_math/foundational_paradoxes_and_problems"),
    ("formal_sciences/applied_math/probability", "formal_sciences/applied_math/statistics"),
    ("formal_sciences/applied_math/optimization", "business/trading/quant"),
    ("formal_sciences/applied_math/statistics", "business/trading/quant"),
    ("formal_sciences/applied_math/game_theory", "economics/microeconomics/microeconomic_foundations"),
    ("formal_sciences/applied_math/game_theory", "humanities/games_and_puzzles/card_games"),
    ("humanities/games_and_puzzles/card_games", "humanities/games_and_puzzles/texas_holdem_poker"),
    ("humanities/games_and_puzzles/chess", "humanities/cognitive_skills/problem_solving"),

    # Quantum Physics, Cosmology & Energy
    ("natural_sciences/physics/electromagnetism", "engineering/circuits/circuit_theory"),
    ("natural_sciences/physics/quantum_mechanics", "natural_sciences/physics/quantum_foundations_and_paradoxes"),
    ("natural_sciences/physics/quantum_foundations_and_paradoxes", "computing/software/technological_frontiers"),
    ("natural_sciences/physics/thermodynamics", "natural_sciences/physics/cosmology_and_thermodynamics"),
    ("natural_sciences/physics/energy_and_frontiers", "natural_sciences/physics/cosmology_and_thermodynamics"),
    ("natural_sciences/physics/classical_mechanics", "natural_sciences/space_and_flight/astronomy"),
    ("natural_sciences/space_and_flight/astronomy", "natural_sciences/space_and_flight/cosmic_frontiers_and_astrobiology"),

    # Biology, Genetics, Neurobiology & Health Sciences
    ("natural_sciences/chemistry/biochemistry", "natural_sciences/biology/molecular_biology"),
    ("natural_sciences/biology/molecular_biology", "natural_sciences/biology/extreme_biology_and_genetics"),
    ("natural_sciences/biology/genetics", "natural_sciences/biology/extreme_biology_and_genetics"),
    ("natural_sciences/biology/neuroscience", "health_sciences/physiology/neurobiology_and_altered_states"),
    ("health_sciences/physiology/neurobiology_and_altered_states", "computing/software/technological_frontiers"),
    ("health_sciences/physiology/exercise_physiology", "health_sciences/exercise/working_out"),
    ("health_sciences/exercise/working_out", "health_sciences/exercise/yoga"),
    ("health_sciences/physiology/nutrition_and_metabolism", "health_sciences/culinary/culinary_fundamentals"),
    ("health_sciences/culinary/culinary_fundamentals", "health_sciences/culinary/baking_and_fermentation"),
    ("health_sciences/lifestyle/hiking_and_outdoors", "health_sciences/lifestyle/first_aid"),

    # Maker, Drones & Fabrication
    ("engineering/circuits/circuit_theory", "crafts/maker/drones_and_fpv"),
    ("crafts/maker/drones_and_fpv", "crafts/maker/rc_cars"),
    ("crafts/maker/cad_3d_modeling", "crafts/3d_printing/cad_modeling"),
    ("crafts/metalworking/metal_fabrication", "crafts/metalworking/welding"),
    ("crafts/metalworking/welding", "crafts/metalworking/cnc_machining"),

    # Music, Synthesizers, Audio DSP & DAWs
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

    # Creative Visual Media & Design
    ("arts/visual_media/graphic_design", "arts/creative_software/adobe_creative_cloud"),
    ("arts/visual_media/photography", "arts/visual_media/video_production"),
    ("arts/visual_media/video_production", "arts/visual_media/content_creation"),

    # Business, Strategy, Risk & Office
    ("business/management/project_management", "business/management/risk_management"),
    ("business/productivity/excel_mastery", "computing/data/data_analysis"),
    ("business/productivity/excel_mastery", "business/corporate_finance/valuation"),
    ("business/productivity/powerpoint_presentation", "humanities/cognitive_skills/public_speaking"),

    # Cognitive Meta-Skills & Philosophy
    ("humanities/philosophy/epistemology", "humanities/cognitive_skills/analytical_thinking"),
    ("humanities/cognitive_skills/analytical_thinking", "humanities/cognitive_skills/problem_solving"),
    ("humanities/cognitive_skills/problem_solving", "humanities/cognitive_skills/creative_thinking"),
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

def find_best_node_match(query: str, nodes_by_id: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    clean = query.strip("/").lower()
    # 1. Exact match
    if clean in nodes_by_id:
        return nodes_by_id[clean]
    # 2. Match first unit of course
    for nid, node in nodes_by_id.items():
        if nid.lower().startswith(clean + "/01_") or nid.lower().startswith(clean + "/"):
            return node
    # 3. Substring match
    for nid, node in nodes_by_id.items():
        if clean in nid.lower():
            return node
    return None

def get_prerequisite_graph() -> Dict[str, Any]:
    tree = get_topic_tree()

    nodes = []
    nodes_by_id = {}
    course_units_map = defaultdict(list)

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
                course_key = f"{domain}/{disc}/{course}"
                units = c_data.get("units", {})
                course_title = c_data.get("display_name") or course.replace('_', ' ').title()
                for unit, u_data in units.items():
                    rel = u_data["rel_path"]
                    status = u_data["status"]
                    unit_title = u_data.get("display_name") or unit.replace('_', ' ').title()
                    # Single-unit courses: the unit is the course, don't repeat it.
                    if len(units) == 1 or unit_title.strip().lower() == course_title.strip().lower():
                        label = unit_title
                    else:
                        label = f"{course_title}: {unit_title}"
                    node_obj = {
                        "id": rel,
                        "label": label,
                        "domain": domain,
                        "category": f"{disc}/{course}",
                        "subtopic": unit,
                        "complete": status["complete"],
                        "color": color,
                        "prerequisites": [],
                        "unlocks": []
                    }
                    nodes.append(node_obj)
                    nodes_by_id[rel] = node_obj
                    course_units_map[course_key].append(node_obj)

    edges = []
    seen_edges = set()

    def add_edge(src_id: str, dst_id: str):
        if not src_id or not dst_id or src_id == dst_id:
            return
        edge_key = f"{src_id}->{dst_id}"
        if edge_key not in seen_edges and src_id in nodes_by_id and dst_id in nodes_by_id:
            seen_edges.add(edge_key)
            edges.append({"source": src_id, "target": dst_id})
            nodes_by_id[src_id]["unlocks"].append(dst_id)
            nodes_by_id[dst_id]["prerequisites"].append(src_id)

    # 1. Intra-Course Sequential Progression: unit 01 -> unit 02 -> unit 03 -> unit 04
    for course_key, unit_nodes in course_units_map.items():
        # Sort by slug index
        sorted_units = sorted(unit_nodes, key=lambda u: u["subtopic"])
        for i in range(len(sorted_units) - 1):
            add_edge(sorted_units[i]["id"], sorted_units[i + 1]["id"])

    # 2. Inter-Course Discipline Progression: last unit of course A -> first unit of course B
    disciplines_map = defaultdict(list)
    for course_key, unit_nodes in course_units_map.items():
        domain_disc = "/".join(course_key.split("/")[:2])
        disciplines_map[domain_disc].append((course_key, sorted(unit_nodes, key=lambda u: u["subtopic"])))

    for domain_disc, courses_list in disciplines_map.items():
        for i in range(len(courses_list) - 1):
            course_a_units = courses_list[i][1]
            course_b_units = courses_list[i + 1][1]
            if course_a_units and course_b_units:
                add_edge(course_a_units[-1]["id"], course_b_units[0]["id"])

    # 3. Cross-Domain Foundational & Inter-Course Bridges
    for src_query, dst_query in CROSS_DOMAIN_BRIDGES:
        src_node = find_best_node_match(src_query, nodes_by_id)
        dst_node = find_best_node_match(dst_query, nodes_by_id)
        if src_node and dst_node:
            add_edge(src_node["id"], dst_node["id"])

    # Compute degree of centrality for visualization
    for n in nodes:
        n["in_degree"] = len(n["prerequisites"])
        n["out_degree"] = len(n["unlocks"])
        n["degree"] = n["in_degree"] + n["out_degree"]

    return {
        "nodes": nodes,
        "edges": edges,
        "edge_count": len(edges),
        "node_count": len(nodes)
    }

def get_topic_dependencies(rel_path: str) -> Dict[str, Any]:
    """Returns immediate prerequisites and unlocked topics for a specific unit."""
    graph = get_prerequisite_graph()
    clean = rel_path.strip("/").lower()
    nodes_map = {n["id"].lower(): n for n in graph["nodes"]}

    target = nodes_map.get(clean)
    if not target:
        for nid, n in nodes_map.items():
            if clean in nid:
                target = n
                break

    if not target:
        return {"prerequisites": [], "unlocks": []}

    prereqs = [nodes_map[pid] for pid in target["prerequisites"] if pid.lower() in nodes_map]
    unlocks = [nodes_map[uid] for uid in target["unlocks"] if uid.lower() in nodes_map]

    return {
        "target": target,
        "prerequisites": [{"id": p["id"], "label": p["label"], "domain": p["domain"]} for p in prereqs],
        "unlocks": [{"id": u["id"], "label": u["label"], "domain": u["domain"]} for u in unlocks]
    }
