#!/usr/bin/env python3
"""
Add Recommended Deep-Systems, Hardware Security, and Fabrication Topics
Extends the curriculum with low-level systems, hardware hacking, automotive cybersecurity,
audio DSP, and metalworking fabrication.
"""

import sys
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.topic_manager import add_subtopic

RECOMMENDED_TOPICS = [
    # 1. Hardware & Embedded Security
    ("computing_and_engineering", "security", "hardware_hacking", "Hardware Hacking, JTAG/UART Probing & Firmware Dumping"),
    ("computing_and_engineering", "security", "automotive_cybersecurity", "Automotive Cybersecurity, CAN Bus & Telemetry"),
    ("computing_and_engineering", "security", "software_defined_radio", "Software-Defined Radio (SDR) & RF Security"),

    # 2. Deep Systems Engineering
    ("computing_and_engineering", "hardware_and_circuits", "computer_architecture_and_assembly", "Computer Architecture, CPU Caches & Assembly (x86/ARM)"),
    ("computing_and_engineering", "infrastructure_and_ops", "linux_kernel_and_drivers", "Linux Kernel Internals & Device Driver Engineering"),
    ("computing_and_engineering", "software_engineering", "systems_programming", "Low-Level Systems Programming in C and Rust"),

    # 3. Audio DSP & Synthesis
    ("arts_and_humanities", "music", "audio_dsp_and_plugins", "Audio DSP & Plugin Architecture (VST/AU & Filters)"),
    ("arts_and_humanities", "music", "modular_synthesis", "Modular Synthesis, Control Voltage & Eurorack Patching"),

    # 4. Metalworking & Machining
    ("hobbies_and_crafts", "metalworking", "welding_and_metal_fabrication", "Metal Fabrication, TIG/MIG Welding & Structural Joints"),
    ("hobbies_and_crafts", "metalworking", "machining_and_cnc", "Precision Machining, Lathes, Mills & CNC G-Code"),

    # 5. Aerodynamics & Flight Dynamics
    ("natural_sciences", "physics", "aerodynamics_and_flight_dynamics", "Aerodynamics, Fluid Dynamics & Flight Mechanics"),
]

def main():
    print("==================================================")
    print("   ADDING RECOMMENDED CROSS-DISCIPLINARY TOPICS   ")
    print("==================================================")

    added = []
    for domain, category, subtopic_id, title in RECOMMENDED_TOPICS:
        print(f"[*] Adding: {domain} / {category} / {subtopic_id} ('{title}')...")
        path = add_subtopic(domain, category, subtopic_id, title)
        added.append((domain, category, subtopic_id, path))

    print(f"\n[✔] Successfully added {len(added)} high-value subtopics to curriculum.")

    # Stage and commit changes to Git and push to Gitea
    try:
        print("[*] Committing new topics to Git and pushing to Gitea...")
        subprocess.run(["git", "pull", "--rebase", "origin", "main"], check=True, cwd=str(WORKSPACE_ROOT))
        subprocess.run(["git", "add", "topics/"], check=True, cwd=str(WORKSPACE_ROOT))
        msg = f"curriculum: add {len(added)} cross-disciplinary topics (hardware hacking, automotive cyber, assembly, audio DSP, metalworking)"
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=str(WORKSPACE_ROOT))
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=str(WORKSPACE_ROOT))
        print("[✔] Pushed to Gitea successfully!")
    except Exception as e:
        print(f"[!] Git sync error: {e}")

if __name__ == "__main__":
    main()
