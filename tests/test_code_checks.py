"""Free static checks of Python code blocks in lessons (no model calls).
A focused review sample (2026-11-23) found ~20% of real errors were code that
fails as written: missing imports, broken or truncated snippets, and other
languages tagged as Python."""
from learning_engine.code_checks import check_python_blocks


def codes(text):
    return [code for code, _ in check_python_blocks(text)]


def test_missing_import_of_a_well_known_name_is_reported():
    text = "```python\nx = np.zeros(3)\n```\n"
    assert codes(text) == ["MISSING_IMPORT"]
    assert "np" in check_python_blocks(text)[0][1] and "numpy" in check_python_blocks(text)[0][1]


def test_import_in_an_earlier_block_of_the_same_lesson_counts():
    text = "```python\nimport numpy as np\n```\nText.\n```python\ny = np.ones(2)\n```\n"
    assert codes(text) == []


def test_from_imports_aliases_and_local_definitions_count():
    text = ("```python\nfrom typing import Optional\nfrom pathlib import Path as P\n"
            "def f(np): return np\nos = None\nprint(Optional, P, os)\n```\n")
    assert codes(text) == []


def test_unknown_names_are_not_guessed():
    # Probably defined in prose or elsewhere: only well-known module names are checked.
    assert codes("```python\nresult = my_helper(model)\n```\n") == []


def test_syntax_errors_and_mislabelled_languages_are_reported():
    assert codes("```python\nSELECT * FROM t;\n```\n") == ["PYTHON_SYNTAX_ERROR"]
    assert codes("```python\nx = 'cut off\n```\n") == ["PYTHON_SYNTAX_ERROR"]


def test_interactive_sessions_and_other_languages_are_skipped():
    assert codes("```python\n>>> 1 +\n```\n") == []
    assert codes("```sql\nSELECT * FROM t;\n```\n```bash\nls -la\n```\n") == []


def test_messages_name_the_line():
    (code, msg), = check_python_blocks("```python\nok = 1\nbroken = (\n```\n")
    assert code == "PYTHON_SYNTAX_ERROR" and "line 2" in msg
