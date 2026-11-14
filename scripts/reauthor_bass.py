#!/usr/bin/env python3
import sys
import os
from pathlib import Path
from datetime import datetime

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from learning_engine.models import AnthropicProvider, validate_generation_output

if not os.getenv("ANTHROPIC_API_KEY"):
    print("[✘] Error: ANTHROPIC_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)

TARGET_PATH = WORKSPACE_ROOT / "topics/arts/music_performance/bass_guitar/lesson_01_technique_and_fretboard_mechanics.md"
if not TARGET_PATH.resolve().is_relative_to(WORKSPACE_ROOT):
    print("[✘] Security: target path escapes workspace root", file=sys.stderr)
    sys.exit(1)

# Backup existing file
if TARGET_PATH.exists():
    backup_path = TARGET_PATH.with_suffix(f".md.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup_path.write_text(TARGET_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[i] Backed up existing file to {backup_path.name}")

p = AnthropicProvider(model="claude-sonnet-5")

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

# Sonnet output bounds
MAX_TOKENS = 8192

try:
    print("[~] Re-authoring bass_guitar lesson 1 with practical musician-first mandate...")
    res = p.generate(prompt, max_tokens=MAX_TOKENS)
    validated = validate_generation_output(res)
    
    if not validated or len(validated.strip()) < 500:
        raise ValueError("Generated content is empty or suspiciously short")
    
    TARGET_PATH.write_text(validated.strip() + "\n", encoding="utf-8")
    print(f"[✔] Re-authored bass_guitar lesson 1: {len(validated.splitlines())} lines written to {TARGET_PATH.name}")
except Exception as e:
    print(f"[✘] Failed to generate lesson: {type(e).__name__}: {e}", file=sys.stderr)
    sys.exit(1)
