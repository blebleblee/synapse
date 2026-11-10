"""
Learning Workspace CLI
Interactive management for curricula, multi-tier lesson generation, and tutor sessions.
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
            provider = get_provider(provider_type=args.provider, model=args.model)
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

    provider = get_provider(provider_type=args.provider, model=args.model)
    print(f"[*] Active LLM Provider: {provider.__class__.__name__} (Model: {getattr(provider, 'model', 'default')})")
    print("[*] Generating Foundation, Lesson, and Labs...")

    results = generate_subtopic_content(domain, cat, sub, sub_path, provider=provider, force=args.force)

    for item, generated in results.items():
        status = "Created" if generated else "Already Exists (skipped)"
        print(f"  - {item.upper()}.md: {status}")

    print(f"\n[✔] Learning module ready at: {sub_path}")

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
    provider = get_provider(provider_type=args.provider, model=args.model)

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

def cmd_serve(args):
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
    p_serve.add_argument("--reload", "-r", action="store_true", help="Enable auto-reload for development")
    p_serve.set_defaults(func=cmd_serve)

    # status
    p_status = subparsers.add_parser("status", help="Show workspace curriculum completion stats")
    p_status.set_defaults(func=cmd_status)

    # tree
    p_tree = subparsers.add_parser("tree", help="Display hierarchical curriculum tree")
    p_tree.add_argument("--domain", "-d", help="Filter by specific domain name")
    p_tree.set_defaults(func=cmd_tree)

    # add
    p_add = subparsers.add_parser("add", help="Add a new subtopic to a domain")
    p_add.add_argument("domain", help="Target domain (e.g. computing_and_engineering)")
    p_add.add_argument("category", help="Target category (e.g. infrastructure_and_ops)")
    p_add.add_argument("subtopic", help="Subtopic slug (e.g. ebpf)")
    p_add.add_argument("--title", "-t", help="Readable display title")
    p_add.add_argument("--generate", "-g", action="store_true", help="Immediately generate content units")
    p_add.add_argument("--provider", "-p", choices=["ollama", "gemini"], help="LLM Provider")
    p_add.add_argument("--model", "-m", help="Specific model name")
    p_add.set_defaults(func=cmd_add)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate Foundation, Lesson, and Labs for a subtopic")
    p_gen.add_argument("query", nargs="?", default=None, help="Subtopic name or path (e.g. 'linux' or 'infrastructure_and_ops/linux')")
    p_gen.add_argument("--all", "-a", action="store_true", help="Generate all missing units across the entire curriculum")
    p_gen.add_argument("--force", "-f", action="store_true", help="Overwrite existing files")
    p_gen.add_argument("--provider", "-p", choices=["ollama", "gemini"], help="LLM Provider")
    p_gen.add_argument("--model", "-m", help="Specific model name (e.g. qwen3:4b, llama3.1:8b)")
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
