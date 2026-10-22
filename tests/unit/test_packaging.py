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
    assert 'id="edit-category" type="hidden"' in html
    assert 'id="edit-category-trigger" class="category-picker-trigger"' in html
    assert 'id="edit-category-search" class="category-search" type="search"' in html
    assert 'id="edit-item-title" tabindex="-1" autofocus' in html


def test_embedded_authentication_opens_standalone_app_before_oauth():
    script = (
        ROOT / "custom_components" / "einkaufszettel" / "www" / "app.js"
    ).read_text(encoding="utf-8")
    auth = script.split("async function connectHomeAssistant() {", 1)[1].split(
        "async function completeAuthorization()", 1
    )[0]
    embedded, oauth = auth.split("  const hassUrl = location.origin;", 1)
    assert "window.top !== window" in embedded
    assert 'appUrl.searchParams.set("connect_ha", "1")' in embedded
    assert 'window.open(appUrl.href, "_blank")' in embedded
    assert "appWindow.opener = null;" in embedded
    assert "if (!appWindow)" in embedded
    assert "return;" in embedded
    assert 'redirectUrl.searchParams.delete("connect_ha")' in oauth
    startup = script.split("async function start() {", 1)[1]
    assert 'appUrl.searchParams.delete("connect_ha")' in startup
    assert "if (startAuthorization)" in startup
    assert "await connectHomeAssistant().catch(showError)" in startup


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
        ("menu-supermarkets", "Supermärkte verwalten", ("manage-supermarkets",)),
        ("menu-categories", "Produktkategorien verwalten", ("manage-categories",)),
    ):
        match = re.search(
            rf'<details id="{section}"[^>]*>(.*?)</details>', html, re.DOTALL
        )
        assert match is not None
        content = match.group(1)
        assert f"<summary>{title}</summary>" in content
        assert 'class="setup-submenu"' in content
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
    submenu = re.search(
        r'<details id="menu-design" class="setup-section">(.*?)</details>',
        html,
        re.DOTALL,
    )
    assert submenu is not None
    assert (
        dict(
            re.findall(
                r'value="([^"]+)"(?: checked)?><span[^>]+></span><span>([^<]+)</span>',
                submenu.group(1),
            )
        )
        == designs
    )
    assert '<body data-theme="mono">' in html
    assert 'value="mono" checked' in submenu.group(1)
    assert 'id="design-dialog"' not in html
    assert 'id="design-select"' not in html
    assert ".design-row:has(input:checked)" in css
    assert '.setup-section > summary::after { content: "+"' in css
    assert r'.setup-section[open] > summary::after { content: "\2212"' in css
    assert ".setup-section > summary::-webkit-details-marker { display: none; }" in css
    assert "designDialog" not in script
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
    assert 'id="manage-supermarkets">Supermarktverwaltung öffnen</button>' in html
    assert 'id="catalog-page" class="app management-page" hidden' in html
    assert 'id="manage-categories"' in html
    assert '<dialog id="supermarket-management"' not in html
    assert '<dialog id="list-management"' not in html
    for field in ("edit-category", "edit-quantity", "edit-notes"):
        assert f'id="{field}"' in html
