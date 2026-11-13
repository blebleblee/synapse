from pathlib import Path
import time
from .models import LLMProvider, validate_generation_output

def enhance_markdown_file(provider: LLMProvider, file_path: Path, domain: str, subtopic_id: str):
    """Feeds existing markdown to Claude for high-end academic/engineering review and enhancement."""
    content = file_path.read_text(encoding="utf-8")
    
    if len(content.strip()) < 50:
        return False
        
    system_instruction = (
        "You are an elite, world-class staff engineer, distinguished researcher, and master technical author (e.g., O'Reilly/MIT Press standard). "
        "Your goal is to perform a rigorous peer review, enhancement, and expansion of the provided curriculum lesson/lab."
    )
    
    prompt = f"""Review and significantly enhance the following educational material for the topic '{subtopic_id}' in domain '{domain}'.

OBJECTIVES:
1. RIGOR & DEPTH: Expand the material with deep, first-principles technical depth. Explain *why* things work at an architectural level.
2. ZERO HALLUCINATION FACT-CHECKING: Correct any inaccuracies, fabricated APIs, or hallucinated facts immediately. Ensure absolute technical correctness.
3. MERMAID DIAGRAMS & CODE: Add missing or enhance existing Mermaid.js diagrams to visualize complex architectures or data flows. Ensure all Mermaid syntax is perfectly valid (e.g., proper quotes around labels: A -->| "Label" | B). Expand code snippets with robust, production-grade examples (Rust, C, Python, Go, SQL, etc.) where appropriate.
4. REMOVE FLUFF: Remove AI conversational filler. Replace generic bullet points with dense, authoritative prose.
5. COMPLETE REWRITE: Output the FULL, enhanced, publication-ready Markdown file. Do NOT truncate or use placeholders.

ORIGINAL CONTENT:
```markdown
{content}
```

Output the full, enhanced, publication-ready raw Markdown document directly (do NOT wrap the entire document in an outer ```markdown code fence). Start directly with the top-level '# ...' title. No preambles.
"""
    
    for attempt in range(1, 3):
        try:
            attempt_str = f" (attempt {attempt}/2)" if attempt > 1 else ""
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
            if attempt < 2:
                print(f"      [!] Retrying {file_path.name} after timeout/error: {e}", flush=True)
                time.sleep(3)
                continue
            print(f"      [✘] Failed to enhance {file_path.name}: {e}", flush=True)
            return False
    return False

from concurrent.futures import ThreadPoolExecutor, as_completed

def enhance_existing_topic(domain: str, subtopic_id: str, subtopic_dir: Path, provider: LLMProvider, max_workers: int = 3):
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
