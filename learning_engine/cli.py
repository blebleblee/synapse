"""
Learning Workspace CLI
Interactive management for curricula, multi-tier lesson generation, search, linting, and export.
"""

import sys
import argparse
import os
import subprocess
import shutil
from pathlib import Path

from learning_engine.security import get_workspace_root, get_topics_dir
WORKSPACE_ROOT = get_workspace_root()
from learning_engine.topic_manager import (
    get_topic_tree,
    list_domains,
    resolve_subtopic,
    add_subtopic,
    get_domain_persona
)
from learning_engine.models import get_provider, OllamaProvider, OllamaCluster, load_env_file, get_node_name
from learning_engine.generator import generate_subtopic_content
from learning_engine.search import search_curriculum
from learning_engine.graph import get_prerequisite_graph
from learning_engine.linter import lint_curriculum
from learning_engine.exporter import export_handbook
from learning_engine.mastery import get_mastery_summary, set_subtopic_mastery
from learning_engine.flashcards import generate_flashcards
from learning_engine.reviewer import review_and_fix_unit, audit_content
from learning_engine.database import get_connection
import json

def format_status_badge(status: dict) -> str:
    l = "L" if status.get("has_lesson") else "."
    b = "B" if status.get("has_labs") else "."
    return f"[{l}{b}]"

def cmd_status(args):
    tree = get_topic_tree()
    total_domains = len(tree)
    total_disciplines = 0
    total_topics = 0
    masterclass_topics = 0
    masterclass_lessons = 0
    masterclass_labs = 0
    legacy_stubs = 0

    for domain, ddata in tree.items():
        disciplines = ddata.get("disciplines", {})
        total_disciplines += len(disciplines)
        for disc, disc_data in disciplines.items():
            courses = disc_data.get("courses", {})
            for course, c_data in courses.items():
                units = c_data.get("units", {})
                for unit, u_data in units.items():
                    total_topics += 1
                    status = u_data.get("status", {})
                    lessons = u_data.get("lessons", [])
                    seq_lessons = [l for l in lessons if l.get("id", "").startswith("lesson_")]
                    has_labs = status.get("has_labs", False)

                    if len(seq_lessons) > 0 and has_labs:
                        masterclass_topics += 1
                        masterclass_lessons += len(seq_lessons)
                        masterclass_labs += 1
                    elif status.get("is_legacy", False) or status.get("has_lesson", False):
                        legacy_stubs += 1

    # Mastery statistics
    conn = get_connection()
    mastery_rows = conn.execute("SELECT completed_lessons FROM mastery").fetchall()
    conn.close()
    completed_lessons_count = sum(len(json.loads(row["completed_lessons"])) for row in mastery_rows)
    mastery_summary = get_mastery_summary()

    # Cluster health
    cluster = OllamaCluster()
    cluster_status = cluster.get_cluster_status()
    online_count = sum(1 for d in cluster_status.values() if d.get("online"))
    total_nodes = len(cluster_status)

    unwritten_topics = total_topics - masterclass_topics - legacy_stubs

    print("==================================================")
    print("       AI LEARNING WORKSPACE CURRICULUM STATUS    ")
    print("==================================================")
    print(f"  Domains (L1):             {total_domains}")
    print(f"  Disciplines (L2):         {total_disciplines}")
    print(f"  Topics & Courses (L3):    {total_topics}")
    print("--------------------------------------------------")
    print(f"  Masterclass Topics:       {masterclass_topics} / {total_topics} (PostgreSQL Standard)")
    print(f"  Authored Lessons:         {masterclass_lessons} (lesson_01_*.md ...)")
    print(f"  Operational Labs:         {masterclass_labs} (labs.md)")
    print(f"  Legacy Stubs to Purge:    {legacy_stubs} (Pending cluster regeneration)")
    print(f"  Unwritten Topics:         {unwritten_topics}")
    print("--------------------------------------------------")
    print(f"  Mastery Competence:       {mastery_summary['mastered_count']} Mastered | {mastery_summary['counts']['studying']} Studying")
    print(f"  Completed Lessons:        {completed_lessons_count} Verified")
    print("--------------------------------------------------")
    print(f"  Ollama Cluster Status:    {online_count}/{total_nodes} Nodes Online")
    for host, h_data in cluster_status.items():
        clean_host = host.rstrip("/")
        name = get_node_name(clean_host).upper()
        is_online = h_data.get("online", False)
        status_str = "ONLINE " if is_online else "OFFLINE"
        pinned = h_data.get("pinned_model")
        pref_model = pinned or h_data.get("preferred_model") or (h_data.get("models") and h_data["models"][0]) or "none"
        pin_label = " [PINNED]" if pinned and is_online else ""
        print(f"    - [{name:10s}] {status_str} | Model: {pref_model}{pin_label}")
    
    if os.environ.get("ANTHROPIC_API_KEY"):
        print(f"    - [ANTHROPIC] ONLINE    | Tier: cloud    | Model: claude-3-5-sonnet-20241022")

    print("==================================================")

def cmd_tree(args):
    tree = get_topic_tree()
    filter_domain = args.domain.lower() if args.domain else None

    print("\nAI Learning Workspace Curriculum Tree [F=Foundation, L=Lesson, B=Labs]\n")
    for domain, ddata in tree.items():
        if filter_domain and filter_domain not in domain.lower():
            continue

        print(f"▾ {domain.upper()}")
        for cat, cdata in ddata["categories"].items():
            print(f"  ▸ {cat.replace('_', ' ').title()}")
            for sub, sdata in cdata.items():
                badge = format_status_badge(sdata["status"])
                print(f"    {badge} {sdata['display_name']} ({sub})")
        print()

def cmd_add(args):
    print(f"[*] Adding subtopic '{args.subtopic}' to {args.domain} / {args.category}...")
    try:
        path = add_subtopic(args.domain, args.category, args.subtopic, args.title)
        print(f"[✔] Created subtopic directory at: {path}")
        print(f"[✔] Updated SYLLABUS.md in topics/{args.domain}/")

        if args.generate:
            print("[*] Generating learning units (Foundation, Lesson, Labs)...")
            provider = get_provider(provider_type=args.provider, model=args.model, domain=args.domain)
            results = generate_subtopic_content(args.domain, args.category, args.subtopic, path, provider=provider)
            print(f"[✔] Generation results: {results}")

    except Exception as e:
        print(f"[✘] Error adding subtopic: {e}")
        sys.exit(1)

def cmd_generate(args):
    if args.all:
        from scripts.generate_all import batch_generate
        batch_generate(provider_type=args.provider, model=args.model, force=args.force)
        return

    if not args.query:
        print("[✘] Please provide a subtopic query or use --all to generate all topics.")
        sys.exit(1)

    target = resolve_subtopic(args.query)
    if not target:
        print(f"[✘] Could not find any subtopic matching '{args.query}'.")
        print("Run 'learning tree' to see available subtopics.")
        sys.exit(1)

    domain, cat, sub, sub_path = target
    print("==================================================")
    print(f"[*] Target Domain:   {domain}")
    print(f"[*] Category:        {cat}")
    print(f"[*] Subtopic:        {sub}")
    print(f"[*] Directory:       {sub_path}")
    print("==================================================")

    provider = get_provider(provider_type=args.provider, model=args.model, domain=domain)
    print(f"[*] Active LLM Provider: {provider.__class__.__name__} (Model: {getattr(provider, 'model', 'default')})")
    print("[*] Target Curriculum: Masterclass Units (Lessons and Labs)")
    print("[*] Generating Lessons and Labs...")

    results = generate_subtopic_content(domain, cat, sub, sub_path, provider=provider, force=args.force)
    print(f"\n[✔] Learning modules updated at: {sub_path}")

def cmd_chat(args):
    target = resolve_subtopic(args.query)
    if not target:
        print(f"[✘] Could not find subtopic matching '{args.query}'.")
        sys.exit(1)

    domain, cat, sub, sub_path = target
    persona = get_domain_persona(domain)

    # Ingest context files
    context_parts = [f"# Active Subject: {sub.replace('_', ' ').title()} ({domain}/{cat})"]
    for l in get_unit_lessons(sub_path)[:4]:
        p = Path(l["path"])
        if p.exists():
            context_parts.append(f"\n--- {p.name} ---\n" + p.read_text(encoding="utf-8")[:2500])

    labs_file = sub_path / "labs.md"
    if labs_file.exists():
        context_parts.append(f"\n--- labs.md ---\n" + labs_file.read_text(encoding="utf-8")[:2000])

    system_instruction = persona + "\n\n" + "\n".join(context_parts)
    provider = get_provider(provider_type=args.provider, model=args.model, domain=domain)

    print("==================================================")
    print(f"   Socratic Tutor Session: {sub.replace('_', ' ').title()}")
    print(f"   Domain: {domain} | Model: {getattr(provider, 'model', 'default')}")
    print("==================================================")
    print("Type your questions, hypotheses, or code. Type 'exit' to quit.\n")

    history = []
    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ["exit", "quit"]:
                print("[*] Ending session.")
                break

            prompt = "\n".join(history + [f"Student: {user_input}", "Tutor:"])
            response = provider.generate(prompt, system_instruction=system_instruction)
            print(f"\nTutor > {response.strip()}\n")
            history.append(f"Student: {user_input}")
            history.append(f"Tutor: {response.strip()}")
        except (KeyboardInterrupt, EOFError):
            print("\n[*] Exiting tutor session.")
            break

def cmd_search(args):
    results = search_curriculum(args.query, max_results=args.limit)
    print(f"\nSearch results for '{args.query}' ({len(results)} matches):\n")
    for idx, r in enumerate(results, 1):
        print(f"{idx:2d}. {r['path']} ({r['level']}) -> {r['section']}")
        print(f"    {r['snippet']}\n")

def cmd_graph(args):
    graph = get_prerequisite_graph()
    print(f"\nPrerequisite Learning DAG ({graph['node_count']} nodes, {graph['edge_count']} dependency edges):\n")
    for e in graph["edges"]:
        print(f"  {e['source']}  ──►  {e['target']}")
    print()

def cmd_lint(args):
    report = lint_curriculum(domain_filter=args.domain or "")
    print("==================================================")
    print("       CURRICULUM CONTENT QUALITY LINT REPORT     ")
    print("==================================================")
    print(f"  Files Scanned:       {report['scanned_files']}")
    print(f"  Errors:              {report['error_count']}")
    print(f"  Warnings:            {report['warning_count']}")
    print(f"  Status:              {'PASSED (Clean)' if report['passed'] else 'FAILED'}")
    print("==================================================")

    if report["issues"]:
        print("Issues Found:")
        for iss in report["issues"][:15]:
            sev = "[!]" if iss["severity"] == "warning" else "[✘]"
            print(f"  {sev} {iss['file']}: {iss['message']}")
        if len(report["issues"]) > 15:
            print(f"  ... and {len(report['issues']) - 15} more issues.")

    if getattr(args, "render", False):
        import subprocess
        print("\n" + "=" * 50)
        print(" [*] Executing Headless AST & Render Validation...")
        print("=" * 50)
        script_path = WORKSPACE_ROOT / "scripts" / "validate_render.mjs"
        target = f"topics/{args.domain}" if args.domain else "topics"
        subprocess.run(["node", str(script_path), target])

def cmd_export(args):
    out_file = export_handbook(domain=args.domain)
    print(f"[✔] Successfully exported {args.domain} handbook to: {out_file}")

def cmd_flashcards(args):
    out = generate_flashcards(args.query, provider_type=args.provider, model=args.model)
    print(f"[✔] Generated Anki flashcard deck at: {out}")

def cmd_mastery(args):
    if args.set:
        res = set_subtopic_mastery(args.query, args.set)
        print(f"[✔] Updated mastery for '{args.query}' to: {args.set.upper()}")
    else:
        summary = get_mastery_summary()
        print("==================================================")
        print("          USER CURRICULUM MASTERY SUMMARY         ")
        print("==================================================")
        print(f"  Total Tracked:    {summary['total_tracked']}")
        print(f"  Mastered Topics:  {summary['mastered_count']} ({summary['percentage']}%)")
        print("--------------------------------------------------")
        for state, count in summary["counts"].items():
            print(f"  - {state.replace('_', ' ').title():16s}: {count}")
        print("==================================================")

def cmd_review(args):
    if args.query:
        target = resolve_subtopic(args.query)
        if not target:
            print(f"[!] Topic '{args.query}' not found.")
            return
        _, _, _, sub_path = target
        print("==================================================")
        print(f"[*] INDEPENDENT CROSS-MODEL PEER REVIEW: {args.query}")
        print(f"[*] Reviewer Model: {args.model or 'deepseek-r1:32b'}")
        print("==================================================")
        res = review_and_fix_unit(sub_path, reviewer_provider=args.provider, reviewer_model=args.model, auto_fix=args.fix)
        for r in res["reports"]:
            badge = "[✔] VERIFIED" if r.get("verdict") == "VERIFIED" else "[!] " + str(r.get("verdict"))
            print(f"\n{badge} :: {r.get('file')} (Score: {r.get('score', 0)}/100)")
            if r.get("hallucinations"):
                print(f"    - Hallucinations: {r.get('hallucinations')}")
            if r.get("factual_errors"):
                print(f"    - Errors: {r.get('factual_errors')}")
            print(f"    - Critique: {r.get('critique')}")
            if r.get("fixed"):
                print(f"    - [FIXED]: Document rewritten and verified.")
    else:
        print("==================================================")
        print(f"[*] RUNNING CROSS-MODEL PEER AUDIT ACROSS UNITS   ")
        print(f"[*] Reviewer Model: {args.model or 'deepseek-r1:32b'}")
        print("==================================================")
        tree = get_topic_tree()
        verified_count = 0
        total_audited = 0
        for domain, ddata in tree.items():
            for disc, disc_data in ddata["disciplines"].items():
                for course, c_data in disc_data["courses"].items():
                    for unit, u_data in c_data["units"].items():
                        if u_data["status"]["complete"]:
                            total_audited += 1
                            u_path = Path(u_data["full_path"])
                            res = review_and_fix_unit(u_path, reviewer_provider=args.provider, reviewer_model=args.model, auto_fix=args.fix)
                            status_str = "[✔] PASS" if not res["has_issues"] else "[!] ISSUES"
                            print(f"{status_str} :: {u_data['rel_path']}")
                            if not res["has_issues"]:
                                verified_count += 1
        print("==================================================")
        print(f"[*] Peer Review Summary: {verified_count} / {total_audited} Units Verified")
        print("==================================================")

def cmd_serve(args):
    import uvicorn
    host = args.host or "127.0.0.1"
    port = args.port or 8000
    print("==================================================")
    print(f"[*] Starting AI Learning Workbench at http://{host}:{port}")
    print(f"[*] Tree Explorer, Lesson Reader, AI Chat, and PTY Terminal are ready.")
    print("==================================================")
    uvicorn.run("app.backend.main:app", host=host, port=port, reload=args.reload)

def cmd_desktop(args):
    """
    Launches the Synapse Electron native desktop shell wrapper.
    """
    desktop_dir = WORKSPACE_ROOT / "app/desktop"
    if not desktop_dir.exists():
        print(f"[!] Desktop shell directory not found at {desktop_dir}")
        return

    npm_path = shutil.which("npm")
    if not npm_path:
        print("[!] Node.js / npm not found on PATH. Please install Node.js to use the desktop shell.")
        return

    if not (desktop_dir / "node_modules").exists():
        print("[*] Installing desktop shell dependencies (npm install)...")
        subprocess.run([npm_path, "install"], cwd=str(desktop_dir), check=True)

    print("==================================================")
    print("   SYNAPSE NATIVE DESKTOP SHELL WORKBENCH         ")
    print("==================================================")
    print("[*] Launching Electron desktop window wrapper...")
    print("==================================================")

    env = os.environ.copy()
    if args.dev:
        env["ELECTRON_DEV"] = "1"

    subprocess.run([npm_path, "start"], cwd=str(desktop_dir), env=env)

def cmd_clean(args):
    """
    Cleans transient runtime artifacts (chat sessions, export bundles, temp logs)
    without touching authored curriculum files.
    """
    topics_dir = get_topics_dir()
    exports_dir = get_workspace_root() / "exports"

    clean_sessions = args.sessions or args.all
    clean_exports = args.exports or args.all
    clean_db = args.db or args.all

    if not clean_sessions and not clean_exports and not clean_db:
        clean_sessions = True
        clean_exports = True
        clean_db = True

    cleaned_count = 0

    if clean_sessions:
        for s_dir in list(topics_dir.rglob("sessions")) + [topics_dir / ".workspace_sessions"]:
            if s_dir.exists() and s_dir.is_dir():
                shutil.rmtree(s_dir)
                print(f"[*] Cleared session directory: {s_dir.relative_to(WORKSPACE_ROOT)}")
                cleaned_count += 1

    if clean_exports and exports_dir.exists():
        for p in exports_dir.rglob("*"):
            if p.is_file():
                p.unlink()
                print(f"[*] Removed exported artifact: {p.relative_to(WORKSPACE_ROOT)}")
                cleaned_count += 1

    if clean_db:
        try:
            from learning_engine.database import vacuum_db, checkpoint_db
            print("[*] Running SQLite database maintenance (VACUUM & Checkpoint)...")
            checkpoint_db(truncate=True)
            vacuum_db()
            print("[✔] Database optimization complete.")
            cleaned_count += 1
        except Exception as e:
            print(f"[!] Database optimization skipped: {e}")

    print(f"[✔] Cleaned {cleaned_count} transient artifacts/subsystems. Authored curriculum is 100% intact.")

def cmd_pack(args):
    from learning_engine.packages import install_topic_pack, list_installed_packs, uninstall_topic_pack
    from pathlib import Path
    
    if args.pack_cmd == "install":
        print(f"[*] Installing package: {args.source}")
        path = Path(args.source)
        try:
            res = install_topic_pack(path)
            print(f"[+] Successfully installed: {res['domain']}")
        except Exception as e:
            print(f"[-] Installation failed: {e}")
            sys.exit(1)
            
    elif args.pack_cmd == "list":
        packs = list_installed_packs()
        print(f"\n[*] Installed Packages ({len(packs)}):")
        for p in packs:
            print(f"    - {p.get('domain')} ({p.get('title', 'No title')}) - {p.get('lesson_count', 0)} lessons")
            
    elif args.pack_cmd == "uninstall":
        print(f"[*] Uninstalling package: {args.domain}")
        try:
            res = uninstall_topic_pack(args.domain)
            print(f"[+] {res['message']}")
        except Exception as e:
            print(f"[-] Uninstall failed: {e}")
            sys.exit(1)

def main():
    load_env_file()
    parser = argparse.ArgumentParser(
        prog="learning",
        description="AI Learning Workspace Content Engine & Socratic Workbench"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # clean
    p_clean = subparsers.add_parser("clean", help="Clean transient chat sessions and export files")
    p_clean.add_argument("--sessions", action="store_true", help="Remove transient Socratic chat sessions")
    p_clean.add_argument("--exports", action="store_true", help="Remove generated .synpack and handbook exports")
    p_clean.add_argument("--db", action="store_true", help="Vacuum and checkpoint the SQLite database to reclaim space")
    p_clean.add_argument("--all", action="store_true", help="Clean all transient runtime artifacts")
    p_clean.set_defaults(func=cmd_clean)

    # desktop
    p_desktop = subparsers.add_parser("desktop", help="Launch the native Electron desktop shell wrapper")
    p_desktop.add_argument("--dev", action="store_true", help="Connect to local Vite development server")
    p_desktop.set_defaults(func=cmd_desktop)
    
    # pack
    p_pack = subparsers.add_parser("pack", help="Manage .synpack curriculum packages")
    pack_subs = p_pack.add_subparsers(dest="pack_cmd")
    p_pack_inst = pack_subs.add_parser("install", help="Install a .synpack file or from URL")
    p_pack_inst.add_argument("source", help="Path to .synpack file")
    p_pack_list = pack_subs.add_parser("list", help="List installed packages")
    p_pack_uninst = pack_subs.add_parser("uninstall", help="Uninstall a package")
    p_pack_uninst.add_argument("domain", help="Domain to uninstall")
    p_pack.set_defaults(func=cmd_pack)

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch the integrated Web Workbench (UI + Backend + Terminal)")
    p_serve.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on (default: 8000)")
    p_serve.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    p_serve.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload for development")
    p_serve.set_defaults(func=cmd_serve)

    # status
    p_status = subparsers.add_parser("status", help="Show workspace curriculum completion stats")
    p_status.set_defaults(func=cmd_status)

    # tree
    p_tree = subparsers.add_parser("tree", help="Display hierarchical curriculum tree")
    p_tree.add_argument("--domain", "-d", help="Filter by specific domain name")
    p_tree.set_defaults(func=cmd_tree)

    # search
    p_search = subparsers.add_parser("search", help="Full-text search across all generated curriculum units")
    p_search.add_argument("query", help="Search keyword(s)")
    p_search.add_argument("--limit", "-l", type=int, default=10, help="Max results to return")
    p_search.set_defaults(func=cmd_search)

    # graph
    p_graph = subparsers.add_parser("graph", help="Display prerequisite learning dependency DAG")
    p_graph.set_defaults(func=cmd_graph)

    # lint
    p_lint = subparsers.add_parser("lint", help="Lint curriculum files for depth, structure, and placeholders")
    p_lint.add_argument("--domain", "-d", help="Filter by specific domain name")
    p_lint.add_argument("--render", "-r", action="store_true", help="Execute headless AST compilation and render validation (Marked, KaTeX, Mermaid.js)")
    p_lint.set_defaults(func=cmd_lint)

    # export
    p_export = subparsers.add_parser("export", help="Compile a domain into a cohesive printable Markdown handbook")
    p_export.add_argument("domain", help="Domain to export (e.g. computing, formal_sciences)")
    p_export.set_defaults(func=cmd_export)

    # flashcards
    p_fc = subparsers.add_parser("flashcards", help="Generate Anki active-recall flashcard deck (CSV format)")
    p_fc.add_argument("query", help="Subtopic name or path")
    p_fc.add_argument("--provider", "-p", choices=["ollama", "gemini"], help="LLM Provider")
    p_fc.add_argument("--model", "-m", help="Specific model name")
    p_fc.set_defaults(func=cmd_flashcards)

    # mastery
    p_mst = subparsers.add_parser("mastery", help="Track or update user topic mastery state")
    p_mst.add_argument("query", nargs="?", default=None, help="Subtopic path")
    p_mst.add_argument("--set", "-s", choices=["not_started", "studying", "lab_verified", "mastered"], help="Set new mastery state")
    p_mst.set_defaults(func=cmd_mastery)

    # review
    p_rev = subparsers.add_parser("review", help="Independent cross-model quality & hallucination audit")
    p_rev.add_argument("query", nargs="?", default=None, help="Target unit name or path")
    p_rev.add_argument("--model", "-m", default="deepseek-r1:32b", help="Reviewer model (default: deepseek-r1:32b)")
    p_rev.add_argument("--provider", "-p", choices=["ollama", "gemini"], help="Reviewer LLM provider")
    p_rev.add_argument("--fix", "-f", action="store_true", help="Auto-fix detected hallucinations and rewrite units")
    p_rev.set_defaults(func=cmd_review)

    # add
    p_add = subparsers.add_parser("add", help="Add a new subtopic to a domain")
    p_add.add_argument("domain", help="Target domain (e.g. computing)")
    p_add.add_argument("category", help="Target category (e.g. infrastructure)")
    p_add.add_argument("subtopic", help="Subtopic slug (e.g. ebpf)")
    p_add.add_argument("--title", "-t", help="Readable display title")
    p_add.add_argument("--generate", "-g", action="store_true", help="Immediately generate content units")
    p_add.add_argument("--provider", "-p", choices=["ollama", "gemini"], help="LLM Provider")
    p_add.add_argument("--model", "-m", help="Specific model name")
    p_add.set_defaults(func=cmd_add)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate Masterclass Lessons and Labs for a subtopic")
    p_gen.add_argument("query", nargs="?", default=None, help="Subtopic name or path (e.g. 'linux' or 'infrastructure/linux')")
    p_gen.add_argument("--all", "-a", action="store_true", help="Generate all missing units across the entire curriculum")
    p_gen.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
    p_gen.add_argument("--provider", "-p", choices=["ollama", "gemini"], help="LLM Provider")
    p_gen.add_argument("--model", "-m", help="Specific model name (e.g. qwen2.5-coder:32b)")
    p_gen.set_defaults(func=cmd_generate)

    # chat
    p_chat = subparsers.add_parser("chat", help="Start an interactive Socratic terminal session with loaded context")
    p_chat.add_argument("query", help="Subtopic name or path")
    p_chat.add_argument("--provider", "-p", choices=["ollama", "gemini"], help="LLM Provider")
    p_chat.add_argument("--model", "-m", help="Specific model name")
    p_chat.set_defaults(func=cmd_chat)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)

if __name__ == "__main__":
    main()
