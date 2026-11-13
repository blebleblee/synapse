#!/usr/bin/env python3
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, validate_generation_output

p = AnthropicProvider(model="claude-opus-5-5")
path = WORKSPACE_ROOT / "topics/arts/music_performance/bass_guitar/lesson_01_technique_and_fretboard_mechanics.md"

prompt = """You are a master conservatory bass instructor and distinguished touring bassist.
Write the complete, comprehensive, publication-ready masterclass lesson for:
Topic: bass_guitar (Discipline: music_performance, Domain: arts)
Lesson: Lesson 1: Bass Guitar Fretboard Layout and Left-Hand Mechanics

PRACTICALITY FIRST MANDATE (85% Hands-On Execution / 15% Acoustic Grounding):
1. Focus on practical, actionable playing mechanics for someone physically holding a bass guitar:
   - Hand and Wrist Posture: Straight fretting wrist, thumb anchored gently behind the neck opposite the middle finger, curved finger arches, finger pads landing right behind the fret wire.
   - Low-Register vs. High-Register Fingering: Explain Franz Simandl 1-2-4 finger technique for frets 1-5 (index=1, middle=2, pinky+ring=4) to prevent carpal tunnel and tendon strain due to wide fret spacing; transition to One-Finger-Per-Fret (OFPF) above fret 7.
   - Movable Fretboard Box Shapes: Root - Major/Minor 3rd - Perfect 5th - Octave box shapes that can be transposed to any key anywhere on the neck.
   - Practical Drills and Metronome Progressions: Real finger-independence and shifting drills with metronome BPM targets (60 -> 80 -> 100 BPM).
2. ACOUSTIC CAP: Give only 1 concise paragraph on string length, tension, and frequency. ABSOLUTE PROHIBITION: Do NOT write CNC fret slotting math, lutherie formulas, or Python frequency scripts.
3. Every Mermaid diagram must use strict subgraph IDs: subgraph sub_id ["Title"].
4. Output the complete raw Markdown document starting directly with the title '# Lesson 1: Bass Guitar Fretboard Layout and Left-Hand Mechanics'. No outer code fences.
"""

print("[~] Re-authoring bass_guitar lesson 1 with practical musician-first mandate...")
res = p.generate(prompt, max_tokens=6000)
validated = validate_generation_output(res)
path.write_text(validated.strip() + "\n", encoding="utf-8")
print(f"[✔] Re-authored bass_guitar lesson 1: {len(validated.splitlines())} lines!")
