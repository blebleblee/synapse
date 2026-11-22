#!/usr/bin/env python3
"""
Synapse Workbench First-Run Health Check Diagnostic.
Verifies runtime environment, database schema, built assets, curriculum
domains, and local AI cluster connectivity.

Usage:
    python3 scripts/health_check.py [--json] [--quiet]
"""

import sys
import os
import json
import sqlite3
import argparse
from pathlib import Path

# Ensure project root is in sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from learning_engine.security import WORKSPACE_ROOT, TOPICS_DIR
from learning_engine.packages import CORE_DOMAINS
from learning_engine.database import get_db_connection, DB_PATH


def check_python_environment() -> dict:
    version = sys.version_info
    valid_version = version >= (3, 10)
    
    missing_deps = []
    required_modules = ["fastapi", "uvicorn", "pydantic", "jinja2", "sqlite3"]
    for mod in required_modules:
        try:
            __import__(mod)
        except ImportError:
            missing_deps.append(mod)

    return {
        "ok": valid_version and len(missing_deps) == 0,
        "version": f"{version.major}.{version.minor}.{version.micro}",
        "valid_version": valid_version,
        "missing_dependencies": missing_deps,
    }


def check_database() -> dict:
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check;")
            integrity = cursor.fetchone()[0]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row[0] for row in cursor.fetchall()}
            
            has_mastery = "mastery" in tables
            has_settings = "settings" in tables
            
            ok = (integrity == "ok") and has_mastery and has_settings
            return {
                "ok": ok,
                "db_path": str(DB_PATH),
                "integrity": integrity,
                "tables": sorted(list(tables)),
                "has_mastery": has_mastery,
                "has_settings": has_settings,
            }
    except Exception as e:
        return {
            "ok": False,
            "db_path": str(DB_PATH),
            "error": str(e),
        }


def check_frontend_assets() -> dict:
    dist_dir = REPO_ROOT / "app" / "frontend" / "dist"
    index_html = dist_dir / "index.html"
    assets_dir = dist_dir / "assets"
    
    has_dist = dist_dir.is_dir()
    has_index = index_html.is_file()
    has_assets = assets_dir.is_dir() and len(list(assets_dir.glob("*.js"))) > 0

    fonts_dir = REPO_ROOT / "app" / "frontend" / "public" / "fonts"
    has_powerline = (fonts_dir / "PowerlineSymbols.otf").is_file()
    has_nerd_font = (fonts_dir / "SymbolsNerdFontMono-Regular.ttf").is_file()

    ok = has_dist and has_index and has_assets and has_powerline and has_nerd_font
    return {
        "ok": ok,
        "built_bundle_present": has_dist and has_index and has_assets,
        "fonts_present": has_powerline and has_nerd_font,
        "dist_path": str(dist_dir),
        "index_html": has_index,
        "powerline_font": has_powerline,
        "nerd_font": has_nerd_font,
    }


def check_curriculum() -> dict:
    has_topics_dir = TOPICS_DIR.is_dir()
    present_domains = []
    missing_domains = []

    if has_topics_dir:
        for domain in CORE_DOMAINS:
            domain_path = TOPICS_DIR / domain
            if domain_path.is_dir() and (domain_path / "SYLLABUS.md").is_file():
                present_domains.append(domain)
            else:
                missing_domains.append(domain)

    ok = has_topics_dir and len(present_domains) > 0
    return {
        "ok": ok,
        "topics_dir": str(TOPICS_DIR),
        "core_domains_present": present_domains,
        "core_domains_missing": missing_domains,
        "total_present": len(present_domains),
    }


def check_local_ai() -> dict:
    try:
        from learning_engine.models import OllamaCluster
        cluster = OllamaCluster()
        status = cluster.get_cluster_status()
        
        online_nodes = [url for url, node in status.items() if node.get("online")]
        all_models = set()
        for node in status.values():
            all_models.update(node.get("models", []))

        return {
            "ok": True,
            "cluster_nodes": list(status.keys()),
            "online_nodes": online_nodes,
            "models_available": sorted(list(all_models)),
            "is_online": len(online_nodes) > 0,
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "is_online": False,
            "models_available": [],
        }


def run_all_checks() -> dict:
    python_report = check_python_environment()
    db_report = check_database()
    assets_report = check_frontend_assets()
    curriculum_report = check_curriculum()
    ai_report = check_local_ai()

    # Core fatal failures: python, db, or built frontend
    fatal_failure = not (python_report["ok"] and db_report["ok"] and assets_report["ok"])
    
    return {
        "status": "fail" if fatal_failure else "pass",
        "python": python_report,
        "database": db_report,
        "frontend": assets_report,
        "curriculum": curriculum_report,
        "local_ai": ai_report,
    }


def main():
    parser = argparse.ArgumentParser(description="Synapse Workbench First-Run Health Diagnostic")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress non-error output")
    args = parser.parse_args()

    report = run_all_checks()

    if args.json:
        print(json.dumps(report, indent=2))
        sys.exit(0 if report["status"] == "pass" else 1)

    if not args.quiet:
        print("==================================================")
        print(" 🔍 SYNAPSE WORKBENCH ENVIRONMENT HEALTH CHECK   ")
        print("==================================================")
        print("")

        # 1. Python
        p = report["python"]
        if p["ok"]:
            print(f" [✔] Python Runtime: {p['version']} (compatible >= 3.10)")
        else:
            print(f" [✘] Python Runtime: {p['version']} (missing dependencies: {p['missing_dependencies']})")

        # 2. Database
        d = report["database"]
        if d["ok"]:
            print(f" [✔] Database: {d['db_path']} (schema valid, tables: {', '.join(d['tables'])})")
        else:
            print(f" [✘] Database: integrity check failed ({d.get('error', 'missing tables')})")

        # 3. Frontend & Fonts
        f = report["frontend"]
        if f["ok"]:
            print(f" [✔] Frontend Production Bundle & Fonts (assets verified)")
        else:
            missing = []
            if not f["built_bundle_present"]:
                missing.append("built dist/ bundle")
            if not f["fonts_present"]:
                missing.append("bundled fonts")
            print(f" [✘] Frontend Assets: missing {', '.join(missing)} (run 'npm run build' in app/frontend)")

        # 4. Curriculum
        c = report["curriculum"]
        if c["ok"]:
            print(f" [✔] Curriculum Data: {c['total_present']} core domains available")
        else:
            print(f" [!] Curriculum Data: no core domains found in {c['topics_dir']}")

        # 5. Local AI Cluster
        a = report["local_ai"]
        if a.get("is_online"):
            models_str = ", ".join(a["models_available"][:3])
            if len(a["models_available"]) > 3:
                models_str += f" (+{len(a['models_available']) - 3} more)"
            print(f" [✔] Local AI Engine: Online ({len(a['online_nodes'])} node(s), models: {models_str or 'none'})")
        else:
            print(f" [!] Local AI Engine: Offline (no cluster nodes reachable; start Ollama or configure cloud API)")

        print("")
        if report["status"] == "pass":
            print("==================================================")
            print(" [✔] ALL CORE HEALTH CHECKS PASSED                ")
            print("==================================================")
        else:
            print("==================================================")
            print(" [✘] HEALTH CHECK REPORTED PREREQUISITE FAILURES  ")
            print("==================================================")

    sys.exit(0 if report["status"] == "pass" else 1)


if __name__ == "__main__":
    main()
