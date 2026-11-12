from pathlib import Path
from typing import Dict, Any, List, Optional
import re
from .security import validate_workspace_path
from .mastery import get_completed_lessons as mastery_get_completed
from .utils import scan_subtopic_status as utils_scan_subtopic_status, get_unit_lessons as utils_get_unit_lessons
from .constants import LEVELS

class TaxonomyService:
    """Handles raw filesystem traversal and curriculum taxonomy."""
    def __init__(self, topics_dir: Path, workspace_root: Path):
        self.topics_dir = validate_workspace_path(topics_dir.parent, topics_dir)
        self.workspace_root = workspace_root
        self.levels = LEVELS


    def list_domains(self) -> List[str]:
        raw = [d.name for d in self.topics_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
        return sorted(raw)

    def get_topic_tree(self) -> Dict[str, Any]:
        tree = {}
        for domain in self.list_domains():
            domain_dir = self.topics_dir / domain
            syllabus_file = domain_dir / "SYLLABUS.md"
            
            tree[domain] = {
                "path": str(domain_dir.relative_to(self.workspace_root)),
                "disciplines": {},
                "categories": {} 
            }
            
            if not syllabus_file.exists():
                continue
                
            content = syllabus_file.read_text(encoding="utf-8")
            pattern = r"-\s+\*\*(.*?)\*\*\s+\(\`(.*?)/\`\)"
            matches = re.findall(pattern, content)
            
            # Extract human-readable course titles
            course_display_names = {}
            current_section = ""
            for line in content.splitlines():
                line_str = line.strip()
                if line_str.startswith("### "):
                    current_section = line_str.lstrip("#").strip()
                elif line_str.startswith("- **"):
                    m = re.match(r"-\s+\*\*(.*?)\*\*\s+\(\`(.*?)/\`\)", line_str)
                    if m:
                        _, u_rel = m.groups()
                        u_parts = u_rel.split("/")
                        u_disc = u_parts[0] if len(u_parts) >= 2 else "general"
                        u_course = u_parts[1] if len(u_parts) >= 2 else u_parts[0]
                        
                        if current_section and (u_disc, u_course) not in course_display_names:
                            c_title = current_section.split(":", 1)[1].strip() if ":" in current_section else current_section
                            course_display_names[(u_disc, u_course)] = c_title if c_title.lower() != u_disc.lower() else u_course.replace("_", " ").title()

            for display_name, rel_path in matches:
                parts = rel_path.split("/")
                if len(parts) >= 3:
                    disc = parts[0]
                    course = parts[1]
                    unit = "/".join(parts[2:])
                elif len(parts) == 2:
                    disc = parts[0]
                    course = parts[1]
                    unit = "core"
                else:
                    disc = "general"
                    course = parts[0]
                    unit = "core"
                
                if disc not in tree[domain]["disciplines"]:
                    tree[domain]["disciplines"][disc] = {"courses": {}}
                    tree[domain]["categories"][disc] = {}
                
                if unit == "core":
                    c_display_title = display_name
                else:
                    c_display_title = course_display_names.get((disc, course), course.replace("_", " ").title())

                if course not in tree[domain]["disciplines"][disc]["courses"]:
                    tree[domain]["disciplines"][disc]["courses"][course] = {
                        "display_name": c_display_title,
                        "units": {}
                    }
                    
                full_path = self.topics_dir / domain / rel_path

                # Ensure status is populated correctly
                status = self.scan_subtopic_status(full_path, self.levels)

                node_data = {
                    "display_name": display_name,
                    "domain": domain,
                    "discipline": disc,
                    "course": course,
                    "course_title": course_display_names.get((disc, course), course.replace("_", " ").title()),
                    "unit": unit,
                    "rel_path": f"{domain}/{rel_path}",
                    "full_path": str(full_path),
                    "status": status,
                    "lessons": self.get_unit_lessons(full_path),
                    "completed_lessons": mastery_get_completed(f"{domain}/{rel_path}"),
                    "has_summary": (full_path / "SUMMARY.md").exists()
                }

                tree[domain]["disciplines"][disc]["courses"][course]["units"][unit] = node_data

                # Legacy mapping
                flat_key = f"{course}_{unit}" if unit != "core" else course
                tree[domain]["categories"][disc][flat_key] = node_data
                
        return tree

    def scan_subtopic_status(self, unit_dir: Path, levels: List[str]) -> Dict[str, Any]:
        level_status = {}
        for lvl in levels:
            lvl_dir = unit_dir / lvl
            f = (lvl_dir / "FOUNDATION.md").exists()
            l = (lvl_dir / "LESSON.md").exists()
            b = (lvl_dir / "LABS.md").exists()
            level_status[lvl] = {
                "has_foundation": f,
                "has_lesson": l,
                "has_labs": b,
                "complete": (f and l and b)
            }

        root_f = (unit_dir / "FOUNDATION.md").exists() or (unit_dir / "foundation.md").exists()
        root_l = (unit_dir / "LESSON.md").exists() or (unit_dir / "lesson.md").exists()
        root_b = (unit_dir / "LABS.md").exists() or (unit_dir / "labs.md").exists()

        all_unit_lessons = self.get_unit_lessons(unit_dir)
        sequential_lessons = [l for l in all_unit_lessons if l["id"].startswith("lesson_")]
        has_multi_lessons = len(sequential_lessons) >= 1
        has_labs = (unit_dir / "labs.md").exists() or (unit_dir / "LABS.md").exists()

        has_foundation = any(s["has_foundation"] for s in level_status.values()) or root_f or has_multi_lessons
        has_lesson = any(s["has_lesson"] for s in level_status.values()) or root_l or has_multi_lessons

        is_leveled_complete = all(s["complete"] for s in level_status.values()) if level_status else False
        is_root_complete = (root_f and (root_l or has_multi_lessons) and root_b)
        is_masterclass_complete = has_multi_lessons and has_labs
        has_legacy_content = (is_leveled_complete or is_root_complete) and not is_masterclass_complete

        all_files = [f.name for f in unit_dir.iterdir() if f.is_file() and not f.name.startswith(".")] if unit_dir.exists() else []

        return {
            "has_foundation": has_foundation,
            "has_lesson": has_multi_lessons or has_lesson,
            "has_labs": has_labs,
            "complete": is_masterclass_complete,
            "is_legacy": has_legacy_content,
            "is_masterclass": is_masterclass_complete,
            "levels": level_status,
            "lesson_count": len(sequential_lessons),
            "lessons": [l["id"] for l in sequential_lessons],
            "file_count": len(all_files),
            "files": all_files
        }

    def get_unit_lessons(self, unit_dir: Path) -> List[Dict[str, str]]:
        if not unit_dir.exists():
            return []

        lessons = []
        files = sorted(list(unit_dir.glob("lesson_*.md")))
        lessons_subdir = unit_dir / "lessons"
        if lessons_subdir.exists():
            files.extend(sorted(list(lessons_subdir.glob("*.md"))))

        artifacts_dir = unit_dir / "artifacts"
        if not files and artifacts_dir.exists():
            files.extend(sorted(list(artifacts_dir.glob("lesson_*.md"))))

        for f in files:
            title = ""
            try:
                for line in f.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("# "):
                        title = line.lstrip("# ").strip()
                        break
            except Exception:
                pass
            if not title:
                cleaned = f.stem.replace("lesson_", "Lesson ").replace("_", " ").title()
                title = cleaned

            lessons.append({
                "id": f.stem,
                "title": title,
                "filename": f.name,
                "path": str(f)
            })

        if not lessons and (unit_dir / "LESSON.md").exists():
            f = unit_dir / "LESSON.md"
            title = "Technical Lesson"
            try:
                for line in f.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("# "):
                        title = line.lstrip("# ").strip()
                        break
            except Exception:
                pass
            lessons.append({
                "id": "lesson",
                "title": title,
                "filename": "LESSON.md",
                "path": str(f)
            })

        return lessons

class CurriculumManagerService:
    """Handles CRUD operations for the curriculum."""
    def __init__(self, topics_dir: Path, workspace_root: Path):
        self.topics_dir = topics_dir
        self.workspace_root = workspace_root
        self.taxonomy = TaxonomyService(topics_dir, workspace_root)

    def add_subtopic(self, domain: str, category: str, subtopic_id: str, display_name: Optional[str] = None) -> Path:
        from .security import sanitize_topic_path, validate_workspace_path
        domain, category, subtopic_id = sanitize_topic_path(domain, category, subtopic_id)
        
        domain_dir = self.topics_dir / domain
        target_dir = validate_workspace_path(self.topics_dir, domain_dir / category / subtopic_id)
        
        target_dir.mkdir(parents=True, exist_ok=True)
        rel_entry = f"{category}/{subtopic_id}"
        display_title = display_name or subtopic_id.replace("_", " ").title()
        syllabus_file = domain_dir / "SYLLABUS.md"
        syllabus_entry = f"- **{display_title}** (`{rel_entry}/`)"

        if syllabus_file.exists():
            content = syllabus_file.read_text(encoding="utf-8")
            if rel_entry not in content:
                parts = category.split("/")
                header_name = parts[-1].replace("_", " ").title()
                cat_header = f"### {header_name}"
                if cat_header in content:
                    p = content.split(cat_header)
                    new_content = p[0] + cat_header + f"\n{syllabus_entry}" + p[1]
                    syllabus_file.write_text(new_content, encoding="utf-8")
                else:
                    content += f"\n\n{cat_header}\n\n{syllabus_entry}\n"
                    syllabus_file.write_text(content, encoding="utf-8")
        else:
            syllabus_file.write_text(f"# Syllabus: {domain.replace('_', ' ').title()}\n\n### {category.replace('_', ' ').title()}\n\n{syllabus_entry}\n", encoding="utf-8")

        return target_dir

    def delete_subtopic(self, rel_path: str) -> bool:
        from .security import validate_workspace_path
        from .mastery import load_mastery_data, save_mastery_data
        
        target_dir = validate_workspace_path(self.topics_dir, self.topics_dir / rel_path)
        
        clean_rel = rel_path.strip("/")
        parts = clean_rel.split("/")
        if len(parts) < 2: return False
        domain = parts[0]
        sub_rel = "/".join(parts[1:])

        if target_dir.exists():
            shutil.rmtree(target_dir)

        syllabus_file = self.topics_dir / domain / "SYLLABUS.md"
        if syllabus_file.exists():
            lines = syllabus_file.read_text(encoding="utf-8").splitlines()
            filtered = [l for l in lines if f"`{sub_rel}/`" not in l and f"`{sub_rel}`" not in l]
            syllabus_file.write_text("\n".join(filtered) + "\n", encoding="utf-8")

        try:
            mdata = load_mastery_data()
            if clean_rel in mdata:
                del mdata[clean_rel]
                save_mastery_data(mdata)
        except Exception: pass
        return True

