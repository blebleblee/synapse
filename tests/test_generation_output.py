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
