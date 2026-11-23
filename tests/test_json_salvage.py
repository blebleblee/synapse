from learning_engine.json_salvage import json_object_list


def test_valid_array_with_chatter_and_fences():
    assert json_object_list('Here:\n```json\n[{"a": 1}, {"a": 2}]\n```') == [{"a": 1}, {"a": 2}]


def test_object_holding_the_list():
    assert json_object_list('{"cards": [{"a": 1}]}', list_keys=("flashcards", "cards")) == [{"a": 1}]
    assert json_object_list('{"other": 1}', list_keys=("cards",)) == []


def test_broken_item_is_dropped_others_kept():
    raw = '[{"a": "ok ${x}"}, {"a": "bad "quote""}, {"a": "fine", "n": {"x": 1}}]'
    assert json_object_list(raw) == [{"a": "ok ${x}"}, {"a": "fine", "n": {"x": 1}}]


def test_no_json_at_all():
    assert json_object_list("Sorry, I cannot help with that.") == []
    assert json_object_list("") == []
