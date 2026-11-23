"""Read a list of JSON objects from a model reply.

Local models often break one item (for example unescaped quotes inside a
shell command), which makes the whole array invalid. Losing every quiz
question or flashcard for one bad item is worse than dropping that item.
"""
import json
from typing import Any, Dict, List


def json_object_list(raw: str, list_keys: tuple = ()) -> List[Dict[str, Any]]:
    """Objects from a JSON array in `raw` (code fences and chatter around it
    are ignored). A JSON object holding the list under one of `list_keys` is
    accepted too. If the array is invalid, each top-level object is parsed on
    its own and the broken ones are dropped."""
    text = (raw or "").strip()
    try:
        whole = json.loads(_strip_fences(text))
        if isinstance(whole, dict):
            whole = next((whole[k] for k in list_keys if isinstance(whole.get(k), list)), [])
        if isinstance(whole, list):
            return [item for item in whole if isinstance(item, dict)]
    except ValueError:
        pass

    start, end = text.find("["), text.rfind("]")
    if start == -1 or end <= start:
        start, end = 0, len(text) - 1
    try:
        data = json.loads(text[start:end + 1])
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
    except ValueError:
        pass

    items: List[Dict[str, Any]] = []
    depth, obj_start = 0, None
    for i in range(start, end + 1):
        ch = text[i]
        if ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}" and depth:
            depth -= 1
            if depth == 0 and obj_start is not None:
                try:
                    obj = json.loads(text[obj_start:i + 1])
                except ValueError:
                    continue
                if isinstance(obj, dict):
                    items.append(obj)
    return items


def _strip_fences(text: str) -> str:
    if text.startswith("```"):
        body = text.split("```")[1]
        return body[4:].strip() if body.startswith("json") else body.strip()
    return text
