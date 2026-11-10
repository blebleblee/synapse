#!/usr/bin/env python3
"""
Automated Global Curriculum Generator
Iterates through every topic in the workspace, reads SYLLABUS.md,
and generates a LESSON.md for every subtopic using the Gemini API.
"""

import os
import sys
import time
import re
from pathlib import Path

try:
    from google import genai
    from google.genai import types
except ImportError:
    print("Error: 'google-genai' package is not installed.")
    sys.exit(1)

# Support both Vertex AI and Google AI Studio API Keys
GCP_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCP_PROJECT")
GCP_LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

if GCP_PROJECT:
    print(f"[*] Authenticating via Vertex AI (Project: {GCP_PROJECT})")
    client = genai.Client(vertexai=True, project=GCP_PROJECT, location=GCP_LOCATION)
elif API_KEY:
    print("[*] Authenticating via Gemini API Key")
    client = genai.Client(api_key=API_KEY)
else:
    print("Error: Neither GOOGLE_CLOUD_PROJECT nor GEMINI_API_KEY was found.")
    sys.exit(1)

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
TOPICS_DIR = WORKSPACE_ROOT / "topics"
MODEL_NAME = os.environ.get("GEMINI_MODEL", "gemini-2.5-pro")

def generate_subtopic_lesson(topic_name, subtopic_name, subtopic_dir, system_instruction):
    dest_path = subtopic_dir / "LESSON.md"
    if dest_path.exists() and dest_path.stat().st_size > 500:
        print(f"[↷] Skipping {topic_name} / {subtopic_name} (LESSON.md already exists)")
        return

    print(f"[*] Generating lesson for {topic_name} -> {subtopic_name}")
    prompt = f"Write an exhaustive, complete technical lesson on the subtopic of '{subtopic_name}'. This is part of a broader course on '{topic_name}'. Include deep theory, practical examples, architecture/formulas where applicable, and a summary. Format strictly in Markdown."

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2,
            ),
        )

        content = response.text
        subtopic_dir.mkdir(parents=True, exist_ok=True)
        with open(dest_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"[✔] Successfully generated and wrote: {dest_path}")

    except Exception as e:
        print(f"[✘] Failed to generate for {subtopic_name}: {e}")

def main():
    print("Starting automated batch generation for all topics...")

    for topic_path in TOPICS_DIR.iterdir():
        if not topic_path.is_dir():
            continue

        topic_name = topic_path.name
        print(f"\n==================================================")
        print(f"[*] Scanning Topic: {topic_name.upper()}")
        print(f"==================================================")

        # Read the persona/system instruction for this specific topic
        gemini_md = topic_path / "GEMINI.md"
        system_instruction = "You are an expert educator. Provide a highly detailed lesson."
        if gemini_md.exists():
            system_instruction = gemini_md.read_text(encoding="utf-8")

        syllabus_md = topic_path / "SYLLABUS.md"
        if not syllabus_md.exists():
            print(f"[!] No SYLLABUS.md found for {topic_name}, skipping.")
            continue

        content = syllabus_md.read_text(encoding="utf-8")
        # Matches patterns like: - **Calculus** (`calculus/`)
        pattern = r"-\s+\*\*(.*?)\*\*\s+\(\`(.*?)/\`\)"
        matches = re.findall(pattern, content)

        if not matches:
            print(f"[!] Could not parse any subtopics from {topic_name}/SYLLABUS.md")
            continue

        for subtopic_name, subtopic_folder in matches:
            subtopic_dir = topic_path / subtopic_folder
            generate_subtopic_lesson(topic_name, subtopic_name, subtopic_dir, system_instruction)
            time.sleep(5)  # Wait 5 seconds to respect rate limits

    print("\n[✔] Master generation complete!")

if __name__ == "__main__":
    main()
