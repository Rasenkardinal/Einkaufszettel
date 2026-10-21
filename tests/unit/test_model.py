"""Portable tests of the actual model, without importing Home Assistant."""

import importlib.util
import sys
from pathlib import Path
from uuid import UUID

import pytest

MODEL = Path(__file__).parents[2] / "custom_components" / "einkaufszettel" / "model.py"
SPEC = importlib.util.spec_from_file_location("einkaufszettel_model", MODEL)
assert SPEC is not None and SPEC.loader is not None
model = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = model
SPEC.loader.exec_module(model)


def test_copy_retains_duplicate_names_but_generates_local_ids():
    raw = [
        {"uid": "source-1", "summary": "Milch", "status": "needs_action"},
        {"uid": "source-2", "summary": "Milch", "status": "needs_action"},
        {"uid": "source-3", "summary": "Brot", "status": "completed"},
    ]
    items = model.import_items(raw)
    assert [item.summary for item in items] == ["Milch", "Milch"]
    assert [item.source_uid for item in items] == ["source-1", "source-2"]
    assert len({UUID(item.uid) for item in items}) == 2
    assert raw[0]["uid"] == "source-1"


def test_empty_list_is_a_valid_persisted_snapshot():
    assert model.import_items([]) == []
    assert model.load_items({"items": []}) == []


def test_round_trip_preserves_metadata_and_completed_status():
    item = model.ShoppingItem(
        "local-1", "Milch", "completed", "3 Flaschen", "2026-10-20", "alexa-1"
    )
    assert model.load_items({"items": [item.to_dict()]}) == [item]


@pytest.mark.parametrize("status", ["completed", "needs_action"])
def test_check_uncheck_preserves_identity_and_other_entries(status):
    first = model.ShoppingItem("one", "Milch", source_uid="external-1")
    second = model.ShoppingItem("two", "Brot")
    original = [first, second]
    updated = model.update_item(original, "one", "Milch", status, "3 Flaschen", None)
    assert updated[0].status == status
    assert updated[0].source_uid == "external-1"
    assert updated[1] == second
    assert original[0] == first


@pytest.mark.parametrize("raw", [None, {}, "items", [None], [{"summary": "Milk"}]])
def test_malformed_source_is_not_treated_as_empty(raw):
    with pytest.raises(ValueError):
        model.import_items(raw)


@pytest.mark.parametrize(
    "data",
    [
        {},
        None,
        {"items": None},
        {"items": [None]},
        {"items": [{"summary": "Milk", "status": "needs_action"}]},
        {
            "items": [
                {"uid": "same", "summary": "Milk", "status": "needs_action"},
                {"uid": "same", "summary": "Bread", "status": "needs_action"},
            ]
        },
    ],
)
def test_corrupt_storage_is_rejected(data):
    with pytest.raises(ValueError):
        model.load_items(data)


@pytest.mark.parametrize(
    "fields",
    [
        {"summary": " "},
        {"uid": ""},
        {"status": "other"},
        {"description": 3},
        {"due": "tomorrow"},
        {"due": "2026-10-18T12:00:00"},
        {"source_uid": 123},
    ],
)
def test_invalid_item_is_rejected(fields):
    with pytest.raises(ValueError):
        model.ShoppingItem(**({"uid": "one", "summary": "Milch"} | fields))


@pytest.mark.parametrize("due", ["2026-10-20", "2026-10-20T12:00:00+02:00"])
def test_due_date_is_lossless(due):
    assert model.parse_due(due).isoformat() == due


def test_unknown_uid_does_not_change_any_item():
    original = [model.ShoppingItem("one", "Milch")]
    with pytest.raises(ValueError, match="Unknown item UID"):
        model.update_item(original, "missing", "Brot", "completed", None, None)
    assert original == [model.ShoppingItem("one", "Milch")]


def test_merge_uses_source_ids_and_retains_completed_items():
    old = model.ShoppingItem("local", "Meine Milch", "completed", source_uid="a")
    incoming = [
        model.ShoppingItem("copy-a", "Milch", source_uid="a"),
        model.ShoppingItem("copy-b", "Milch", source_uid="b"),
        model.ShoppingItem("copy-b-again", "Milch", source_uid="b"),
    ]
    assert model.append_new_items([old], incoming) == [old, incoming[1]]


def test_merge_refuses_to_guess_identity_without_source_ids():
    with pytest.raises(ValueError, match="Source item IDs"):
        model.append_new_items([], [model.ShoppingItem("local", "Milch")])


def test_merge_empty_source_preserves_existing_items():
    old = model.ShoppingItem("local", "Milch", source_uid="a")
    assert model.append_new_items([old], []) == [old]


def test_merge_allows_locally_created_items_without_source_ids():
    local = model.ShoppingItem("local", "Kaffee")
    imported = model.ShoppingItem("copy", "Milch", source_uid="external-id")
    assert model.append_new_items([local], [imported]) == [local, imported]
