from pathlib import Path
import time
from .models import LLMProvider, validate_generation_output

def enhance_markdown_file(provider: LLMProvider, file_path: Path, domain: str, subtopic_id: str):
    """Feeds existing markdown to Claude for high-end academic/engineering review and enhancement."""
    content = file_path.read_text(encoding="utf-8")
    
    if len(content.strip()) < 50:
        return False
        
    domain_gemini = Path(__file__).resolve().parent.parent / "topics" / domain / "GEMINI.md"
    domain_instructions = ""
    if domain_gemini.exists():
        try:
            domain_instructions = domain_gemini.read_text(encoding="utf-8")
        except Exception:
            pass

    system_instruction = (
        f"You are a master practitioner, distinguished educator, and authoritative author in '{domain}'. "
        "Your mission is to produce highly practical, actionable, and rigorously grounded masterclass lessons and labs.\n\n"
        "PRACTICALITY FIRST MANDATE:\n"
        "- 80% Actionable Execution: Focus on concrete, hands-on techniques, physical mechanics, step-by-step procedures, runnable code/manifests/drills, and real-world troubleshooting.\n"
        "- 20% First-Principles Intuition: Ground the practice in core theory/physics, but NEVER let abstract math, academic derivations, or disconnected scripts overshadow hands-on mastery.\n"
        "- Zero Placeholder Policy: Provide complete, runnable, and immediately useful examples with zero stubs.\n\n"
        + (f"DOMAIN INSTRUCTIONS:\n{domain_instructions}\n" if domain_instructions else "")
    )

    prompt = f"""Review and significantly enhance the following educational material for the topic '{subtopic_id}' in domain '{domain}'.

CORE MANDATES:
1. PRACTICAL & ACTIONABLE: Make this material immediately useful for someone physically practicing or executing this discipline.
   - In music performance & instruments: Focus on hands-on playing ergonomics, hand posture, fingerings, fretboard/keyboard box shapes, chord voicings, and practice drills with metronome targets. Do NOT write instrument builder / lutherie math papers or python frequency calculators.
   - In engineering & computing: Focus on production-grade architectures, real CLI/API commands, working code, and concrete debugging procedures.
   - In crafts & fabrication: Focus on feeds, speeds, toolpaths, physical clamping, material behavior, and real G-code / fabrication parameters.
2. TECHNICAL DEPTH: Explain *why* techniques work without drowning the practitioner in disconnected academic formalism.
3. REMOVE TEMPLATE FLUFF: Discard any generic or mismatched template boilerplate from earlier drafts. Anchor 100% to '{subtopic_id}'.
4. MERMAID DIAGRAMS & FORMATTING: Ensure all Mermaid diagrams use strict subgraph IDs (subgraph sub_id ["Title"]). Do NOT wrap output in outer ```markdown fences.
5. COMPLETE REWRITE: Output the FULL, enhanced, publication-ready raw Markdown file starting directly with '# ...'. No preambles.

ORIGINAL CONTENT:
```markdown
{content}
```

Output the full, enhanced, publication-ready raw Markdown document directly (do NOT wrap the entire document in an outer ```markdown code fence). Start directly with the top-level '# ...' title. No preambles.
"""
    
    for attempt in range(1, 4):
        try:
            attempt_str = f" (attempt {attempt}/3)" if attempt > 1 else ""
            print(f"      [~] Enhancing {file_path.name} via {provider.model}{attempt_str}...", flush=True)
            t0 = time.time()
            enhanced = provider.generate(prompt, system_instruction=system_instruction)
            validated = validate_generation_output(enhanced)

            # Safety check: if Claude failed completely, don't overwrite
            if len(validated) < len(content) * 0.3:
                print(f"      [!] {file_path.name} enhancement aborted (output too short).", flush=True)
                return False

            file_path.write_text(validated.strip() + "\n", encoding="utf-8")
            elapsed = time.time() - t0
            print(f"      [✔] Enhanced {file_path.name} in {elapsed:.1f}s", flush=True)
            return True
        except Exception as e:
            if attempt < 3:
                backoff = attempt * 4
                print(f"      [!] Retrying {file_path.name} after timeout/error: {e} (waiting {backoff}s)", flush=True)
                time.sleep(backoff)
                continue
            print(f"      [✘] Failed to enhance {file_path.name}: {e}", flush=True)
            return False
    return False

from concurrent.futures import ThreadPoolExecutor, as_completed

def enhance_existing_topic(domain: str, subtopic_id: str, subtopic_dir: Path, provider: LLMProvider, max_workers: int = 2):
    """Enhances markdown files in a topic concurrently using a thread pool."""
    md_files = sorted(list(subtopic_dir.glob("*.md")))
    if not md_files:
        return False
        
    pool_size = min(max_workers, len(md_files))
    print(f"  [*] Starting deep parallel enhancement of '{subtopic_id}' ({len(md_files)} files, {pool_size} concurrent workers) with {provider.model}...", flush=True)
    
    success_count = 0
    with ThreadPoolExecutor(max_workers=pool_size) as executor:
        future_to_file = {
            executor.submit(enhance_markdown_file, provider, md_file, domain, subtopic_id): md_file
            for md_file in md_files
        }
        for future in as_completed(future_to_file):
            if future.result():
                success_count += 1
            
    return success_count == len(md_files)
