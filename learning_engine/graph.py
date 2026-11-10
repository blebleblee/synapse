"""
Prerequisite Learning Graph (DAG) Engine
Models, resolves, and visualizes cross-domain learning dependencies across 4-level study units.
"""

from typing import Dict, List, Any, Optional
from .topic_manager import get_topic_tree

# Explicit Cross-Disciplinary Prerequisite Dependencies (source course -> target course)
PREREQUISITES_DAG = [
    # Systems, Kernels & Rust
    ("computing/software/rust_systems", "computing/infrastructure/linux_device_drivers"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/linux_device_drivers"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/ebpf"),
    ("computing/infrastructure/ebpf", "computing/infrastructure/kubernetes"),
    ("computing/infrastructure/kubernetes", "computing/infrastructure/harvester"),

    # Low-Level Computing, Hardware & Reverse Engineering
    ("engineering/hardware/computer_architecture", "engineering/hardware/assembly_programming"),
    ("engineering/hardware/assembly_programming", "computing/security/reverse_engineering"),
    ("computing/security/reverse_engineering", "computing/security/software_exploitation"),
    ("computing/security/software_exploitation", "computing/security/exploit_defense"),
    ("computing/security/reverse_engineering", "computing/security/hardware_hacking"),

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

    # Physics, Aerodynamics & Motorsports
    ("natural_sciences/physics/classical_mechanics", "motorsports/driving/aerodynamics"),
    ("motorsports/driving/aerodynamics", "motorsports/driving/performance_driving"),
    ("natural_sciences/physics/classical_mechanics", "motorsports/driving/vehicle_dynamics"),
    ("motorsports/driving/vehicle_dynamics", "motorsports/driving/performance_driving"),

    # Audio DSP, Synthesizers & Music Performance
    ("arts/music_performance/piano", "arts/composition/music_theory"),
    ("arts/composition/music_theory", "arts/composition/counterpoint"),
    ("arts/composition/counterpoint", "arts/composition/orchestration"),
    ("arts/composition/orchestration", "arts/composition/orchestral_scoring"),
    ("arts/music_performance/piano", "arts/music_production/synthesizers"),
    ("arts/music_production/synthesizers", "arts/music_production/modular_synthesis"),
    ("formal_sciences/pure_math/calculus", "arts/music_production/audio_dsp"),
    ("arts/music_production/audio_dsp", "arts/music_production/audio_plugins"),
    ("arts/music_production/acoustics", "arts/music_production/audio_engineering"),

    # Fabrication, Welding & CNC Machining
    ("crafts/metalworking/metal_fabrication", "crafts/metalworking/welding"),
    ("crafts/metalworking/welding", "crafts/metalworking/cnc_machining"),
    ("crafts/3d_printing/cad_modeling", "crafts/3d_printing/slicing"),

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
