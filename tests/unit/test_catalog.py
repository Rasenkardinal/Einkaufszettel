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


@pytest.mark.parametrize("keys", [None, {}, [""], ["Artikel"], ["a", "a"], [123]])
def test_invalid_deleted_product_keys_rejected(keys):
    with pytest.raises(ValueError, match="Löschvermerke"):
        catalog.validate_catalog({"deleted_product_keys": keys})


def test_deleted_product_can_be_explicitly_created_again():
    data = {
        "products": [{"key": "artikel", "name": "Artikel", "category_id": None}],
        "product_events": {"old-event": "artikel"},
    }
    deleted = catalog.change_catalog(data, "delete_product", {"product_key": "artikel"})
    assert deleted["deleted_product_keys"] == ["artikel"]
    assert deleted["product_events"] == data["product_events"]
    recreated = catalog.change_catalog(deleted, "create_product", {"name": "Artikel"})
    assert recreated["products"][0]["name"] == "Artikel"
    catalog.validate_catalog(recreated)


@pytest.mark.parametrize("count", [0, 1, 100, 2147483647])
def test_correct_overall_statistics_without_changing_history(count):
    data = sample()
    usage = {
        "a": {"added": 4, "last_added": 1000, "weeks": {"2026-W43": 4}},
        "b": {"added": 3, "last_added": 2000, "weeks": {"2026-W43": 3}},
    }
    data["products"] = [
        {"key": "milch", "name": "Milch", "category_id": None, "usage": usage}
    ]
    for value in [10, count]:
        data = catalog.change_catalog(
            data, "set_product_statistics", {"product_key": "milch", "count": value}
        )
    product = data["products"][0]
    assert catalog.product_usage_count(product) == count
    assert product["usage"] == usage
    catalog.validate_catalog(data)
    product["usage"]["a"]["added"] += 1
    product["usage"]["a"]["weeks"]["2026-W43"] += 1
    assert catalog.product_usage_count(product) == count + 1


@pytest.mark.parametrize("count", [-1, 1.5, True, None, "3", 2147483648])
def test_invalid_statistics_count_rejected(count):
    data = sample()
    data["products"] = [{"key": "milch", "name": "Milch", "category_id": None}]
    with pytest.raises(ValueError, match="ganze Zahl"):
        catalog.change_catalog(
            data, "set_product_statistics", {"product_key": "milch", "count": count}
        )


@pytest.mark.parametrize("adjustment", [True, "1", 1.5, -1])
def test_invalid_stored_statistics_adjustment_rejected(adjustment):
    data = sample()
    data["products"] = [
        {
            "key": "milch",
            "name": "Milch",
            "category_id": None,
            "usage_adjustment": adjustment,
        }
    ]
    with pytest.raises(ValueError):
        catalog.validate_catalog(data)


def test_corrected_statistics_survive_merge_and_rename():
    data = sample()
    data["products"] = [
        {
            "key": name,
            "name": name,
            "category_id": None,
            "usage": {
                "a": {"added": count, "last_added": 0, "weeks": {"2026-W43": count}}
            },
        }
        for name, count in [("milch", 4), ("milhc", 7)]
    ]
    data = catalog.change_catalog(
        data, "set_product_statistics", {"product_key": "milch", "count": 0}
    )
    data = catalog.change_catalog(
        data, "set_product_statistics", {"product_key": "milhc", "count": 2}
    )
    data = catalog.change_catalog(
        data, "merge_product", {"product_key": "milhc", "target_key": "milch"}
    )
    assert catalog.product_usage_count(data["products"][0]) == 2
    assert data["products"][0]["usage"]["a"]["weeks"]["2026-W43"] == 11
    data = catalog.change_catalog(
        data, "rename_product", {"product_key": "milch", "name": "Hafermilch"}
    )
    assert catalog.product_usage_count(data["products"][0]) == 2


@pytest.mark.parametrize("key", ["deposit_receipt_hint", "show_bonus_card"])
@pytest.mark.parametrize("value", [None, 0, 1, "false", []])
def test_market_checkout_options_reject_non_booleans(key, value):
    data = sample()
    data["supermarkets"][0][key] = value
    with pytest.raises(ValueError, match="Supermarktoptionen"):
        catalog.validate_catalog(data)


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


def test_create_product_adds_an_unassigned_catalog_entry():
    result = catalog.change_catalog(
        sample(), "create_product", {"name": " Hafermilch "}
    )
    assert result["products"] == [
        {
            "key": "hafermilch",
            "name": "Hafermilch",
            "category_id": None,
            "category_known": False,
        }
    ]


def test_rename_product_keeps_usage_and_redirects_old_names():
    data = sample()
    data["products"] = [
        {
            "key": "mandelmilhc",
            "name": "Mandelmilhc",
            "category_id": "fruit",
            "usage": {
                "list-a": {
                    "added": 3,
                    "last_added": 2000,
                    "weeks": {"2026-W42": 2, "2026-W43": 1},
                }
            },
        }
    ]
    data["product_events"] = {"event-a": "mandelmilhc"}
    result = catalog.change_catalog(
        data,
        "rename_product",
        {"product_key": "mandelmilhc", "name": "Mandelmilch"},
    )
    assert result["products"][0]["key"] == "mandelmilch"
    assert result["products"][0]["name"] == "Mandelmilch"
    assert result["products"][0]["usage"] == data["products"][0]["usage"]
    assert result["products"][0]["category_id"] == "fruit"
    assert result["product_aliases"] == {"mandelmilhc": "mandelmilch"}
    assert result["product_events"] == {"event-a": "mandelmilch"}
    assert data["products"][0]["name"] == "Mandelmilhc"


def test_rename_product_rejects_existing_name_instead_of_losing_usage():
    data = sample()
    data["products"] = [
        {"key": "milhc", "name": "Milhc", "category_id": None},
        {"key": "milch", "name": "Milch", "category_id": None},
    ]
    with pytest.raises(ValueError, match="zusammen"):
        catalog.change_catalog(
            data, "rename_product", {"product_key": "milhc", "name": "Milch"}
        )


def test_merge_product_adds_list_weekly_and_total_usage():
    data = sample()
    data["products"] = [
        {
            "key": "mandelmilhc",
            "name": "Mandelmilhc",
            "category_id": "fruit",
            "usage": {
                "list-a": {
                    "added": 3,
                    "last_added": 2000,
                    "weeks": {"2026-W42": 2, "2026-W43": 1},
                },
                "list-b": {
                    "added": 1,
                    "last_added": 1000,
                    "weeks": {"2026-W43": 1},
                },
            },
        },
        {
            "key": "mandelmilch",
            "name": "Mandelmilch",
            "category_id": None,
            "usage": {
                "list-a": {
                    "added": 2,
                    "last_added": 3000,
                    "weeks": {"2026-W42": 1, "2026-W43": 1},
                }
            },
        },
    ]
    data["product_aliases"] = {"mandelmilch-fehler": "mandelmilhc"}
    data["product_events"] = {"event-a": "mandelmilhc"}
    result = catalog.change_catalog(
        data,
        "merge_product",
        {"product_key": "mandelmilhc", "target_key": "mandelmilch"},
    )
    target = result["products"][0]
    assert target["key"] == "mandelmilch"
    assert target["category_id"] == "fruit"
    assert target["usage"] == {
        "list-a": {
            "added": 5,
            "last_added": 3000,
            "weeks": {"2026-W42": 3, "2026-W43": 2},
        },
        "list-b": {"added": 1, "last_added": 1000, "weeks": {"2026-W43": 1}},
    }
    assert result["product_aliases"] == {
        "mandelmilhc": "mandelmilch",
        "mandelmilch-fehler": "mandelmilch",
    }
    assert result["product_events"] == {"event-a": "mandelmilch"}
    assert len(data["products"]) == 2


def test_delete_product_removes_usage_and_references():
    data = sample()
    data["products"] = [
        {
            "key": "milch",
            "name": "Milch",
            "category_id": None,
            "usage": {"list-a": {"added": 1, "last_added": 1, "weeks": {}}},
        }
    ]
    data["product_aliases"] = {"milhc": "milch"}
    data["product_events"] = {"event": "milch"}
    result = catalog.change_catalog(data, "delete_product", {"product_key": "milch"})
    assert result["products"] == []
    assert result["product_aliases"] == {}
    assert result["product_events"] == {"event": "milch"}
    assert set(result["deleted_product_keys"]) == {"milch", "milhc"}
    assert data["products"][0]["usage"]["list-a"]["added"] == 1


def test_dismissed_product_suggestion_is_persisted_and_idempotent():
    data = sample()
    data["products"] = [
        {"key": "eier", "name": "Eier", "category_id": None},
        {"key": "bier", "name": "Bier", "category_id": None},
    ]
    message = {"product_key": "eier", "similar_key": "bier"}

    result = catalog.change_catalog(data, "dismiss_product_suggestion", message)
    repeated = catalog.change_catalog(
        result,
        "dismiss_product_suggestion",
        {"product_key": "bier", "similar_key": "eier"},
    )

    assert result["dismissed_product_suggestions"] == [["eier", "bier"]]
    assert repeated["dismissed_product_suggestions"] == [["eier", "bier"]]
    assert "dismissed_product_suggestions" not in data


def test_dismissed_product_suggestion_rejects_unknown_articles():
    data = sample()
    data["products"] = [
        {"key": "eier", "name": "Eier", "category_id": None},
        {"key": "bier", "name": "Bier", "category_id": None},
    ]
    data["dismissed_product_suggestions"] = [["eier", "milch"]]

    with pytest.raises(ValueError, match="Artikelsuchvorschläge"):
        catalog.validate_catalog(data)
