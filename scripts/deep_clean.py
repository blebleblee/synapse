import shutil
import re
from pathlib import Path

TOPICS_DIR = Path("topics")

def deep_clean():
    print("[*] Starting deep curriculum cleanup...")
    
    # Define allowed patterns
    # Keep: SYLLABUS.md (in domain dir), GEMINI.md, sessions/, lesson_*.md, labs.md, summary.md
    
    for path in TOPICS_DIR.rglob("*"):
        if path.is_file():
            # Allowed files:
            # 1. SYLLABUS.md in domain root
            # 2. GEMINI.md in any topic/discipline/domain
            # 3. lesson_*.md
            # 4. labs.md
            # 5. summary.md
            
            is_allowed = (
                path.name == "SYLLABUS.md" or
                path.name == "GEMINI.md" or
                re.match(r"^lesson_\d{2}_.*\.md$", path.name) or
                path.name == "labs.md" or
                path.name == "summary.md"
            )
            
            if not is_allowed:
                print(f"  [Removing File] {path}")
                path.unlink()
                
        elif path.is_dir():
            # Directories to keep:
            # 1. sessions/
            # 2. Artifacts if strictly needed? Actually, let's keep it simple: 
            #    Remove empty directories and old leveled directories (beginner/...)
            if path.name in ["beginner", "intermediate", "advanced", "lessons", "artifacts"]:
                 # Just remove them, they are legacy
                 shutil.rmtree(path)
                 print(f"  [Removing Dir] {path}")
            elif path.name != "sessions" and not any(path.iterdir()):
                 # Remove if empty and not a sessions dir
                 path.rmdir()
                 print(f"  [Removing Empty Dir] {path}")

deep_clean()
print("[✔] Deep cleanup complete.")
