"""Guard the metadata required by HACS commit downloads."""

import json
import re
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


def test_web_app_assets_are_versioned_and_precached():
    webapp = ROOT / "custom_components" / "einkaufszettel" / "www"
    html = (webapp / "app.html").read_text(encoding="utf-8")
    worker = (webapp / "service-worker.js").read_text(encoding="utf-8")
    assets = re.findall(r'(?:href|src)="(\./app\.(?:css|js)\?v=[^"]+)"', html)
    assert len(assets) == 2
    version = json.loads((webapp.parent / "manifest.json").read_text(encoding="utf-8"))[
        "version"
    ]
    assert {asset.split("?v=")[1] for asset in assets} == {version}
    for asset in assets:
        assert f'"{asset}"' in worker


def test_list_selection_uses_custom_flyout_not_native_popup():
    html = (
        ROOT / "custom_components" / "einkaufszettel" / "www" / "app.html"
    ).read_text(encoding="utf-8")
    assert '<select id="list-select"' not in html
    assert '<button id="list-select"' in html
    assert 'aria-controls="list-flyout"' in html
    assert 'id="list-flyout" aria-label="Einkaufsliste auswählen" hidden' in html


def test_app_menu_groups_existing_actions():
    html = (
        ROOT / "custom_components" / "einkaufszettel" / "www" / "app.html"
    ).read_text(encoding="utf-8")
    for section, title, actions in (
        (
            "menu-installation",
            "Installation",
            ("connect", "install", "open-app-browser", "open-homeassistant"),
        ),
        ("menu-lists", "Listenverwaltung", ("manage-lists", "copy-source")),
    ):
        match = re.search(
            rf'<details id="{section}"[^>]*>(.*?)</details>', html, re.DOTALL
        )
        assert match is not None
        content = match.group(1)
        assert f"<summary>{title}</summary>" in content
        for action in actions:
            assert f'id="{action}"' in content


def test_named_dark_designs_share_layout_and_storage():
    webapp = ROOT / "custom_components" / "einkaufszettel" / "www"
    html = (webapp / "app.html").read_text(encoding="utf-8")
    css = (webapp / "app.css").read_text(encoding="utf-8")
    script = (webapp / "app.js").read_text(encoding="utf-8")
    designs = {
        "botanical": "Botanical",
        "midnight-plum": "Midnight Plum",
        "market-journal": "Market Journal",
        "fresh-signal": "Fresh Signal",
        "mono": "Mono",
        "tomato": "Tomato",
        "lime-focus": "Lime Focus",
        "indigo-pocket": "Indigo Pocket",
    }
    dialog = re.search(
        r'<dialog id="design-dialog"[^>]*>(.*?)</dialog>', html, re.DOTALL
    )
    assert dialog is not None
    assert (
        dict(
            re.findall(
                r'value="([^"]+)"(?: checked)?><span[^>]+></span><span>([^<]+)</span>',
                dialog.group(1),
            )
        )
        == designs
    )
    assert '<body data-theme="mono">' in html
    assert 'value="mono" checked' in dialog.group(1)
    assert (
        'id="menu-design" type="button" aria-haspopup="dialog" aria-controls="design-dialog"'
        in html
    )
    assert 'id="design-select"' not in html
    assert ".design-row:has(input:checked)" in css
    assert "elements.designDialog.showModal()" in script
    for theme in designs.keys() - {"mono"}:
        block = re.search(rf'body\[data-theme="{theme}"\]\s*\{{([^}}]+)\}}', css)
        assert block is not None
        assert all(
            declaration.strip().startswith("--")
            for declaration in block.group(1).split(";")
            if declaration.strip()
        )
    assert "localStorage.setItem(DESIGN_KEY" in script
    assert "localStorage.getItem(DESIGN_KEY)" in script
    assert ".item.completed .item-name { text-decoration: line-through; }" in css
    assert 'class="list-arrow" aria-hidden="true"' in html
    assert "Design-Einstellungen folgen" not in html


def test_supermarket_picker_and_management_are_separate_from_lists():
    webapp = ROOT / "custom_components" / "einkaufszettel" / "www"
    html = (webapp / "app.html").read_text(encoding="utf-8")
    heading = re.search(r'<div class="list-heading">(.*?)</div>', html, re.DOTALL)
    assert heading is not None
    assert 'id="market-select"' in heading.group(1)
    assert 'aria-label="Supermarkt auswählen"' in heading.group(1)
    assert '<select id="market-select"' not in html
    assert '<button id="market-select"' in heading.group(1)
    assert 'aria-controls="market-flyout"' in heading.group(1)
    assert 'id="market-flyout" aria-label="Supermarkt auswählen" hidden' in html
    assert '<span id="market-name">Ohne Markt</span>' in heading.group(1)
    assert 'id="manage-supermarkets">Supermärkte verwalten</button>' in html
    assert 'id="supermarket-management"' in html
    assert 'id="add-supermarket-form"' in html
