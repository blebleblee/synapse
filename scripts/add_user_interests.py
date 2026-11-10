#!/usr/bin/env python3
"""
Add User Interest Topics
Appends security, automotive, retro gaming, and music subtopics to the learning curriculum.
"""

import sys
import subprocess
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.topic_manager import add_subtopic

TOPICS_TO_ADD = [
    # Computing and Engineering -> Security
    ("computing_and_engineering", "security", "web_security", "Web Application Security & OWASP Defenses"),
    ("computing_and_engineering", "security", "vulnerability_research", "Vulnerability Research & Memory Safety"),
    ("computing_and_engineering", "security", "software_exploitation_and_defense", "Software Exploitation Mechanics & Defenses"),
    ("computing_and_engineering", "security", "network_security_and_defense", "Network Security, Telemetry & Defense"),

    # Computing and Engineering -> Software Engineering
    ("computing_and_engineering", "software_engineering", "game_emulation_internals", "Game Emulation Architecture & Virtual Machines"),
    ("computing_and_engineering", "software_engineering", "game_design_and_mechanics", "Game Design Architecture & Mechanics"),

    # Hobbies and Crafts -> Automotive and Motorsports
    ("hobbies_and_crafts", "automotive_and_motorsports", "car_mechanics", "Automotive Engineering & Car Mechanics"),
    ("hobbies_and_crafts", "automotive_and_motorsports", "motorcycle_mechanics", "Motorcycle Mechanics & Powertrains"),
    ("hobbies_and_crafts", "automotive_and_motorsports", "performance_driving", "High-Performance Driving & Vehicle Dynamics"),
    ("hobbies_and_crafts", "automotive_and_motorsports", "motorcycle_riding_dynamics", "Motorcycle Riding Dynamics & Roadcraft"),
    ("hobbies_and_crafts", "automotive_and_motorsports", "vehicle_diagnostics_and_maintenance", "Vehicle Maintenance, Wrenching & Diagnostics"),

    # Hobbies and Crafts -> Retro Gaming
    ("hobbies_and_crafts", "retro_gaming", "retro_console_hardware", "Retro Console Hardware (8-bit & 16-bit Systems)"),
    ("hobbies_and_crafts", "retro_gaming", "arcade_mechanics_and_restoration", "Arcade Systems, JAMMA & CRT Mechanics"),
    ("hobbies_and_crafts", "retro_gaming", "speedrunning_and_glitch_mechanics", "Speedrunning, Glitch Mechanics & Memory Inspection"),

    # Arts and Humanities -> Music
    ("arts_and_humanities", "music", "orchestral_composition", "Orchestral Composition & Symphony Scoring"),
    ("arts_and_humanities", "music", "midi_and_sequencing", "MIDI Protocol, MPE & Hardware Sequencing"),
    ("arts_and_humanities", "music", "audio_effects_and_processing", "Audio Effects, DSP & Dynamics Processing"),
]

def main():
    print("==================================================")
    print("   ADDING USER INTEREST TOPICS TO CURRICULUM      ")
    print("==================================================")

    added = []
    for domain, category, subtopic_id, title in TOPICS_TO_ADD:
        print(f"[*] Adding: {domain} / {category} / {subtopic_id} ('{title}')...")
        path = add_subtopic(domain, category, subtopic_id, title)
        added.append((domain, category, subtopic_id, path))

    print(f"\n[✔] Successfully added {len(added)} new subtopics to curriculum.")

    # Stage and commit changes to Git and push to Gitea
    try:
        print("[*] Committing new topics to Git and pushing to Gitea...")
        subprocess.run(["git", "add", "topics/"], check=True, cwd=str(WORKSPACE_ROOT))
        msg = f"curriculum: add {len(added)} user interest topics (security, automotive, retro gaming, music)"
        subprocess.run(["git", "commit", "-m", msg], check=True, cwd=str(WORKSPACE_ROOT))
        subprocess.run(["git", "push", "origin", "main"], check=True, cwd=str(WORKSPACE_ROOT))
        print("[✔] Pushed to Gitea successfully!")
    except Exception as e:
        print(f"[!] Git sync error: {e}")

if __name__ == "__main__":
    main()
