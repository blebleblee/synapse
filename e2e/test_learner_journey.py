"""
End-to-End Browser Journey & Resume Selection Verification Tests.
Exercises:
1. Core learner journey with automatic reload-and-resume (NO manual reselection).
2. Selection and restoration of different specific lessons and 'all lessons' view.
3. Resilient handling of malformed stored data and 404 missing topics.
4. Fallback replacement for stale lesson IDs.
5. Race handling: user selection and logout supersede in-flight restore requests.
6. Unauthorized (401) handling: clears protected reader content and requires login,
   while preserving saved selection in localStorage.
7. Explicit logout clears saved selection and resets active state.
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
    Seeds a minimal fixture curriculum with unique titles for identity verification
    and multi-topic/multi-lesson navigation tests.
    """
    comp_dir = topics_dir / "computing"
    pg_dir = comp_dir / "data" / "postgresql"
    bash_dir = comp_dir / "systems" / "bash"

    pg_dir.mkdir(parents=True, exist_ok=True)
    bash_dir.mkdir(parents=True, exist_ok=True)

    # Unique fixture syllabus title
    (comp_dir / "SYLLABUS.md").write_text(
        "# Computing Syllabus\n\n"
        "- **E2E Unique Storage Invariants** (`data/postgresql/`)\n"
        "- **E2E Shell Invariants** (`systems/bash/`)\n",
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

    (bash_dir / "lesson_01_syntax.md").write_text(
        "# E2E Shell Syntax\n\n"
        "Process substitution and file descriptor redirection.\n",
        encoding="utf-8"
    )

    formal_dir = topics_dir / "formal_sciences" / "logic" / "proofs"
    formal_dir.mkdir(parents=True, exist_ok=True)
    (topics_dir / "formal_sciences" / "SYLLABUS.md").write_text(
        "# Formal Sciences Syllabus\n\n"
        "- **E2E Formal Proofs** (`logic/proofs/`)\n",
        encoding="utf-8"
    )
    (formal_dir / "lesson_01_invariants.md").write_text(
        "# E2E Formal Invariants\n\n"
        "Inductive proofs and invariants across finite state transitions.\n",
        encoding="utf-8"
    )


@pytest.fixture(scope="module")
def e2e_server(tmp_path_factory):
    """
    Spawns an isolated test server instance on 127.0.0.1 on an ephemeral port.
    Verifies unique fixture identity before yielding and terminates safely.
    """
    tmp_path = tmp_path_factory.mktemp("synapse_e2e_server")
    tmp_workspace = tmp_path / "workspace"
    tmp_topics = tmp_workspace / "topics"
    tmp_data = tmp_workspace / "data"
    tmp_data.mkdir(parents=True, exist_ok=True)
    tmp_db = tmp_data / "synapse_e2e.db"

    seed_minimal_e2e_fixture(tmp_topics)

    port = get_free_loopback_port()
    server_url = f"http://127.0.0.1:{port}"

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

    try:
        ready = False
        start_time = time.time()
        timeout_seconds = 15.0

        while time.time() - start_time < timeout_seconds:
            exit_code = server_proc.poll()
            if exit_code is not None:
                log_fp.seek(0)
                output = log_fp.read()
                raise RuntimeError(
                    f"Child server process exited prematurely with code {exit_code}. Log:\n{output}"
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
                f"Server failed readiness verification within {timeout_seconds}s at {server_url}. Log:\n{output}"
            )

        yield server_url

    finally:
        if server_proc.poll() is None:
            server_proc.terminate()
            try:
                server_proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                server_proc.kill()
                server_proc.wait(timeout=2.0)
        log_fp.close()


@pytest.fixture
def browser_page(e2e_server):
    """
    Launches headless Chromium with failure tracing and pre-seeded onboarding.
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context(viewport={"width": 1280, "height": 800})
    context.tracing.start(screenshots=True, snapshots=True, sources=True)

    page = context.new_page()

    # Pre-seed standard onboarding completion
    page.add_init_script("""
        localStorage.setItem('synapse_onboarding_completed', 'true');
        localStorage.setItem('synapse_app_settings', JSON.stringify({
            theme: 'midnight',
            fontSize: 'standard',
            readerWidth: 'full',
            language: 'en'
        }));
    """)

    test_failed = False
    try:
        yield page, e2e_server
    except Exception:
        test_failed = True
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        try:
            page.screenshot(path=str(ARTIFACTS_DIR / "failure_screenshot.png"), full_page=True)
        except Exception:
            pass
        try:
            context.tracing.stop(path=str(ARTIFACTS_DIR / "failure_trace.zip"))
        except Exception:
            pass
        raise
    finally:
        if not test_failed:
            try:
                context.tracing.stop()
            except Exception:
                pass
        context.close()
        browser.close()
        playwright.stop()


def expand_all_topics(page):
    """Expands all domains and categories in the sidebar tree."""
    expand_btn = page.locator("button[title*='Expand'], button[title*='expand']").first
    if expand_btn.is_visible():
        expand_btn.click()


def select_fixture_lesson(page, cat_text="Data", course_text="E2e Unique Storage Invariants", lesson_text="Foundations"):
    """Helper to navigate sidebar tree to a specific course and lesson."""
    domain_hdr = page.locator(".domain-header:has-text('Computing')").first
    expect(domain_hdr).to_be_visible(timeout=10000)

    cat_hdr = page.locator(f".category-header:has-text('{cat_text}')").first
    if not cat_hdr.is_visible():
        domain_hdr.click()

    expect(cat_hdr).to_be_visible(timeout=5000)
    item = page.locator(f".course-header:has-text('{course_text}'), .subtopic-item:has-text('{course_text}')").first
    if not item.is_visible():
        cat_hdr.click()

    expect(item).to_be_visible(timeout=5000)
    item.click()

    lesson_item = page.locator(f".unit-lesson-subitem:has-text('{lesson_text}')").first
    if lesson_item.is_visible():
        lesson_item.click()


def test_learner_core_journey_with_automatic_resume(browser_page):
    """
    Requirement 1: Verify full learner journey and automatic reload-and-resume
    WITHOUT manual reselection.
    """
    page, server_url = browser_page

    # 1. Open app
    page.goto(server_url)
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # 2. Select fixture curriculum and first lesson
    select_fixture_lesson(page, "Data", "E2e Unique Storage Invariants", "Foundations")

    # 3. Assert initially incomplete
    btn_toggle = page.locator(".btn-toggle-complete").first
    expect(btn_toggle).to_be_visible(timeout=5000)
    expect(btn_toggle).to_have_text("Mark Complete")
    expect(btn_toggle).not_to_have_class(re.compile(r"\bcompleted\b"))

    sidebar_badge = page.locator(".course-progress").first
    expect(sidebar_badge).to_have_text("2L")

    # 4. Mark complete
    btn_toggle.click()

    # 5. Assert update
    expect(btn_toggle).to_have_text("Completed ✓", timeout=5000)
    expect(btn_toggle).to_have_class(re.compile(r"\bcompleted\b"))
    expect(sidebar_badge).to_have_text("1/2", timeout=5000)

    # 6. RELOAD and verify AUTOMATIC RESUME without manual reselection!
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # Assert content and lesson control automatically restored
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)
    btn_toggle = page.locator(".btn-toggle-complete").first
    expect(btn_toggle).to_be_visible(timeout=5000)
    expect(btn_toggle).to_have_text("Completed ✓")
    expect(btn_toggle).to_have_class(re.compile(r"\bcompleted\b"))

    # Expand sidebar to verify persisted progress badge
    expand_all_topics(page)
    expect(page.locator(".course-progress:has-text('1/2')").first).to_be_visible(timeout=5000)

    # 7. Mark incomplete
    btn_toggle.click()
    expect(btn_toggle).to_have_text("Mark Complete", timeout=5000)
    expect(btn_toggle).not_to_have_class(re.compile(r"\bcompleted\b"))
    expect(page.locator(".course-progress:has-text('2L')").first).to_be_visible(timeout=5000)

    # 8. RELOAD again and verify incomplete state persisted automatically!
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)
    btn_toggle = page.locator(".btn-toggle-complete").first
    expect(btn_toggle).to_be_visible(timeout=5000)
    expect(btn_toggle).to_have_text("Mark Complete")
    expect(btn_toggle).not_to_have_class(re.compile(r"\bcompleted\b"))

    expand_all_topics(page)
    expect(page.locator(".course-progress:has-text('2L')").first).to_be_visible(timeout=5000)


def test_resume_different_lesson_and_all_lessons_view(browser_page):
    """
    Requirements 2 & 3:
    - Verify selecting a different lesson (Lesson 2) is saved and restored on reload.
    - Verify selecting 'all lessons' is saved and restored on reload.
    """
    page, server_url = browser_page
    page.goto(server_url)
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # Select Lesson 2 ("B-Tree Mechanics")
    select_fixture_lesson(page, "Data", "E2e Unique Storage Invariants", "B-Tree Mechanics")
    expect(page.locator("h1:has-text('E2E B-Tree Mechanics')")).to_be_visible(timeout=5000)

    # Reload without manual reselection
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # Assert Lesson 2 was automatically resumed
    expect(page.locator("h1:has-text('E2E B-Tree Mechanics')")).to_be_visible(timeout=5000)

    # Now select "Complete Guide" via reader "All" button
    all_btn = page.locator("button.lesson-number-btn:has-text('All'), button:has-text('All')").first
    expect(all_btn).to_be_visible(timeout=5000)
    all_btn.click()

    # In all lessons view, dropdown shows 'all' and full guide is visible
    expect(page.locator(".study-lesson-dropdown")).to_have_value("all")

    # Reload without manual reselection
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # Assert Complete Guide view automatically resumed
    expect(page.locator(".study-lesson-dropdown")).to_have_value("all", timeout=5000)


def test_resume_malformed_and_missing_topic_error_handling(browser_page):
    """
    Requirement 4:
    - Verify malformed saved data does not crash startup and shows empty reader.
    - Verify missing topic (404) clears saved selection and shows empty reader.
    """
    page, server_url = browser_page

    # Scenario A: Malformed saved JSON
    page.goto(server_url)
    page.evaluate("localStorage.setItem('synapse_active_selection', '{ broken malformed json')")
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # Reader displays empty placeholder without crashing
    expect(page.locator(".viewer-empty")).to_be_visible(timeout=5000)
    expect(page.locator("h2:has-text('Select a Topic to Begin')")).to_be_visible()

    # Scenario B: Missing topic (404)
    page.evaluate("""
        localStorage.setItem('synapse_active_selection', JSON.stringify({
            path: 'computing/data/nonexistent_course_404',
            lessonId: 'lesson_01'
        }))
    """)
    with page.expect_response(lambda res: "nonexistent_course_404" in res.url and res.status == 404):
        page.reload()

    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)
    expect(page.locator(".viewer-empty")).to_be_visible(timeout=5000)

    # Wait for localStorage to be cleared upon 404 handling
    page.wait_for_function("() => localStorage.getItem('synapse_active_selection') === null", timeout=5000)
    saved = page.evaluate("localStorage.getItem('synapse_active_selection')")
    assert saved is None, f"Expected stale 404 topic selection to be cleared, got: {saved}"


def test_resume_stale_lesson_id_fallback(browser_page):
    """
    Requirement 5:
    - Verify missing lesson falls back to normal topic default and replaces stale saved ID.
    """
    page, server_url = browser_page
    page.goto(server_url)

    # Seed valid topic with deleted / stale lesson ID
    page.evaluate("""
        localStorage.setItem('synapse_active_selection', JSON.stringify({
            path: 'computing/data/postgresql',
            lessonId: 'deleted_lesson_99'
        }))
    """)
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # Reader automatically falls back to Lesson 1: Foundations
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)

    # Verify localStorage now holds the valid fallback lesson ID, not deleted_lesson_99
    saved_raw = page.evaluate("localStorage.getItem('synapse_active_selection')")
    assert saved_raw is not None
    saved = json.loads(saved_raw)
    assert saved["path"] == "computing/data/postgresql"
    assert saved["lessonId"] == "lesson_01_foundations"


def test_late_restore_superseded_by_user_selection(browser_page):
    """
    Requirement 6:
    - Verify late restore response does NOT overwrite a newer explicit user selection.
    """
    page, server_url = browser_page

    page.goto(server_url)
    page.evaluate("""
        localStorage.setItem('synapse_active_selection', JSON.stringify({
            path: 'computing/data/postgresql',
            lessonId: 'lesson_01_foundations'
        }))
    """)

    # Delay /api/topic response for topic A (restore request)
    page.route("**/api/topic?query=computing%2Fdata%2Fpostgresql*", lambda route: (
        time.sleep(1.0),
        route.continue_()
    ))

    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # User immediately selects topic B before delayed restore arrives
    select_fixture_lesson(page, "Systems", "E2e Shell Invariants", "Shell Syntax")
    expect(page.locator("h1:has-text('E2E Shell Syntax')")).to_be_visible(timeout=5000)

    # Wait for in-flight restore response to fulfill
    page.wait_for_timeout(1500)

    # Assert topic B remains displayed and was NOT overwritten by late restore of topic A
    expect(page.locator("h1:has-text('E2E Shell Syntax')")).to_be_visible()


def test_unauthorized_response_clears_content_but_preserves_saved_selection(browser_page):
    """
    Focused regression test for unauthorized (401) handling:
    1. Start with a saved topic and lesson.
    2. Trigger unauthorized handling through an actual application request receiving a controlled 401 response.
    3. Verify protected reader content is cleared and login modal is required.
    4. Verify the saved topic/lesson identifiers remain in localStorage.
    """
    page, server_url = browser_page

    # 1. Start with valid saved selection in storage and open app
    page.goto(server_url)
    page.evaluate("""
        localStorage.setItem('synapse_active_selection', JSON.stringify({
            path: 'computing/data/postgresql',
            lessonId: 'lesson_01_foundations'
        }))
    """)
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)

    # 2. Configure controlled 401 response on application API requests
    page.route("**/api/topic?query=computing%2Fsystems%2Fbash*", lambda route: route.fulfill(
        status=401,
        content_type="application/json",
        body=json.dumps({"detail": "Authentication required"})
    ))

    # Trigger actual application request by selecting a different topic in the sidebar
    # We catch the timeout or pointer interception because the 401 response might arrive
    # instantly upon clicking the course header, popping the modal before the lesson is clicked.
    try:
        select_fixture_lesson(page, "Systems", "E2e Shell Invariants", "Shell Syntax")
    except Exception:
        pass

    # 3. Verify protected reader content is cleared and login is required
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).not_to_be_visible(timeout=5000)
    expect(page.locator("h1:has-text('E2E Shell Syntax')")).not_to_be_visible()
    expect(page.locator(".login-card")).to_be_visible(timeout=5000)

    # 4. Verify saved topic/lesson identifiers REMAIN in localStorage (not cleared by 401)
    saved_raw = page.evaluate("localStorage.getItem('synapse_active_selection')")
    assert saved_raw is not None, "Expected saved selection to be preserved in localStorage upon 401"
    saved = json.loads(saved_raw)
    assert saved["path"] == "computing/data/postgresql"
    assert saved["lessonId"] == "lesson_01_foundations"


def test_explicit_logout_clears_saved_selection(browser_page):
    """
    Verifies that explicit logout clears saved selection and resets active state.
    """
    page, server_url = browser_page
    page.goto(server_url)

    # 1. Seed saved selection and configure auth required + authenticated
    page.evaluate("""
        localStorage.setItem('synapse_active_selection', JSON.stringify({
            path: 'computing/data/postgresql',
            lessonId: 'lesson_01_foundations'
        }));
        localStorage.setItem('synapse_auth_token', 'test_bearer_token');
    """)

    page.route("**/api/auth/status", lambda route: route.fulfill(
        status=200,
        content_type="application/json",
        body=json.dumps({"auth_required": True, "authenticated": True, "token": "test_bearer_token"})
    ))

    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)

    # 2. In authenticated protected mode, the Logout button is visible and active in the sidebar
    logout_btn = page.locator("button[title*='Logout'], button[title*='Lock']").first
    expect(logout_btn).to_be_visible(timeout=5000)

    # 3. Explicitly click Logout
    logout_btn.click()

    # 4. Assert saved selection is cleared from localStorage
    saved = page.evaluate("localStorage.getItem('synapse_active_selection')")
    assert saved is None, f"Expected explicit logout to clear saved selection, but got: {saved}"

    # 5. Assert reader content is cleared and login modal is required
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).not_to_be_visible()
    expect(page.locator(".login-card")).to_be_visible(timeout=5000)


def test_keyboard_navigation_contract(browser_page):
    """
    Verifies the complete keyboard navigation contract:
    - In an individual lesson, [ goes to previous lesson and ] to next.
    - At the first/last lesson, do not wrap.
    - In 'all lessons', ] opens first lesson; [ does nothing.
    - In 'labs', neither shortcut changes the view.
    - Ignore these shortcuts in inputs, textareas, editable content, terminal,
      and when Ctrl, Cmd, Alt, or Shift is held.
    - Keep reload/resume selection persistence working.
    """
    page, server_url = browser_page
    page.goto(server_url)
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # 1. Start in "all lessons" view
    select_fixture_lesson(page, "Data", "E2e Unique Storage Invariants", "Foundations")
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)

    all_btn = page.locator("button.lesson-number-btn:has-text('All'), button:has-text('All')").first
    all_btn.click()
    expect(page.locator(".study-lesson-dropdown")).to_have_value("all", timeout=5000)

    # In "all lessons", [ does nothing
    page.keyboard.press("[")
    page.wait_for_timeout(300)
    expect(page.locator(".study-lesson-dropdown")).to_have_value("all")

    # In "all lessons", ] opens first lesson
    page.keyboard.press("]")
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_01_foundations")

    # 2. At first lesson, [ does NOT wrap to last lesson
    page.keyboard.press("[")
    page.wait_for_timeout(300)
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible()
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_01_foundations")

    # 3. From first lesson, ] advances to next lesson (Lesson 2)
    page.keyboard.press("]")
    expect(page.locator("h1:has-text('E2E B-Tree Mechanics')")).to_be_visible(timeout=5000)
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_02_indexing")

    # 4. At last lesson, ] does NOT wrap to first lesson
    page.keyboard.press("]")
    page.wait_for_timeout(300)
    expect(page.locator("h1:has-text('E2E B-Tree Mechanics')")).to_be_visible()
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_02_indexing")

    # 5. From last lesson, [ navigates back to Lesson 1
    page.keyboard.press("[")
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_01_foundations")

    # 6. Modifiers (Ctrl, Cmd, Alt, Shift) are ignored
    page.keyboard.press("Control+[")
    page.keyboard.press("Meta+[")
    page.keyboard.press("Alt+[")
    page.keyboard.press("Shift+[")
    page.keyboard.press("Control+]")
    page.keyboard.press("Meta+]")
    page.keyboard.press("Alt+]")
    page.keyboard.press("Shift+]")
    page.wait_for_timeout(300)
    # View must remain on Lesson 1
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible()
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_01_foundations")

    # 7. In inputs / typing: shortcuts are ignored
    filter_input = page.locator("input.filter-input").first
    if filter_input.is_visible():
        filter_input.focus()
        page.keyboard.press("]")
        page.keyboard.press("[")
        page.wait_for_timeout(300)
        expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible()
        expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_01_foundations")

    # 8. In "labs", neither shortcut changes the view
    labs_tab = page.locator("button.tab-btn:has-text('Labs'), .tab-item:has-text('Labs')").first
    labs_tab.click()
    page.wait_for_timeout(300)

    page.keyboard.press("[")
    page.keyboard.press("]")
    page.wait_for_timeout(300)
    # Reader should still be on labs tab
    expect(page.locator("button.tab-btn.active:has-text('Labs'), .tab-item.active:has-text('Labs')").first).to_be_visible()

    # 9. Verify reload/resume selection persistence after keyboard navigation
    # Switch back to study tab, advance to Lesson 2 via ]
    study_tab = page.locator("button.tab-btn:has-text('Study'), .tab-item:has-text('Study')").first
    study_tab.click()
    expect(page.locator("h1:has-text('E2E Storage Foundations')")).to_be_visible(timeout=5000)

    page.keyboard.press("]")
    expect(page.locator("h1:has-text('E2E B-Tree Mechanics')")).to_be_visible(timeout=5000)

    # Reload page
    page.reload()
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)
    # Automatically resumes Lesson 2
    expect(page.locator("h1:has-text('E2E B-Tree Mechanics')")).to_be_visible(timeout=5000)
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_02_indexing")


def test_search_navigation_to_matched_lesson(browser_page):
    """
    Verifies that search highlights query keywords, domain filter chips allow
    narrowing multi-domain results, and clicking a result navigates directly
    to the matched lesson instead of falling back to Lesson 1.
    """
    page, server_url = browser_page
    page.goto(server_url)
    expect(page.locator("aside.tree-sidebar")).to_be_visible(timeout=10000)

    # 1. Open search modal via sidebar action button
    search_btn = page.locator("button[title*='Search']").first
    expect(search_btn).to_be_visible(timeout=5000)
    search_btn.click()

    search_input = page.locator(".search-modal-header input")
    expect(search_input).to_be_visible(timeout=5000)

    # 2. Search multi-domain query "invariants" (matches Computing and Formal Sciences)
    search_input.fill("invariants")

    # Domain filter chips should appear for multi-domain results
    expect(page.locator(".search-filter-chip:has-text('Computing')")).to_be_visible(timeout=5000)
    expect(page.locator(".search-filter-chip:has-text('Formal Sciences')")).to_be_visible(timeout=5000)

    # Filter to Formal Sciences only
    page.locator(".search-filter-chip:has-text('Formal Sciences')").click()
    expect(page.locator(".search-result-item:has-text('Formal Invariants')")).to_be_visible(timeout=5000)
    expect(page.locator(".search-result-item:has-text('Storage Foundations')")).not_to_be_visible()

    # Reset filter back to All
    page.locator(".search-filter-chip:has-text('All')").click()
    expect(page.locator(".search-result-item:has-text('Storage Foundations')")).to_be_visible(timeout=5000)
    expect(page.locator(".search-result-item:has-text('Formal Invariants')")).to_be_visible()

    # 3. Type query matching Lesson 2 ("B-Tree Mechanics")
    search_input.fill("B-Tree")

    # Expect matching result item to appear with highlighted search terms
    result_item = page.locator(".search-result-item:has-text('B-Tree Mechanics')").first
    expect(result_item).to_be_visible(timeout=5000)
    expect(result_item.locator(".search-highlight:has-text('B-Tree')").first).to_be_visible()

    # Click the search result item
    result_item.click()

    # Verify modal is closed
    expect(page.locator(".search-modal-header input")).not_to_be_visible(timeout=5000)

    # Verify reader opens Lesson 2 directly (not Lesson 1)
    expect(page.locator("h1:has-text('E2E B-Tree Mechanics')")).to_be_visible(timeout=5000)
    expect(page.locator(".study-lesson-dropdown")).to_have_value("lesson_02_indexing")


