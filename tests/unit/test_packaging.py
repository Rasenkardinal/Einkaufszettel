"""Guard the metadata required by HACS commit downloads."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[2]


def test_hacs_metadata_and_integration_layout():
    hacs = json.loads((ROOT / "hacs.json").read_text(encoding="utf-8"))
    assert hacs["name"] == "Einkaufszettel"
    assert hacs["homeassistant"] == "2025.10.0"
    assert not hacs.get("content_in_root", False)
    assert not hacs.get("zip_release", False)
    components = [
        path
        for path in (ROOT / "custom_components").iterdir()
        if path.is_dir() and not path.name.startswith((".", "__"))
    ]
    assert [path.name for path in components] == ["einkaufszettel"]
    manifest = json.loads((components[0] / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["domain"] == components[0].name
    assert manifest["name"] == hacs["name"]
    assert manifest["integration_type"] == "service"
    assert (components[0] / "__init__.py").is_file()
    assert (components[0] / "config_flow.py").is_file()
