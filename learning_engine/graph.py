"""
Prerequisite Learning Graph (DAG) Engine
Models and visualizes cross-domain learning dependencies.
"""

from typing import Dict, List, Any
from .topic_manager import get_topic_tree

# Explicit Cross-Disciplinary Prerequisite Dependencies (source -> target)
PREREQUISITES_DAG = [
    # Systems & Kernel
    ("computing/software/systems_programming", "computing/infrastructure/linux_kernel"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/device_drivers"),
    ("computing/infrastructure/linux_kernel", "computing/infrastructure/ebpf"),
    ("computing/infrastructure/ebpf", "computing/security/network_defense"),
    ("computing/infrastructure/linux", "computing/infrastructure/kubernetes"),
    ("computing/infrastructure/kubernetes", "computing/infrastructure/harvester"),

    # Low-Level Computing & Exploiting
    ("engineering/hardware/computer_architecture", "engineering/hardware/assembly_programming"),
    ("engineering/hardware/assembly_programming", "computing/security/reverse_engineering"),
    ("computing/security/reverse_engineering", "computing/security/software_exploitation"),
    ("computing/security/software_exploitation", "computing/security/exploit_defense"),
    ("computing/security/reverse_engineering", "computing/security/hardware_hacking"),

    # Security & Automotive
    ("computing/infrastructure/networking", "computing/security/network_security"),
    ("computing/software/web_development", "computing/security/web_security"),
    ("engineering/circuits/circuit_theory", "computing/security/hardware_hacking"),
    ("motorsports/driving/vehicle_diagnostics", "computing/security/automotive_cybersecurity"),
    ("engineering/circuits/rf_engineering", "computing/security/software_defined_radio"),

    # Mathematics & Quantitative Finance
    ("formal_sciences/pure_math/algebra", "formal_sciences/pure_math/linear_algebra"),
    ("formal_sciences/pure_math/calculus", "formal_sciences/pure_math/differential_equations"),
    ("formal_sciences/pure_math/linear_algebra", "formal_sciences/applied_math/optimization"),
    ("formal_sciences/pure_math/calculus", "formal_sciences/applied_math/optimization"),
    ("formal_sciences/applied_math/probability", "formal_sciences/applied_math/statistics"),
    ("formal_sciences/applied_math/optimization", "business/trading/quant"),
    ("formal_sciences/applied_math/statistics", "business/trading/quant"),
    ("formal_sciences/applied_math/game_theory", "economics/microeconomics/microeconomic_foundations"),

    # Physics & Motorsports
    ("natural_sciences/physics/classical_mechanics", "natural_sciences/physics/aerodynamics"),
    ("natural_sciences/physics/aerodynamics", "natural_sciences/physics/flight_dynamics"),
    ("natural_sciences/physics/classical_mechanics", "motorsports/driving/vehicle_dynamics"),
    ("motorsports/driving/vehicle_dynamics", "motorsports/driving/performance_driving"),

    # Audio & Music Engineering
    ("arts/music_production/acoustics", "arts/music_production/audio_engineering"),
    ("arts/music_production/audio_engineering", "arts/music_production/audio_effects"),
    ("formal_sciences/pure_math/calculus", "arts/music_production/audio_dsp"),
    ("arts/music_production/audio_dsp", "arts/music_production/audio_plugins"),
    ("engineering/circuits/circuit_theory", "arts/music_production/modular_synthesis"),
    ("arts/composition/music_theory", "arts/composition/counterpoint"),
    ("arts/composition/counterpoint", "arts/composition/orchestration"),
    ("arts/composition/orchestration", "arts/composition/orchestral_scoring"),

    # Fabrication & Metalworking
    ("crafts/metalworking/metal_fabrication", "crafts/metalworking/welding"),
    ("crafts/metalworking/machining", "crafts/metalworking/cnc"),
    ("crafts/3d_printing/cad_modeling", "crafts/3d_printing/slicing")
]

def get_prerequisite_graph() -> Dict[str, Any]:
    tree = get_topic_tree()

    # Index all nodes with metadata
    nodes = []
    node_set = set()

    # Domain color palette for graph visualization
    DOMAIN_COLORS = {
        "computing": "#58a6ff",
        "engineering": "#3fb950",
        "formal_sciences": "#bc8cff",
        "natural_sciences": "#39c5cf",
        "business": "#d29922",
        "economics": "#f0883e",
        "arts": "#ff7b72",
        "humanities": "#e3b341",
        "crafts": "#79c0ff",
        "motorsports": "#ffa657"
    }

    for domain, ddata in tree.items():
        color = DOMAIN_COLORS.get(domain, "#8b949e")
        for cat, cdata in ddata["categories"].items():
            for sub, sdata in cdata.items():
                rel = sdata["rel_path"]
                status = sdata["status"]
                node_set.add(rel)
                nodes.append({
                    "id": rel,
                    "label": sdata["display_name"],
                    "domain": domain,
                    "category": cat,
                    "subtopic": sub,
                    "complete": status["complete"],
                    "color": color
                })

    edges = []
    for src, dst in PREREQUISITES_DAG:
        if src in node_set and dst in node_set:
            edges.append({
                "source": src,
                "target": dst
            })

    return {
        "nodes": nodes,
        "edges": edges,
        "edge_count": len(edges),
        "node_count": len(nodes)
    }
