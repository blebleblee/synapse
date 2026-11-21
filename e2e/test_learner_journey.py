"""
End-to-End Browser Journey Test for Synapse Learner Progression.
Exercises:
1. Open isolated application in Chromium.
2. Select fixture curriculum and its first lesson.
3. Assert initially incomplete.
4. Mark complete.
5. Assert lesson control and sidebar progress update.
6. Reload, reselect topic/lesson, and verify completion persisted.
7. Mark incomplete and verify control and sidebar progress revert.
8. Reload and reopen again to verify incomplete state persisted.
"""

import sys
import os
import re
import time
import json
import socket
import urllib.request
import subprocess
from pathlib import Path
import pytest
from playwright.sync_api import sync_playwright, expect

REPO_ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS_DIR = REPO_ROOT / "e2e" / "artifacts"


def get_free_loopback_port() -> int:
    """Finds an ephemeral free port on 127.0.0.1."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def seed_minimal_e2e_fixture(topics_dir: Path):
    """
    Seeds a minimal fixture curriculum with a unique title to verify server identity.
    """
    comp_dir = topics_dir / "computing"
    pg_dir = comp_dir / "data" / "postgresql"
    pg_dir.mkdir(parents=True, exist_ok=True)

    # Unique fixture syllabus title
    (comp_dir / "SYLLABUS.md").write_text(
        "# Computing Syllabus\n\n"
        "- **E2E Unique Storage Invariants** (`data/postgresql/`)\n",
        encoding="utf-8"
    )

    (pg_dir / "lesson_01_foundations.md").write_text(
        "# E2E Storage Foundations\n\n"
        "Core invariants of page layout and write-ahead logging.\n",
        encoding="utf-8"
    )

    (pg_dir / "lesson_02_indexing.md").write_text(
        "# E2E B-Tree Mechanics\n\n"
        "B-Tree index structure and leaf page traversal.\n",
        encoding="utf-8"
    )


def test_learner_core_journey(tmp_path):
    """
    Executes the full automated browser journey against a dedicated child server
    using Playwright Chromium with observable UI assertions.
    """
    # 1. Setup isolated directories
    tmp_workspace = tmp_path / "workspace"
    tmp_topics = tmp_workspace / "topics"
    tmp_data = tmp_workspace / "data"
    tmp_data.mkdir(parents=True, exist_ok=True)
    tmp_db = tmp_data / "synapse_e2e.db"

    seed_minimal_e2e_fixture(tmp_topics)

    # 2. Allocate dedicated port
    port = get_free_loopback_port()
    server_url = f"http://127.0.0.1:{port}"

    # 3. Environment configuration: curated, minimal, no leaked cloud keys or passwords
    child_env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONPATH": str(REPO_ROOT),
        "SYNAPSE_WORKSPACE": str(tmp_workspace),
        "SYNAPSE_TOPICS_DIR": str(tmp_topics),
        "SYNAPSE_DB_PATH": str(tmp_db),
        "OLLAMA_HOSTS": "http://127.0.0.1:0",
    }
    if "VIRTUAL_ENV" in os.environ:
        child_env["VIRTUAL_ENV"] = os.environ["VIRTUAL_ENV"]

    # 4. Spawn isolated child server
    launcher_script = REPO_ROOT / "e2e" / "server_launcher.py"
    server_log_file = tmp_path / "server_e2e.log"
    log_fp = open(server_log_file, "w+", encoding="utf-8")

    server_proc = subprocess.Popen(
        [sys.executable, str(launcher_script), str(port)],
        cwd=str(REPO_ROOT),
        env=child_env,
        stdout=log_fp,
        stderr=subprocess.STDOUT
    )

    playwright = None
    browser = None
    context = None
    page = None
    test_failed = False

    try:
        # 5. Wait for readiness with bounded timeout and verify unique fixture identity
        ready = False
        start_time = time.time()
        timeout_seconds = 15.0

        while time.time() - start_time < timeout_seconds:
            exit_code = server_proc.poll()
            if exit_code is not None:
                log_fp.seek(0)
                output = log_fp.read()
                raise RuntimeError(
                    f"Child server process exited prematurely with code {exit_code}. Server log:\n{output}"
                )

            try:
                req = urllib.request.Request(f"{server_url}/api/tree")
                with urllib.request.urlopen(req, timeout=1.0) as resp:
                    if resp.status == 200:
                        tree_data = json.loads(resp.read().decode("utf-8"))
                        comp = tree_data.get("computing", {})
                        disc = comp.get("disciplines", {}).get("data", {})
                        course = disc.get("courses", {}).get("postgresql", {})
                        if course.get("display_name") == "E2E Unique Storage Invariants":
                            ready = True
                            break
            except Exception:
                pass
            time.sleep(0.2)

        if not ready:
            log_fp.seek(0)
            output = log_fp.read()
            raise TimeoutError(
                f"Server failed readiness verification within {timeout_seconds}s at {server_url}. Server log:\n{output}"
            )

        # 6. Launch browser and trace context
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800}
        )
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

        page = context.new_page()

        # Pre-seed localStorage to bypass onboarding wizard without mutating code
        page.add_init_script("""
            localStorage.setItem('synapse_onboarding_completed', 'true');
            localStorage.setItem('synapse_app_settings', JSON.stringify({
                theme: 'midnight',
                fontSize: 'standard',
                readerWidth: 'full',
                language: 'en'
            }));
        """)

        # Helper to navigate through sidebar to first lesson
        def select_fixture_lesson():
            # Expand domain if not already open
            domain_hdr = page.locator(".domain-header:has-text('Computing')").first
            expect(domain_hdr).to_be_visible(timeout=10000)
            cat_hdr = page.locator(".category-header:has-text('Data')").first
            if not cat_hdr.is_visible():
                domain_hdr.click()

            # Expand category if not already open
            expect(cat_hdr).to_be_visible(timeout=5000)
            course_hdr = page.locator(".course-header:has-text('E2e Unique Storage Invariants')").first
            if not course_hdr.is_visible():
                cat_hdr.click()

            # Expand course / unit if not already open
            expect(course_hdr).to_be_visible(timeout=5000)
            lesson_item = page.locator(".unit-lesson-subitem:has-text('Foundations')").first
            if not lesson_item.is_visible():
                course_hdr.click()

            expect(lesson_item).to_be_visible(timeout=5000)
            lesson_item.click()

        # Step 1: Open the isolated app
        page.goto(server_url)
        expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

        # Step 2: Select the fixture curriculum and first lesson
        select_fixture_lesson()

        # Step 3: Assert initially incomplete
        btn_toggle = page.locator(".btn-toggle-complete").first
        expect(btn_toggle).to_be_visible(timeout=5000)
        expect(btn_toggle).to_have_text("Mark Complete")
        expect(btn_toggle).not_to_have_class(re.compile(r"\bcompleted\b"))

        sidebar_badge = page.locator(".course-progress").first
        expect(sidebar_badge).to_be_visible()
        expect(sidebar_badge).to_have_text("2L")

        # Step 4: Mark complete
        btn_toggle.click()

        # Step 5: Assert lesson control and visible sidebar progress update
        expect(btn_toggle).to_have_text("Completed ✓", timeout=5000)
        expect(btn_toggle).to_have_class(re.compile(r"\bcompleted\b"))

        expect(sidebar_badge).to_have_text("1/2", timeout=5000)

        # Step 6: Reload, reselect topic/lesson, and verify completion persisted
        page.reload()
        expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

        select_fixture_lesson()

        btn_toggle = page.locator(".btn-toggle-complete").first
        expect(btn_toggle).to_be_visible(timeout=5000)
        expect(btn_toggle).to_have_text("Completed ✓")
        expect(btn_toggle).to_have_class(re.compile(r"\bcompleted\b"))

        sidebar_badge = page.locator(".course-progress").first
        expect(sidebar_badge).to_have_text("1/2")

        # Step 7: Mark incomplete and verify control and sidebar progress revert
        btn_toggle.click()

        expect(btn_toggle).to_have_text("Mark Complete", timeout=5000)
        expect(btn_toggle).not_to_have_class(re.compile(r"\bcompleted\b"))

        expect(sidebar_badge).to_have_text("2L", timeout=5000)

        # Step 8: Reload and reopen again to verify incomplete state persisted
        page.reload()
        expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

        select_fixture_lesson()

        btn_toggle = page.locator(".btn-toggle-complete").first
        expect(btn_toggle).to_be_visible(timeout=5000)
        expect(btn_toggle).to_have_text("Mark Complete")
        expect(btn_toggle).not_to_have_class(re.compile(r"\bcompleted\b"))

        sidebar_badge = page.locator(".course-progress").first
        expect(sidebar_badge).to_have_text("2L")

    except Exception:
        test_failed = True
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        if page:
            try:
                page.screenshot(path=str(ARTIFACTS_DIR / "failure_screenshot.png"), full_page=True)
            except Exception:
                pass
        if context:
            try:
                context.tracing.stop(path=str(ARTIFACTS_DIR / "failure_trace.zip"))
            except Exception:
                pass
        try:
            log_fp.seek(0)
            (ARTIFACTS_DIR / "server_output.log").write_text(log_fp.read(), encoding="utf-8")
        except Exception:
            pass
        raise
    finally:
        # Teardown browser
        if context and not test_failed:
            try:
                context.tracing.stop()
            except Exception:
                pass
        if browser:
            try:
                browser.close()
            except Exception:
                pass
        if playwright:
            try:
                playwright.stop()
            except Exception:
                pass

        # Teardown server: terminate only the child process owned by this test
        if server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait(timeout=2.0)
        log_fp.close()
