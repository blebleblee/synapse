"""
Learning Workspace CLI
Interactive management for curricula, multi-tier lesson generation, search, linting, and export.
"""

import sys
import argparse
from pathlib import Path
from .topic_manager import (
    get_topic_tree,
    list_domains,
    resolve_subtopic,
    add_subtopic,
    get_domain_persona
)
from .models import get_provider, OllamaProvider
from .generator import generate_subtopic_content
from .search import search_curriculum
from .graph import get_prerequisite_graph
from .linter import lint_curriculum
from .exporter import export_handbook
from .daemon import start_daemon, stop_daemon, generate_service_files
from .mastery import get_mastery_summary, set_subtopic_mastery, load_mastery_data
from .flashcards import generate_flashcards

def format_status_badge(status: dict) -> str:
    f = "F" if status["has_foundation"] else "."
    l = "L" if status["has_lesson"] else "."
    b = "B" if status["has_labs"] else "."
    return f"[{f}{l}{b}]"

def cmd_status(args):
    tree = get_topic_tree()
    total_domains = len(tree)
    total_categories = 0
    total_subtopics = 0
    with_foundation = 0
    with_lesson = 0
    with_labs = 0
    complete = 0

    for domain, ddata in tree.items():
        total_categories += len(ddata["categories"])
        for cat, cdata in ddata["categories"].items():
            total_subtopics += len(cdata)
            for sub, sdata in cdata.items():
                st = sdata["status"]
                if st["has_foundation"]: with_foundation += 1
                if st["has_lesson"]: with_lesson += 1
                if st["has_labs"]: with_labs += 1
                if st["complete"]: complete += 1

    ollama_status = "Online" if OllamaProvider.is_available() else "Offline"
    ollama_models = ", ".join(OllamaProvider.list_models()[:3]) if ollama_status == "Online" else "None"

    print("==================================================")
    print("       AI LEARNING WORKSPACE CURRICULUM STATUS    ")
    print("==================================================")
    print(f"  Domains:             {total_domains}")
    print(f"  Categories:          {total_categories}")
    print(f"  Subtopics:           {total_subtopics}")
    print("--------------------------------------------------")
    print(f"  [F] Foundation:      {with_foundation} / {total_subtopics} ({with_foundation*100//(total_subtopics or 1)}%)")
    print(f"  [L] Technical Lesson: {with_lesson} / {total_subtopics} ({with_lesson*100//(total_subtopics or 1)}%)")
    print(f"  [B] Operational Labs: {with_labs} / {total_subtopics} ({with_labs*100//(total_subtopics or 1)}%)")
    print(f"  [FLB] Complete Units: {complete} / {total_subtopics} ({complete*100//(total_subtopics or 1)}%)")
    print("--------------------------------------------------")
    print(f"  Local Ollama Engine: {ollama_status} ({ollama_models})")
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
    print(f"[*] Target Level: {args.level or 'ALL (Beginner, Intermediate, Advanced)'}")
    print("[*] Generating Foundation, Lesson, and Labs...")

    results = generate_subtopic_content(domain, cat, sub, sub_path, provider=provider, force=args.force, level=args.level)
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
    for fname in ["FOUNDATION.md", "LESSON.md", "LABS.md"]:
        fpath = sub_path / fname
        if fpath.exists():
            context_parts.append(f"\n--- {fname} ---\n" + fpath.read_text(encoding="utf-8")[:3000])

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

def cmd_export(args):
    out_file = export_handbook(domain=args.domain, level=args.level)
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

def cmd_stop(args):
    stop_daemon()

def cmd_serve(args):
    if args.daemon:
        start_daemon(host=args.host or "127.0.0.1", port=args.port or 8000)
        return

    if args.service:
        generate_service_files()
        return

    import uvicorn
    host = args.host or "127.0.0.1"
    port = args.port or 8000
    print("==================================================")
    print(f"[*] Starting AI Learning Workbench at http://{host}:{port}")
    print(f"[*] Tree Explorer, Lesson Reader, AI Chat, and PTY Terminal are ready.")
    print("==================================================")
    uvicorn.run("app.backend.main:app", host=host, port=port, reload=args.reload)

def main():
    parser = argparse.ArgumentParser(
        prog="learning",
        description="AI Learning Workspace Content Engine & Socratic Workbench"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # serve
    p_serve = subparsers.add_parser("serve", help="Launch the integrated Web Workbench (UI + Backend + Terminal)")
    p_serve.add_argument("--port", "-p", type=int, default=8000, help="Port to listen on (default: 8000)")
    p_serve.add_argument("--host", default="127.0.0.1", help="Host address (default: 127.0.0.1)")
    p_serve.add_argument("--daemon", "-d", action="store_true", help="Run server as a background daemon process")
    p_serve.add_argument("--service", action="store_true", help="Generate systemd and launchd service files")
    p_serve.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload for development")
    p_serve.set_defaults(func=cmd_serve)

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop running background workbench daemon")
    p_stop.set_defaults(func=cmd_stop)

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
    p_lint.set_defaults(func=cmd_lint)

    # export
    p_export = subparsers.add_parser("export", help="Compile a domain into a cohesive printable Markdown handbook")
    p_export.add_argument("domain", help="Domain to export (e.g. computing, formal_sciences)")
    p_export.add_argument("--level", "-l", choices=["beginner", "intermediate", "advanced"], help="Filter by difficulty level")
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
    p_gen = subparsers.add_parser("generate", help="Generate Foundation, Lesson, and Labs for a subtopic")
    p_gen.add_argument("query", nargs="?", default=None, help="Subtopic name or path (e.g. 'linux' or 'infrastructure/linux')")
    p_gen.add_argument("--level", "-l", choices=["beginner", "intermediate", "advanced"], help="Target specific level")
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
