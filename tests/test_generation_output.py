"""validate_generation_output() cleans model replies; it must not eat content.

A mentor reply that opened with a scenario and then a bash block lost
everything before the first "# comment" inside the code (taken for a
heading), and a reply ending in a code block lost its closing fence."""
from learning_engine.models import validate_generation_output


def test_comment_inside_code_is_not_a_heading():
    reply = "Here is a scenario.\n\n```bash\n# Read the log\ngrep ERROR app.log\n```\n\nWhat is wrong?"
    assert validate_generation_output(reply) == reply


def test_closing_fence_of_a_final_code_block_is_kept():
    reply = "Use process substitution:\n\n```bash\nwhile read l; do :; done < <(cat f)\n```"
    assert validate_generation_output(reply) == reply


def test_preamble_before_lesson_heading_is_still_dropped():
    out = validate_generation_output("Sure! Here is the lesson:\n\n# Lesson 1: Intro\n\nBody.")
    assert out.startswith("# Lesson 1: Intro")


def test_whole_reply_in_a_markdown_fence_is_unwrapped():
    out = validate_generation_output("```markdown\n# Lesson 1\n\nBody.\n```")
    assert out == "# Lesson 1\n\nBody."


def test_mermaid_labels_with_brackets_or_inner_quotes_are_quoted():
    """Models write phonetic brackets and quoted examples into flowchart labels
    (`H{Contains [r]?}`, `D["I am"<br/>"She is"]`, `-->|\\"x\\"|`). Mermaid rejects
    them and the reader shows a broken diagram."""
    from learning_engine.models import repair_mermaid_diagrams
    src = ("```mermaid\ngraph TD\n"
           "    F --> H{Contains [r] or [r̩]?}\n"
           '    C --> D["I am a teacher"<br/>"She is Czech"]\n'
           '    B -->|\\"No Clear Suffix\\"| F{"Check Pattern"}\n'
           '    B -->|"-ít" or "-ět"| E["I-Group"]\n'
           "    A((circle)) --> Z[(db)]\n"
           "```")
    out = repair_mermaid_diagrams(src)
    assert 'H{"Contains [r] or [r̩]?"}' in out
    assert 'D["#quot;I am a teacher#quot;<br/>#quot;She is Czech#quot;"]' in out
    assert '-->|"No Clear Suffix"| F{"Check Pattern"}' in out
    assert '-->|"#quot;-ít#quot; or #quot;-ět#quot;"| E["I-Group"]' in out
    assert "A((circle)) --> Z[(db)]" in out
    fixed = repair_mermaid_diagrams('```mermaid\ngraph TD\n    D --> I["zu dem → zum → [tsm̩"]]\n    S[["Subroutine"]]\n```')
    assert 'I["zu dem → zum → [tsm̩]"]' in fixed and 'S[["Subroutine"]]' in fixed
    assert repair_mermaid_diagrams(out) == out


def test_mermaid_repair_leaves_class_diagrams_alone():
    from learning_engine.models import repair_mermaid_diagrams
    src = "```mermaid\nclassDiagram\n    Repo : +find(List[int] ids)\n```"
    assert repair_mermaid_diagrams(src) == src
