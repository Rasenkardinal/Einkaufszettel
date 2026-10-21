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
    brand = components[0] / "brand"
    assert {"icon.png", "icon@2x.png", "logo.png", "logo@2x.png"}.issubset(
        {path.name for path in brand.iterdir()}
    )
    for name, size in (
        ("icon.png", (256, 256)),
        ("icon@2x.png", (512, 512)),
        ("logo.png", (512, 180)),
        ("logo@2x.png", (1024, 360)),
    ):
        image = (brand / name).read_bytes()
        assert image[:8] == b"\x89PNG\r\n\x1a\n"
        assert int.from_bytes(image[16:20], "big") == size[0]
        assert int.from_bytes(image[20:24], "big") == size[1]
    webapp = components[0] / "www"
    assert {
        "app.html",
        "app.css",
        "app.js",
        "manifest.json",
        "service-worker.js",
        "icon.svg",
        "icon-192.png",
        "icon-512.png",
    }.issubset({path.name for path in webapp.iterdir()})
    web_manifest = json.loads((webapp / "manifest.json").read_text(encoding="utf-8"))
    assert web_manifest["display"] == "standalone"
    assert {icon["src"] for icon in web_manifest["icons"]} == {
        "./icon.svg",
        "./icon-192.png",
        "./icon-512.png",
    }
    assert 'circle cx="256" cy="256"' in (webapp / "icon.svg").read_text(
        encoding="utf-8"
    )
    app_html = (webapp / "app.html").read_text(encoding="utf-8")
    assert 'class="brand-icon" src="./icon.svg"' in app_html
    assert "open-app-browser" in app_html
    assert 'id="list-select"' in app_html
    assert 'id="edit-item-form"' in app_html
    assert 'id="setup"' in app_html
    assert 'id="manage-lists"' in app_html
    assert 'id="list-management"' in app_html
