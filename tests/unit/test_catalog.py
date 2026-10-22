"""Portable tests for the shared category store and market order."""

import importlib.util
from copy import deepcopy
from pathlib import Path

import pytest

PATH = Path(__file__).parents[2] / "custom_components" / "einkaufszettel" / "catalog.py"
SPEC = importlib.util.spec_from_file_location("einkaufszettel_catalog", PATH)
assert SPEC is not None and SPEC.loader is not None
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


def sample():
    return {
        "categories": [
            {"id": "fruit", "name": "Obst"},
            {"id": "bread", "name": "Brot"},
        ],
        "supermarkets": [
            {"id": "shop", "name": "Markt", "category_ids": ["fruit", "bread"]}
        ],
    }


@pytest.mark.parametrize(
    "usage",
    [
        None,
        [],
        {"a": {"added": True, "last_added": 0, "weeks": {}}},
        {"a": {"added": -1, "last_added": 0, "weeks": {}}},
        {"a": {"added": 1, "last_added": float("nan"), "weeks": {}}},
        {"a": {"added": 1, "last_added": 0, "weeks": {"bad": 1}}},
        {"a": {"added": 1, "last_added": 0, "weeks": {"2026-W43": -1}}},
    ],
)
def test_invalid_product_usage_is_rejected(usage):
    data = sample()
    data["products"] = [
        {"key": "milch", "name": "Milch", "category_id": None, "usage": usage}
    ]
    with pytest.raises(ValueError):
        catalog.validate_catalog(data)


def test_weekly_product_usage_survives_category_assignment_removal():
    data = sample()
    usage = {"a": {"added": 2, "last_added": 1000, "weeks": {"2026-W43": 2}}}
    data["products"] = [
        {"key": "milch", "name": "Milch", "category_id": "fruit", "usage": usage}
    ]
    result = catalog.change_catalog(
        data,
        "remove_category_product",
        {"product_key": "milch", "category_id": "fruit"},
    )
    assert result["products"][0]["usage"] == usage
    assert result["products"][0]["category_id"] is None


def test_legacy_market_store_can_add_categories_without_losing_markets():
    old = {"supermarkets": [{"id": "shop", "name": "Markt"}]}
    result = catalog.change_catalog(
        old, "save_category", {"category_id": "", "name": " Milch "}
    )
    assert result["categories"][0]["name"] == "Milch"
    assert result["categories"][0]["id"]
    assert result["supermarkets"] == old["supermarkets"]
    assert "categories" not in old


def test_rename_keeps_identity_and_market_order():
    result = catalog.change_catalog(
        sample(), "save_category", {"category_id": "fruit", "name": "Gemüse"}
    )
    assert result["categories"][0] == {"id": "fruit", "name": "Gemüse"}
    assert result["supermarkets"][0]["category_ids"] == ["fruit", "bread"]


def test_delete_prunes_market_assignments_atomically():
    old = sample()
    result = catalog.change_catalog(old, "delete_category", {"category_id": "fruit"})
    assert result["categories"] == [{"id": "bread", "name": "Brot"}]
    assert result["supermarkets"][0]["category_ids"] == ["bread"]
    assert old == sample()


def test_order_and_unassignment_preserve_central_store():
    old = sample()
    result = catalog.change_catalog(
        old,
        "save_market_categories",
        {
            "market_id": "shop",
            "category_ids": ["bread", "fruit"],
        },
    )
    assert result["supermarkets"][0]["category_ids"] == ["bread", "fruit"]
    result = catalog.change_catalog(
        result,
        "save_market_categories",
        {
            "market_id": "shop",
            "category_ids": [],
        },
    )
    assert result["categories"] == old["categories"]
    assert result["supermarkets"][0]["category_ids"] == []


def test_market_order_accepts_uncategorized_position():
    result = catalog.change_catalog(
        sample(),
        "save_market_categories",
        {"market_id": "shop", "category_ids": ["fruit", "", "bread"]},
    )
    assert result["supermarkets"][0]["category_ids"] == ["fruit", "", "bread"]


def test_market_bonus_card_is_saved_and_removed_without_affecting_other_markets():
    old = sample()
    old["supermarkets"].append({"id": "other", "name": "Anderer Markt"})
    image = "data:image/png;base64," + "AA=="
    result = catalog.change_catalog(
        old,
        "save_market_bonus_card",
        {"market_id": "shop", "bonus_card": image},
    )
    assert result["supermarkets"][0]["bonus_card"] == image
    assert "bonus_card" not in result["supermarkets"][1]
    removed = catalog.change_catalog(
        result,
        "save_market_bonus_card",
        {"market_id": "shop", "bonus_card": ""},
    )
    assert "bonus_card" not in removed["supermarkets"][0]
    assert "bonus_card" not in old["supermarkets"][0]


@pytest.mark.parametrize(
    "image",
    [
        "data:image/svg+xml;base64,PHN2Zy8+",
        "data:image/png;base64,not-base64",
        "data:image/jpeg;base64,",
    ],
)
def test_market_bonus_card_rejects_invalid_images(image):
    with pytest.raises(ValueError, match="Bonuskartenbild"):
        catalog.change_catalog(
            sample(),
            "save_market_bonus_card",
            {"market_id": "shop", "bonus_card": image},
        )


def test_market_bonus_card_rejects_oversized_images():
    image = "data:image/webp;base64," + (
        "AAAA" * (catalog.MAX_BONUS_CARD_BYTES // 3 + 1)
    )
    with pytest.raises(ValueError, match="Bonuskartenbild"):
        catalog.change_catalog(
            sample(),
            "save_market_bonus_card",
            {"market_id": "shop", "bonus_card": image},
        )


def test_catalog_validation_rejects_invalid_persisted_bonus_card():
    data = sample()
    data["supermarkets"][0]["bonus_card"] = "data:image/png;base64,invalid"
    with pytest.raises(ValueError, match="Bonuskartenbild"):
        catalog.validate_catalog(data)


@pytest.mark.parametrize("ids", [["missing"], ["fruit", "fruit"], ["", ""], [None]])
def test_invalid_orders_do_not_modify_input(ids):
    old = sample()
    before = deepcopy(old)
    with pytest.raises(ValueError):
        catalog.change_catalog(
            old, "save_market_categories", {"market_id": "shop", "category_ids": ids}
        )
    assert old == before


@pytest.mark.parametrize(
    "uid,name", [("", " "), ("fruit", "brot"), ("missing", "Neu"), ("", "x" * 101)]
)
def test_invalid_category_edits(uid, name):
    with pytest.raises(ValueError):
        catalog.change_catalog(
            sample(), "save_category", {"category_id": uid, "name": name}
        )


def test_stale_market_is_rejected():
    with pytest.raises(ValueError):
        catalog.change_catalog(
            sample(),
            "save_market_categories",
            {"market_id": "missing", "category_ids": []},
        )


def test_category_deletion_retains_explicit_product_removal_marker():
    old = sample()
    old["products"] = [{"key": "apfel", "name": "Apfel", "category_id": "fruit"}]
    result = catalog.change_catalog(old, "delete_category", {"category_id": "fruit"})
    assert result["products"][0]["category_id"] is None
    assert old["products"][0]["category_id"] == "fruit"


@pytest.mark.parametrize(
    "value",
    [
        [{"key": "milch", "name": "Milch", "category_id": []}],
        [{"key": "milch", "name": "Milch", "category_id": "missing"}],
        [{"key": "wrong", "name": "Milch", "category_id": None}],
        [{"key": "milch", "name": "Milch", "category_id": None}] * 2,
    ],
)
def test_invalid_product_registry_is_not_silently_reset(value):
    data = sample()
    data["products"] = value
    with pytest.raises(ValueError):
        catalog.validate_catalog(data)


@pytest.mark.parametrize("name", [" MILCH ", "Milch", "milch"])
def test_product_identity_ignores_case_and_surrounding_whitespace(name):
    assert catalog.product_key(name) == "milch"
