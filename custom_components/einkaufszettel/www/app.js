const STORAGE_NAME = "einkaufszettel-offline-v1";
const ENTRY_KEY = "einkaufszettel.entry_id";
const TOKEN_KEY = "einkaufszettel.auth";
const OAUTH_STATE_PREFIX = "einkaufszettel.oauth.";
const DOMAIN = "einkaufszettel";
const DESIGN_KEY = "einkaufszettel.design";
const MARKETS_KEY = "einkaufszettel.supermarkets";
const MARKET_SELECTION_PREFIX = "einkaufszettel.supermarket.";
const CATALOG_KEY = "einkaufszettel.catalog";

const elements = {
  setup: document.querySelector("#setup"),
  marketSelect: document.querySelector("#market-select"),
  marketFlyout: document.querySelector("#market-flyout"),
  marketName: document.querySelector("#market-name"),
  manageSupermarkets: document.querySelector("#manage-supermarkets"),
  catalogPage: document.querySelector("#catalog-page"),
  catalogTitle: document.querySelector("#catalog-title"),
  catalogHelp: document.querySelector("#catalog-help"),
  catalogMessage: document.querySelector("#catalog-message"),
  catalogContent: document.querySelector("#catalog-content"),
  catalogBack: document.querySelector("#catalog-back"),
  manageCategories: document.querySelector("#manage-categories"),
  designOptions: document.querySelector("#design-options"),
  designName: document.querySelector("#design-name"),
  designMessage: document.querySelector("#design-message"),
  manageLists: document.querySelector("#manage-lists"),
  listManagement: document.querySelector("#list-management"),
  managementMessage: document.querySelector("#management-message"),
  sourceLists: document.querySelector("#source-lists"),
  addForm: document.querySelector("#add-form"),
  newItem: document.querySelector("#new-item"),
  items: document.querySelector("#items"),
  empty: document.querySelector("#empty"),
  message: document.querySelector("#message"),
  resolveSyncConflicts: document.querySelector("#resolve-sync-conflicts"),
  syncConflicts: document.querySelector("#sync-conflicts"),
  syncConflictsMessage: document.querySelector("#sync-conflicts-message"),
  syncConflictsContent: document.querySelector("#sync-conflicts-content"),
  listName: document.querySelector("#list-name"),
  listSelect: document.querySelector("#list-select"),
  listFlyout: document.querySelector("#list-flyout"),
  editItem: document.querySelector("#edit-item"),
  editItemForm: document.querySelector("#edit-item-form"),
  editSummary: document.querySelector("#edit-summary"),
  editCategory: document.querySelector("#edit-category"),
  editQuantity: document.querySelector("#edit-quantity"),
  editNotes: document.querySelector("#edit-notes"),
  cancelEdit: document.querySelector("#cancel-edit"),
  connectionDot: document.querySelector("#connection-dot"),
  connectionLabel: document.querySelector("#connection-label"),
  syncDetail: document.querySelector("#sync-detail"),
  sync: document.querySelector("#sync"),
  copySource: document.querySelector("#copy-source"),
  connect: document.querySelector("#connect"),
  install: document.querySelector("#install"),
  installHelp: document.querySelector("#install-help"),
  openHomeassistant: document.querySelector("#open-homeassistant"),
  openAppBrowser: document.querySelector("#open-app-browser"),
};

const queryEntryId = new URLSearchParams(location.search).get("entry_id");
let entryId = queryEntryId;
try {
  if (queryEntryId) localStorage.setItem(ENTRY_KEY, queryEntryId);
  else entryId = localStorage.getItem(ENTRY_KEY);
} catch {
  entryId = queryEntryId;
}
let database;
let socket;
let connecting = false;
let authenticated = false;
let authenticationBlocked = false;
let refreshAfterRejection = false;
let reconnectTimer;
let reconnectAttempts = 0;
let connectionTimer;
let connectionSyncTimer;
let heartbeatTimer;
let heartbeatId;
let connectionGeneration = 0;
let nextMessageId = 1;
let pendingInstallPrompt;
let currentItems = [];
let deletedUids = new Set();
let pendingOperations = [];
let busy = false;
let syncPromise;
let syncRequested = false;
let fullSyncRequested = false;
let syncTimer;
let listRefreshPromise;
let lastOperationTime = 0;
let availableLists = [];
let editingUid;
let supermarkets = [];
let selectedMarket = "";
let managingSupermarkets = false;
let categories = [];
let catalogView;
let catalogDraft;
let catalogDirty = false;
let catalogRequest = 0;
const nameOrder = new Intl.Collator("de", { sensitivity: "base", numeric: true });

function validateSupermarkets(value) {
  if (!Array.isArray(value) || value.some(market =>
    !market || typeof market.id !== "string" || !market.id ||
    typeof market.name !== "string" || !market.name.trim() || market.name.length > 100 ||
    (market.category_ids !== undefined && (!Array.isArray(market.category_ids) ||
      market.category_ids.some(id => typeof id !== "string" || !id) ||
      new Set(market.category_ids).size !== market.category_ids.length))
  ) || new Set(value.map(market => market.id)).size !== value.length) {
    throw new Error("Die Supermarktdaten sind ungültig. Bitte erneut mit Home Assistant verbinden.");
  }
  return value;
}

function applyCatalog(value) {
  const nextMarkets = validateSupermarkets(value.supermarkets);
  const nextCategories = validateSupermarkets(value.categories);
  if (nextMarkets.some(market => (market.category_ids || []).some(id => !nextCategories.some(c => c.id === id)))) {
    throw new Error("Der Katalog enthält unbekannte Markt-Kategorien. Bitte erneut laden.");
  }
  supermarkets = nextMarkets;
  categories = nextCategories;
}

function cacheCatalog() {
  localStorage.setItem(CATALOG_KEY, JSON.stringify({ supermarkets, categories }));
}

function renderMarketSelection() {
  elements.marketFlyout.replaceChildren();
  for (const market of [{ id: "", name: "Ohne Markt" }, ...supermarkets]) {
    elements.marketFlyout.append(createPickerOption(market.name, market.id === selectedMarket, () => {
      closeFlyout(elements.marketSelect, elements.marketFlyout, true);
      selectedMarket = market.id;
      renderMarketSelection();
      render();
      try {
        localStorage.setItem(MARKET_SELECTION_PREFIX + entryId, selectedMarket);
      } catch (error) {
        showError(new Error(`Die Marktauswahl konnte nicht gespeichert werden: ${error.message}`));
      }
    }));
  }
  const market = supermarkets.find(market => market.id === selectedMarket);
  elements.marketName.textContent = market?.name || "Ohne Markt";
  elements.marketSelect.setAttribute("aria-label", `Supermarkt auswählen, aktuell ${elements.marketName.textContent}`);
  elements.marketSelect.disabled = busy || !entryId;
}

function loadMarketSelection() {
  selectedMarket = "";
  try {
    selectedMarket = entryId ? localStorage.getItem(MARKET_SELECTION_PREFIX + entryId) || "" : "";
    if (selectedMarket && !supermarkets.some(market => market.id === selectedMarket)) {
      localStorage.removeItem(MARKET_SELECTION_PREFIX + entryId);
      selectedMarket = "";
      showError(new Error("Der gewählte Supermarkt ist nicht mehr verfügbar. Bitte wähle einen anderen."));
    }
  } catch (error) {
    showError(error);
  }
  renderMarketSelection();
}

function loadCachedSupermarkets() {
  try {
    const catalog = localStorage.getItem(CATALOG_KEY);
    if (catalog) applyCatalog(JSON.parse(catalog));
    else {
      const cached = localStorage.getItem(MARKETS_KEY);
      if (cached) supermarkets = validateSupermarkets(JSON.parse(cached));
    }
  } catch (error) {
    showError(error);
  }
  loadMarketSelection();
}

async function refreshSupermarkets() {
  const catalog = await sendCommand(`${DOMAIN}/get_catalog`);
  applyCatalog(catalog);
  let cacheError;
  try {
    cacheCatalog();
  } catch (error) {
    cacheError = new Error(`Supermärkte geladen, aber die Offline-Kopie konnte nicht gespeichert werden: ${error.message}`);
  }
  loadMarketSelection();
  render();
  if (cacheError) throw cacheError;
}

function button(text, action, className = "secondary") {
  const element = document.createElement("button");
  element.type = "button";
  element.className = className;
  element.textContent = text;
  element.addEventListener("click", action);
  return element;
}

function paragraph(text, className = "management-help") {
  const element = document.createElement("p");
  element.className = className;
  element.textContent = text;
  return element;
}

function showManagementPage(page) {
  cancelCategoryDrag?.();
  document.querySelector("main.app").hidden = true;
  elements.catalogPage.hidden = page !== elements.catalogPage;
  elements.listManagement.hidden = page !== elements.listManagement;
  elements.setup.open = false;
  window.scrollTo(0, 0);
}

function leaveManagement() {
  if (managingSupermarkets || (catalogDirty && !confirm("Ungespeicherte Änderungen verwerfen?"))) return;
  cancelCategoryDrag?.();
  catalogRequest++;
  catalogDirty = false;
  catalogView = undefined;
  elements.catalogPage.hidden = true;
  elements.listManagement.hidden = true;
  document.querySelector("main.app").hidden = false;
  elements.listSelect.focus();
}

function openCatalog(view, record) {
  if (managingSupermarkets || (catalogDirty && !confirm("Ungespeicherte Änderungen verwerfen?"))) return;
  cancelCategoryDrag?.();
  catalogDirty = false;
  catalogView = view;
  catalogDraft = record ? { ...record, category_ids: [...(record.category_ids || [])] } : { id: "", name: "", category_ids: [] };
  showManagementPage(elements.catalogPage);
  renderCatalogPage();
}

async function loadCatalogPage(view) {
  openCatalog(view);
  const request = ++catalogRequest;
  elements.catalogMessage.textContent = "Katalog wird geladen …";
  try {
    await refreshSupermarkets();
    if (request === catalogRequest && catalogView === view && !catalogDirty) {
      renderCatalogPage();
      elements.catalogMessage.textContent = "";
    }
  } catch (error) {
    if (request === catalogRequest) {
      elements.catalogMessage.textContent = `Offline-Kopie. Änderungen benötigen eine Verbindung und HA-Administratorrechte: ${error.message}`;
    }
  }
}

async function saveCatalog(command, payload, nextView) {
  if (managingSupermarkets) return;
  managingSupermarkets = true;
  elements.catalogContent.inert = true;
  elements.catalogBack.disabled = true;
  elements.catalogMessage.textContent = "Wird gespeichert …";
  let saved = false;
  try {
    const result = await sendCommand(`${DOMAIN}/${command}`, payload);
    if (command.endsWith("supermarket")) {
      applyCatalog({ supermarkets: result, categories });
    } else {
      applyCatalog(result);
    }
    saved = true;
    catalogDirty = false;
    catalogView = nextView;
    cacheCatalog();
    elements.catalogMessage.textContent = "In Home Assistant gespeichert.";
  } catch (error) {
    elements.catalogMessage.textContent = saved
      ? `In Home Assistant gespeichert, aber Offline-Kopie fehlgeschlagen: ${error.message}`
      : error.message;
  } finally {
    managingSupermarkets = false;
    elements.catalogContent.inert = false;
    elements.catalogBack.disabled = false;
    if (saved) {
      const message = elements.catalogMessage.textContent;
      loadMarketSelection();
      render();
      renderCatalogPage();
      elements.catalogMessage.textContent = message;
    }
  }
}

let cancelCategoryDrag;

function renderCatalogPage() {
  cancelCategoryDrag?.();
  const content = elements.catalogContent;
  content.replaceChildren();
  elements.catalogMessage.textContent = "";
  const isMarket = catalogView?.startsWith("market");
  const isList = catalogView === "markets" || catalogView === "categories";
  const noun = isMarket ? "Supermarkt" : "Kategorie";
  elements.catalogBack.querySelector("span").textContent = isList ? "Zurück zur Liste"
    : catalogView === "market-order" ? "Supermarkt bearbeiten"
    : catalogView === "market-select" ? "Marktkategorien"
    : isMarket ? "Supermärkte" : "Produktkategorien";
  elements.catalogBack.onclick = () => {
    if (isList) leaveManagement();
    else if (catalogView === "market-order") openCatalog("market-edit", catalogDraft);
    else if (catalogView === "market-select") {
      catalogView = "market-order";
      renderCatalogPage();
    } else openCatalog(isMarket ? "markets" : "categories");
  };
  elements.catalogHelp.textContent = "Gemeinsamer Katalog für alle Nutzer. Speichern benötigt eine Verbindung und HA-Administratorrechte.";
  if (isList) {
    elements.catalogTitle.textContent = isMarket ? "Supermärkte" : "Produktkategorien";
    content.append(button(`＋ ${noun} hinzufügen`, () => openCatalog(isMarket ? "market-edit" : "category-edit"), "primary full-width"));
    const records = [...(isMarket ? supermarkets : categories)].sort((a, b) => nameOrder.compare(a.name, b.name));
    const list = document.createElement("div");
    list.className = "management-list";
    for (const record of records) {
      list.append(button(`${record.name}  ›`, () => openCatalog(isMarket ? "market-edit" : "category-edit", record), "management-link"));
    }
    content.append(list);
    if (!records.length) content.append(paragraph(`Noch keine ${isMarket ? "Supermärkte" : "Produktkategorien"} angelegt.`));
  } else if (catalogView === "market-order" || catalogView === "market-select") {
    renderMarketCategories();
  } else {
    elements.catalogTitle.textContent = `${noun} ${catalogDraft.id ? "bearbeiten" : "hinzufügen"}`;
    const form = document.createElement("form");
    form.className = "management-form";
    const label = document.createElement("label");
    label.htmlFor = "catalog-name";
    label.textContent = isMarket ? "Supermarktname" : "Kategoriename";
    const input = document.createElement("input");
    input.id = "catalog-name";
    input.required = true;
    input.maxLength = 100;
    input.autocomplete = "off";
    input.value = catalogDraft.name;
    input.addEventListener("input", () => {
      input.setCustomValidity("");
      catalogDraft.name = input.value;
      catalogDirty = true;
    });
    form.append(label, input);
    if (isMarket && catalogDraft.id) {
      form.append(button("Produktkategorien für diesen Markt bearbeiten  ›", () => {
        if (catalogDirty && !confirm("Ungespeicherten Namen verwerfen und Produktkategorien öffnen?")) return;
        catalogDirty = false;
        catalogDraft = { ...supermarkets.find(m => m.id === catalogDraft.id), category_ids: [...catalogDraft.category_ids] };
        catalogView = "market-order";
        renderCatalogPage();
      }, "management-link category-navigation"));
    }
    if (catalogDraft.id) {
      const danger = document.createElement("section");
      danger.className = "danger-section";
      danger.append(paragraph(`${noun} löschen`, "danger-title"));
      danger.append(paragraph(isMarket
        ? "Entfernt diesen Markt aus der Marktauswahl. Einkaufslisten bleiben erhalten."
        : "Entfernt die Kategorie und ihre Marktzuordnungen. Artikel bleiben erhalten und erscheinen ohne Kategorie."));
      danger.append(button(`${noun} löschen`, () => {
        if (confirm(`${noun} „${catalogDraft.name}“ endgültig für alle Nutzer löschen?`)) {
          saveCatalog(isMarket ? "delete_supermarket" : "delete_category",
            { [isMarket ? "market_id" : "category_id"]: catalogDraft.id }, isMarket ? "markets" : "categories");
        }
      }, "secondary danger-button"));
      form.append(danger);
    }
    const actions = document.createElement("div");
    actions.className = "page-actions";
    const save = button("Speichern", () => {});
    save.type = "submit";
    save.className = "primary";
    actions.append(button("Abbrechen", () => openCatalog(isMarket ? "markets" : "categories")), save);
    form.append(actions);
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!input.value.trim()) {
        input.setCustomValidity("Bitte gib einen Namen ein.");
        input.reportValidity();
        return;
      }
      saveCatalog(isMarket ? "save_supermarket" : "save_category",
        { [isMarket ? "market_id" : "category_id"]: catalogDraft.id, name: input.value.trim() },
        isMarket ? "markets" : "categories");
    });
    content.append(form);
  }
  content.append(paragraph("Offline-Kopie auf diesem Gerät · Änderungen werden in Home Assistant gespeichert.", "management-footer"));
  elements.catalogTitle.focus();
}

function renderMarketCategories() {
  const content = elements.catalogContent;
  const selecting = catalogView === "market-select";
  elements.catalogTitle.textContent = selecting ? "Kategorien auswählen" : "Produktkategorien bearbeiten";
  elements.catalogHelp.textContent = `${catalogDraft.name} · ${selecting ? "Aus dem Kategoriespeicher wählen (A–Z)." : "Diese Reihenfolge gilt nur für diesen Markt."}`;
  if (selecting) {
    const selected = new Set(catalogDraft.category_ids);
    for (const category of [...categories].sort((a, b) => nameOrder.compare(a.name, b.name))) {
      const label = document.createElement("label");
      label.className = "category-choice";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = selected.has(category.id);
      checkbox.addEventListener("change", () => {
        catalogDraft.category_ids = checkbox.checked
          ? [...catalogDraft.category_ids, category.id]
          : catalogDraft.category_ids.filter(id => id !== category.id);
        catalogDirty = true;
      });
      label.append(checkbox, document.createTextNode(category.name));
      content.append(label);
    }
    if (!categories.length) content.append(paragraph("Noch keine Kategorien im Speicher. Bitte zuerst unter Produktkategorien verwalten anlegen."));
    content.append(button("Auswahl übernehmen", () => { catalogView = "market-order"; renderCatalogPage(); }, "primary full-width"));
    return;
  }
  content.append(button("＋ Kategorien aus dem Speicher auswählen  ›", () => {
    catalogView = "market-select";
    renderCatalogPage();
  }, "primary full-width"));
  content.append(paragraph("Am Griff ziehen oder mit ↑ / ↓ verschieben. × entfernt nur die Marktzuordnung."));
  const list = document.createElement("ol");
  list.className = "category-order";
  const move = (from, to) => {
    const ids = [...catalogDraft.category_ids];
    const [id] = ids.splice(from, 1);
    ids.splice(to, 0, id);
    catalogDraft.category_ids = ids;
    catalogDirty = true;
    renderCatalogPage();
    elements.catalogContent.querySelectorAll(".move-grip")[to]?.focus();
  };
  catalogDraft.category_ids.forEach((id, index) => {
    const category = categories.find(c => c.id === id);
    if (!category) return;
    const row = document.createElement("li");
    row.className = "category-order-row";
    row.dataset.categoryId = id;
    const position = () => catalogDraft.category_ids.indexOf(id);
    const grip = button("⠿", () => {}, "text-button move-grip");
    grip.setAttribute("aria-label", `${category.name} verschieben; Pfeiltasten hoch und runter`);
    grip.addEventListener("keydown", event => {
      const from = position();
      const target = event.key === "ArrowUp" ? from - 1 : event.key === "ArrowDown" ? from + 1 : from;
      if (target !== from) {
        event.preventDefault();
        if (target >= 0 && target < catalogDraft.category_ids.length) move(from, target);
      }
    });
    const name = document.createElement("span");
    name.className = "order-name";
    name.textContent = `${index + 1}. ${category.name}`;
    const up = button("↑", () => move(position(), position() - 1), "secondary move-button");
    up.disabled = index === 0;
    up.setAttribute("aria-label", `${category.name} nach oben`);
    const down = button("↓", () => move(position(), position() + 1), "secondary move-button");
    down.disabled = index === catalogDraft.category_ids.length - 1;
    down.setAttribute("aria-label", `${category.name} nach unten`);
    const remove = button("×", () => {
      catalogDraft.category_ids = catalogDraft.category_ids.filter(key => key !== id);
      catalogDirty = true;
      renderCatalogPage();
    }, "text-button move-button");
    remove.setAttribute("aria-label", `${category.name} aus diesem Markt entfernen`);
    row.append(grip, name, up, down, remove);
    list.append(row);
  });
  content.append(list);
  initializeCategorySorting(list);
  if (!catalogDraft.category_ids.length) content.append(paragraph("Noch keine Kategorien für diesen Markt ausgewählt."));
  const actions = document.createElement("div");
  actions.className = "page-actions";
  actions.append(button("Abbrechen", () => openCatalog("market-edit", supermarkets.find(m => m.id === catalogDraft.id))),
    button("Speichern", () => saveCatalog("save_market_categories", {
      market_id: catalogDraft.id, category_ids: catalogDraft.category_ids,
    }, "markets"), "primary"));
  content.append(actions);
}

function initializeCategorySorting(list) {
  let drag;
  let frame;
  const announcement = document.createElement("p");
  announcement.className = "visually-hidden";
  announcement.setAttribute("role", "status");
  list.after(announcement);

  function updateOrder() {
    const rows = [...list.children];
    catalogDraft.category_ids = rows.map(row => row.dataset.categoryId);
    rows.forEach((row, index) => {
      const category = categories.find(value => value.id === row.dataset.categoryId);
      row.querySelector(".order-name").textContent = `${index + 1}. ${category.name}`;
      const controls = row.querySelectorAll(".secondary");
      controls[0].disabled = index === 0;
      controls[1].disabled = index === rows.length - 1;
    });
  }

  function positionRow() {
    if (!drag?.ghost) return;
    drag.ghost.style.top = `${drag.y - drag.offsetY}px`;
    drag.ghost.style.left = `${drag.x - drag.offsetX}px`;
    const others = [...list.children].filter(row => row !== drag.row);
    const target = others.find(row => {
      const rect = row.getBoundingClientRect();
      return drag.y < rect.top + rect.height / 2;
    });
    if (drag.row.nextElementSibling !== (target || null)) {
      list.insertBefore(drag.row, target || null);
      updateOrder();
      catalogDirty = true;
      announcement.textContent = `${drag.name}, Position ${catalogDraft.category_ids.indexOf(drag.id) + 1} von ${list.children.length}`;
    }
  }

  function scrollAtEdge(timestamp) {
    if (!drag?.ghost) return;
    const elapsed = Math.min(timestamp - (drag.time || timestamp), 32);
    drag.time = timestamp;
    const scroller = drag.scroller;
    const isDocument = scroller === document.scrollingElement;
    const rect = isDocument ? { top: 0, bottom: window.innerHeight } : scroller.getBoundingClientRect();
    const top = Math.max(0, rect.top);
    const bottom = Math.min(window.innerHeight, rect.bottom);
    const edge = Math.min(64, (bottom - top) / 4);
    const direction = drag.y < top + edge ? -Math.min(1, (top + edge - drag.y) / edge)
      : drag.y > bottom - edge ? Math.min(1, (drag.y - bottom + edge) / edge) : 0;
    if (direction && drag.x >= 0 && drag.x <= window.innerWidth) {
      scroller.scrollTop += direction * elapsed * .65;
      positionRow();
    }
    frame = window.requestAnimationFrame(scrollAtEdge);
  }

  function finish(cancelled = false) {
    if (!drag) return;
    const previous = drag;
    drag = undefined;
    window.cancelAnimationFrame(frame);
    window.removeEventListener("pointermove", pointerMove);
    window.removeEventListener("pointerup", pointerUp);
    window.removeEventListener("pointercancel", pointerCancel);
    window.removeEventListener("keydown", keyDown, true);
    window.removeEventListener("blur", pointerCancel);
    window.removeEventListener("pagehide", pointerCancel);
    window.removeEventListener("pointerdown", blockOtherPointer, true);
    list.removeEventListener("lostpointercapture", pointerCancel);
    previous.ghost?.remove();
    previous.row.classList.remove("dragging");
    list.classList.remove("sorting");
    if (cancelled) {
      const rows = new Map([...list.children].map(row => [row.dataset.categoryId, row]));
      for (const id of previous.order) list.append(rows.get(id));
      updateOrder();
      catalogDirty = previous.dirty;
      announcement.textContent = "Verschieben abgebrochen.";
    } else if (previous.ghost) {
      catalogDirty = previous.dirty || previous.order.some((id, index) => id !== catalogDraft.category_ids[index]);
      announcement.textContent = `${previous.name}, Position ${catalogDraft.category_ids.indexOf(previous.id) + 1} von ${list.children.length}`;
    }
    if (list.hasPointerCapture(previous.pointerId)) list.releasePointerCapture(previous.pointerId);
    previous.grip.focus({ preventScroll: true });
    cancelCategoryDrag = undefined;
  }

  function pointerMove(event) {
    if (!drag || event.pointerId !== drag.pointerId) return;
    event.preventDefault();
    drag.x = event.clientX;
    drag.y = event.clientY;
    if (!drag.ghost) {
      if (Math.hypot(drag.x - drag.startX, drag.y - drag.startY) < 5) return;
      const rect = drag.row.getBoundingClientRect();
      drag.ghost = drag.row.cloneNode(true);
      drag.ghost.classList.add("category-drag-ghost");
      drag.ghost.setAttribute("aria-hidden", "true");
      drag.ghost.inert = true;
      drag.ghost.style.width = `${rect.width}px`;
      document.body.append(drag.ghost);
      drag.row.classList.add("dragging");
      list.classList.add("sorting");
      frame = window.requestAnimationFrame(scrollAtEdge);
    }
    positionRow();
  }

  function pointerUp(event) {
    if (drag && event.pointerId === drag.pointerId) finish();
  }
  function pointerCancel(event) {
    if (drag && (event.pointerId === undefined || event.pointerId === drag.pointerId)) finish(true);
  }
  function keyDown(event) {
    event.preventDefault();
    event.stopImmediatePropagation();
    if (event.key === "Escape") {
      finish(true);
    }
  }
  function blockOtherPointer(event) {
    if (drag && event.pointerId !== drag.pointerId) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }
  list.addEventListener("pointerdown", event => {
    const grip = event.target.closest(".move-grip");
    if (!grip || event.button !== 0 || event.isPrimary === false || drag) return;
    event.preventDefault();
    const row = grip.closest(".category-order-row");
    const rect = row.getBoundingClientRect();
    let scroller = list.parentElement;
    while (scroller && !(scroller.scrollHeight > scroller.clientHeight &&
      /(auto|scroll)/.test(getComputedStyle(scroller).overflowY))) scroller = scroller.parentElement;
    drag = {
      grip, row, id: row.dataset.categoryId, name: categories.find(value => value.id === row.dataset.categoryId).name,
      pointerId: event.pointerId, startX: event.clientX, startY: event.clientY,
      x: event.clientX, y: event.clientY, offsetX: event.clientX - rect.left, offsetY: event.clientY - rect.top,
      order: [...catalogDraft.category_ids], dirty: catalogDirty,
      scroller: scroller || document.scrollingElement,
    };
    grip.focus({ preventScroll: true });
    list.setPointerCapture(event.pointerId);
    cancelCategoryDrag = () => finish(true);
    window.addEventListener("pointermove", pointerMove, { passive: false });
    window.addEventListener("pointerup", pointerUp);
    window.addEventListener("pointercancel", pointerCancel);
    window.addEventListener("keydown", keyDown, true);
    window.addEventListener("blur", pointerCancel);
    window.addEventListener("pagehide", pointerCancel);
    window.addEventListener("pointerdown", blockOtherPointer, true);
    list.addEventListener("lostpointercapture", pointerCancel);
  });
}

elements.manageSupermarkets.addEventListener("click", () => loadCatalogPage("markets"));
elements.manageCategories.addEventListener("click", () => loadCatalogPage("categories"));
document.querySelector("#lists-back").addEventListener("click", leaveManagement);
window.addEventListener("beforeunload", event => {
  if (catalogDirty || managingSupermarkets) { event.preventDefault(); event.returnValue = ""; }
});

function applyDesign(theme) {
  document.body.dataset.theme = theme;
  for (const option of elements.designOptions.querySelectorAll("input")) {
    option.checked = option.value === theme;
    if (option.checked) elements.designName.textContent = option.parentElement.querySelector("span:not([aria-hidden])").textContent;
  }
  document.querySelector('meta[name="theme-color"]').content =
    getComputedStyle(document.body).getPropertyValue("--bg").trim();
}

function initializeDesign() {
  try {
    const theme = localStorage.getItem(DESIGN_KEY) || "mono";
    if (![...elements.designOptions.querySelectorAll("input")].some((option) => option.value === theme)) {
      throw new Error("Das gespeicherte Farbschema ist unbekannt. Bitte wähle unter Menü → Design ein neues aus.");
    }
    applyDesign(theme);
  } catch (error) {
    showError(error);
  }
}

elements.designOptions.addEventListener("change", (event) => {
  const theme = event.target.value;
  applyDesign(theme);
  elements.designMessage.textContent = "";
  try {
    localStorage.setItem(DESIGN_KEY, theme);
  } catch (error) {
    const message = `Das Farbschema konnte nicht auf diesem Gerät gespeichert werden: ${error.message}`;
    elements.designMessage.textContent = message;
    showError(new Error(message));
  }
});

function openDatabase() {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(STORAGE_NAME, 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      db.createObjectStore("lists", { keyPath: "entry_id" });
      db.createObjectStore("operations", { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

let localUpdates = Promise.resolve();

function withLocalState(update) {
  const result = localUpdates.then(update, update);
  localUpdates = result;
  return result;
}

function storeRequest(storeName, method, value) {
  return new Promise((resolve, reject) => {
    const transaction = database.transaction(storeName, "readwrite");
    const store = transaction.objectStore(storeName);
    const request = value === undefined ? store[method](entryId) : store[method](value);
    transaction.oncomplete = () => resolve(request.result);
    transaction.onabort = () => reject(transaction.error || request.error ||
      new Error("Die lokale Änderung konnte nicht gespeichert werden."));
    transaction.onerror = () => reject(transaction.error || request.error ||
      new Error("Der lokale Speicher ist nicht verfügbar."));
  });
}

async function saveList(snapshot) {
  await withLocalState(() => storeRequest("lists", "put", snapshot));
}

async function readQueue(listId = entryId) {
  return new Promise((resolve, reject) => {
    const request = database.transaction("operations").objectStore("operations").getAll();
    request.onsuccess = () => {
      resolve(
        request.result
          .filter((operation) => operation.entry_id === listId)
          .sort((a, b) => a.created_at - b.created_at || a.id.localeCompare(b.id)),
      );
    };
    request.onerror = () => reject(request.error);
  });
}

async function enqueue(operation, listId = entryId) {
  if (!listId) throw new Error("Bitte wähle zuerst eine Einkaufsliste aus.");
  const queued = {
    ...operation,
    id: crypto.randomUUID(),
    entry_id: listId,
    created_at: (lastOperationTime = Math.max(Date.now(), lastOperationTime + 1)),
  };
  await withLocalState(async () => {
    await storeRequest("operations", "put", queued);
    if (entryId === listId) {
      pendingOperations.push(queued);
      applyLocalOperation(queued);
      render();
      updateConnection("pending");
    }
  });
  if (authenticated) scheduleSynchronization();
}

function applyLocalOperation(operation) {
  if (deletedUids.has(operation.uid)) return;
  if (operation.type === "add_item") {
    if (!currentItems.some((item) => item.uid === operation.uid)) {
      currentItems.push({
        uid: operation.uid,
        summary: operation.summary,
        status: "needs_action",
      });
    }
  } else if (operation.type === "update_item") {
    const changes = {};
    for (const field of ["status", "summary", "description", "due"]) {
      if (operation[field] !== undefined) changes[field] = operation[field];
    }
    currentItems = currentItems.map((item) =>
      item.uid === operation.uid ? {
        ...item, ...changes,
        ...(operation.metadata ? { metadata: { ...item.metadata, ...operation.metadata } } : {}),
      } : item,
    );
  } else if (operation.type === "delete_item") {
    currentItems = currentItems.filter((item) => item.uid !== operation.uid);
  }
}

function enableItemSwipeDelete(row, uid, listId = entryId) {
  let pointer = null;
  let suppressClick = false;
  row.addEventListener("click", event => {
    if (!suppressClick) return;
    suppressClick = false;
    event.preventDefault();
    event.stopPropagation();
  }, true);
  row.addEventListener("pointerdown", event => {
    if (busy || event.button !== 0 || row.classList.contains("swipe-removing")) return;
    pointer = { id: event.pointerId, x: event.clientX, y: event.clientY, horizontal: false };
  });
  row.addEventListener("pointermove", event => {
    if (!pointer || pointer.id !== event.pointerId) return;
    const deltaX = event.clientX - pointer.x;
    const deltaY = event.clientY - pointer.y;
    if (!pointer.horizontal) {
      if (Math.max(Math.abs(deltaX), Math.abs(deltaY)) < 10) return;
      if (Math.abs(deltaY) >= Math.abs(deltaX) || deltaX >= 0) {
        pointer = null;
        return;
      }
      pointer.horizontal = true;
      row.classList.add("swiping");
    }
    event.preventDefault();
    row.style.transform = `translateX(${Math.max(deltaX, -row.clientWidth)}px)`;
  });
  row.addEventListener("pointerup", event => {
    if (!pointer || pointer.id !== event.pointerId) return;
    const shouldDelete = pointer.horizontal && event.clientX - pointer.x <= -72;
    pointer = null;
    row.classList.remove("swiping");
    row.style.transform = "";
    if (!shouldDelete) return;
    suppressClick = true;
    window.setTimeout(() => { suppressClick = false; }, 0);
    row.classList.add("swipe-removing");
    window.setTimeout(() => {
      enqueue({ type: "delete_item", uid }, listId).catch(error => {
        showError(error);
        row.classList.remove("swipe-removing");
        row.style.transform = "";
      });
    }, 180);
  });
  row.addEventListener("pointercancel", () => {
    pointer = null;
    row.classList.remove("swiping");
    row.style.transform = "";
  });
}

function render() {
  const pendingIds = new Set(
    pendingOperations.map((operation) => operation.uid),
  );
  elements.items.replaceChildren();
  const order = supermarkets.find(market => market.id === selectedMarket)?.category_ids || [];
  const sortedCategories = [...categories].sort((a, b) => {
    const ai = order.indexOf(a.id), bi = order.indexOf(b.id);
    if (ai >= 0 || bi >= 0) return (ai < 0 ? Infinity : ai) - (bi < 0 ? Infinity : bi);
    return nameOrder.compare(a.name, b.name);
  });
  const groupLists = new Map();
  for (const category of [...sortedCategories, { id: "", name: "Ohne Kategorie" }]) {
    const matches = currentItems.filter(item => {
      const id = item.metadata?.category_id;
      return category.id ? id === category.id : !categories.some(c => c.id === id);
    });
    if (!matches.length) continue;
    const group = document.createElement("li");
    group.className = "item-category";
    const heading = document.createElement("h2");
    heading.className = "item-category-title";
    heading.textContent = category.name;
    const count = document.createElement("span");
    count.textContent = String(matches.length);
    count.className = "category-count";
    heading.append(count);
    const list = document.createElement("ul");
    list.className = "items category-items";
    group.append(heading, list);
    elements.items.append(group);
    groupLists.set(category.id, list);
  }
  for (const item of currentItems) {
    const row = document.createElement("li");
    row.className = `item${item.status === "completed" ? " completed" : ""}`;
    const main = document.createElement("div");
    main.className = "item-main";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = item.status === "completed";
    checkbox.setAttribute("aria-label", `Erledigt: ${item.summary}`);
    checkbox.addEventListener("change", () => {
      enqueue({
        type: "update_item",
        uid: item.uid,
        status: checkbox.checked ? "completed" : "needs_action",
      }).catch(showError);
    });
    const label = document.createElement("button");
    label.type = "button";
    label.className = "item-name";
    const summary = document.createElement("span");
    summary.textContent = item.summary;
    label.append(summary);
    const details = [item.metadata?.quantity, item.description].filter(Boolean).join(" · ");
    if (details) {
      const note = document.createElement("span");
      note.className = "item-note";
      note.textContent = details;
      label.append(note);
      label.classList.add("has-note");
    }
    label.setAttribute("aria-label", `Bearbeiten: ${item.summary}`);
    label.setAttribute("aria-description", "Zum Löschen nach links wischen oder die Entf-Taste drücken.");
    label.setAttribute("aria-keyshortcuts", "Delete");
    label.addEventListener("click", () => {
      editingUid = item.uid;
      elements.editSummary.value = item.summary;
      elements.editQuantity.value = item.metadata?.quantity || "";
      elements.editNotes.value = item.description || "";
      elements.editCategory.replaceChildren(new Option("Ohne Kategorie", ""));
      for (const category of [...categories].sort((a, b) => nameOrder.compare(a.name, b.name))) {
        elements.editCategory.append(new Option(category.name, category.id));
      }
      const categoryId = item.metadata?.category_id || "";
      if (categoryId && !categories.some(c => c.id === categoryId)) {
        elements.editCategory.append(new Option("Nicht verfügbare Kategorie", categoryId));
      }
      elements.editCategory.value = categoryId;
      elements.editItem.showModal();
    });
    label.addEventListener("keydown", event => {
      if (event.key !== "Delete" || !confirm(`„${item.summary}“ wirklich löschen?`)) return;
      event.preventDefault();
      enqueue({ type: "delete_item", uid: item.uid }).catch(showError);
    });
    if (pendingIds.has(item.uid)) label.title = "Lokal gespeichert – Übertragung an Home Assistant ausstehend";
    main.append(checkbox, label);
    row.append(main);
    enableItemSwipeDelete(row, item.uid);
    const categoryId = categories.some(c => c.id === item.metadata?.category_id) ? item.metadata.category_id : "";
    groupLists.get(categoryId).append(row);
  }
  elements.empty.hidden = currentItems.length > 0;
  elements.syncDetail.textContent = pendingOperations.length
    ? `${pendingOperations.length} Änderung${pendingOperations.length === 1 ? "" : "en"} ausstehend`
    : syncPromise ? "Listen werden im Hintergrund abgeglichen. Du kannst weiter einkaufen."
      : "Liste ist auf diesem Gerät gespeichert.";
  setBusy(busy);
}

function setBusy(value) {
  busy = value;
  const blocked = value;
  elements.listSelect.disabled = blocked || !availableLists.length;
  if (elements.listSelect.disabled) closeFlyout(elements.listSelect, elements.listFlyout);
  elements.marketSelect.disabled = blocked || !entryId;
  if (elements.marketSelect.disabled) closeFlyout(elements.marketSelect, elements.marketFlyout);
  elements.addForm.inert = blocked || !entryId;
  elements.sync.disabled = blocked || !!syncPromise || !!listRefreshPromise;
  elements.copySource.disabled = blocked || !!syncPromise || !entryId;
  elements.items.inert = blocked;
  elements.manageLists.disabled = blocked;
}

function renderListSelection() {
  elements.listFlyout.replaceChildren();
  const lists = [...availableLists];
  if (entryId && !lists.some((list) => list.entry_id === entryId)) {
    lists.unshift({ entry_id: entryId, name: elements.listName.textContent });
  }
  for (const list of lists) {
    elements.listFlyout.append(createPickerOption(list.name, list.entry_id === entryId, () => {
      closeFlyout(elements.listSelect, elements.listFlyout, true);
      if (list.entry_id !== entryId) selectList(list.entry_id).catch(showError);
    }));
  }
  elements.listSelect.setAttribute("aria-label", `Einkaufsliste auswählen, aktuell ${elements.listName.textContent}`);
  setBusy(busy);
}

function createPickerOption(label, selected, onSelect) {
  const option = document.createElement("button");
  option.type = "button";
  option.className = "list-option";
  option.setAttribute("aria-pressed", String(selected));
  const name = document.createElement("span");
  name.className = "list-option-name";
  name.textContent = label;
  const check = document.createElement("span");
  check.className = "list-option-check";
  check.textContent = "✓";
  check.setAttribute("aria-hidden", "true");
  option.append(name, check);
  option.addEventListener("click", onSelect);
  return option;
}

function closeFlyout(trigger, flyout, focus = false) {
  flyout.hidden = true;
  trigger.setAttribute("aria-expanded", "false");
  if (focus) trigger.focus();
}

function initializePicker(trigger, flyout) {
  const container = trigger.parentElement.closest(".list-title, .market-picker");
  const close = (focus = false) => closeFlyout(trigger, flyout, focus);
  function open(focus = false) {
    if (trigger.disabled) return;
    for (const [otherTrigger, otherFlyout] of [
      [elements.listSelect, elements.listFlyout],
      [elements.marketSelect, elements.marketFlyout],
    ]) {
      if (otherFlyout !== flyout) closeFlyout(otherTrigger, otherFlyout);
    }
    elements.setup.open = false;
    flyout.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    if (focus) {
      (flyout.querySelector('[aria-pressed="true"]') ||
        flyout.querySelector("button"))?.focus();
    }
  }

  trigger.addEventListener("click", () => {
    if (flyout.hidden) open();
    else close();
  });
  trigger.addEventListener("keydown", (event) => {
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      open(true);
    }
  });
  flyout.addEventListener("keydown", (event) => {
    const options = [...flyout.querySelectorAll("button")];
    if (!["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key) || !options.length) return;
    event.preventDefault();
    const current = options.indexOf(document.activeElement);
    const next = event.key === "Home" ? 0 : event.key === "End" ? options.length - 1 :
      (current + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length;
    options[next].focus();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !flyout.hidden) {
      event.preventDefault();
      close(true);
    }
  });
  document.addEventListener("click", (event) => {
    if (!container.contains(event.target)) close();
  });
  container.addEventListener("focusout", (event) => {
    if (!container.contains(event.relatedTarget)) close();
  });
}

initializePicker(elements.listSelect, elements.listFlyout);
initializePicker(elements.marketSelect, elements.marketFlyout);

async function readCachedLists() {
  return new Promise((resolve, reject) => {
    const request = database.transaction("lists").objectStore("lists").getAll();
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function loadSelectedList() {
  const listId = entryId;
  await withLocalState(async () => {
    if (entryId !== listId) return;
    const cached = await storeRequest("lists", "get", listId);
    const operations = await readQueue(listId);
    if (entryId !== listId) return;
    deletedUids = new Set(cached?.deleted_uids || []);
    elements.listName.textContent = cached?.name ||
      availableLists.find((list) => list.entry_id === listId)?.name || "Liste laden";
    currentItems = cached?.items || [];
    pendingOperations = operations;
    for (const operation of pendingOperations) applyLocalOperation(operation);
    lastOperationTime = pendingOperations.reduce(
      (latest, operation) => Math.max(latest, operation.created_at), lastOperationTime,
    );
    render();
    renderListSelection();
    loadMarketSelection();
  });
}

async function selectList(listId) {
  if (busy) return;
  const previousEntry = entryId;
  setBusy(true);
  try {
    entryId = listId;
    await loadSelectedList();
    localStorage.setItem(ENTRY_KEY, entryId);
    const url = new URL(location.href);
    url.searchParams.set("entry_id", entryId);
    history.replaceState(null, "", url);
    elements.openAppBrowser.href = url.href;
    elements.message.textContent = "";
    updateConnection(pendingOperations.length ? "pending" : "offline");
  } catch (error) {
    entryId = previousEntry;
    await loadSelectedList();
    showError(error);
  } finally {
    setBusy(false);
  }
  synchronize().catch(showError);
}

elements.cancelEdit.addEventListener("click", () => elements.editItem.close());
elements.editItemForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const summary = elements.editSummary.value.trim();
  if (!summary) {
    elements.editSummary.setCustomValidity("Bitte gib einen Artikelnamen ein.");
    elements.editSummary.reportValidity();
    return;
  }
  try {
    await enqueue({
      type: "update_item", uid: editingUid, summary,
      description: elements.editNotes.value.trim() || null,
      metadata: {
        category_id: elements.editCategory.value || null,
        quantity: elements.editQuantity.value.trim() || null,
      },
    });
    elements.editItem.close();
  } catch (error) {
    showError(error);
    elements.editItem.close();
  }
});
elements.editSummary.addEventListener("input", () => elements.editSummary.setCustomValidity(""));

function updateConnection(state, detail) {
  elements.connectionDot.className = `dot ${state === "online" ? "online" : state === "pending" ? "pending" : ""}`;
  elements.connectionLabel.textContent =
    state === "online"
      ? "Mit Home Assistant verbunden"
      : state === "pending"
        ? "Synchronisierung ausstehend"
        : "Offline – lokale Liste";
  if (detail) elements.syncDetail.textContent = detail;
}

function showError(error) {
  elements.message.textContent = error instanceof Error ? error.message : String(error);
}

function readTokens() {
  try {
    const stored = localStorage.getItem(TOKEN_KEY);
    if (!stored) return null;
    const tokens = JSON.parse(stored);
    if (
      typeof tokens.access_token !== "string" ||
      typeof tokens.refresh_token !== "string" ||
      tokens.hassUrl !== location.origin ||
      tokens.clientId !== `${location.origin}/`
    ) return null;
    return tokens;
  } catch {
    return null;
  }
}

async function refreshTokenIfNeeded(tokens) {
  if (
    typeof tokens.expires !== "number" ||
    tokens.expires > Date.now() + 30000 ||
    typeof tokens.refresh_token !== "string"
  ) {
    return tokens;
  }
  const body = new FormData();
  body.set("grant_type", "refresh_token");
  body.set("refresh_token", tokens.refresh_token);
  if (tokens.clientId) body.set("client_id", tokens.clientId);
  const controller = new AbortController();
  const generation = connectionGeneration;
  const timeout = window.setTimeout(() => controller.abort(), 15000);
  let response;
  try {
    response = await fetch(`${tokens.hassUrl}/auth/token`, {
      method: "POST",
      credentials: "same-origin",
      body,
      signal: controller.signal,
    });
  } finally {
    window.clearTimeout(timeout);
  }
  if (generation !== connectionGeneration) throw new Error("Die Anmeldung wurde während der Verbindungsprüfung geändert.");
  if (response.status === 400 || response.status === 401) {
    authenticationBlocked = true;
    throw new Error("Home Assistant hat die Anmeldung abgelehnt. Bitte erneut mit HA verbinden.");
  }
  if (!response.ok) throw new Error(`Home Assistant ist vorübergehend nicht erreichbar (HTTP ${response.status}).`);
  const refreshed = await response.json();
  if (generation !== connectionGeneration) throw new Error("Die Anmeldung wurde während der Verbindungsprüfung geändert.");
  if (
    typeof refreshed.access_token !== "string" ||
    !Number.isFinite(refreshed.expires_in)
  ) {
    throw new Error("Home Assistant hat ein ungültiges Token zurückgegeben.");
  }
  const next = {
    ...tokens,
    ...refreshed,
    expires: Date.now() + refreshed.expires_in * 1000,
    refresh_token: refreshed.refresh_token || tokens.refresh_token,
  };
  localStorage.setItem(TOKEN_KEY, JSON.stringify(next));
  return next;
}

function base64UrlEncode(bytes) {
  return btoa(String.fromCharCode(...bytes))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}

async function connectHomeAssistant() {
  if (window.top !== window) {
    const appUrl = new URL(location.href);
    for (const key of ["code", "state", "error", "auth_callback"]) {
      appUrl.searchParams.delete(key);
    }
    appUrl.hash = "";
    appUrl.searchParams.set("connect_ha", "1");
    // HA reads OAuth parameters from the top-level window; its sandbox allows popups.
    const appWindow = window.open(appUrl.href, "_blank");
    if (!appWindow) {
      throw new Error("Bitte erlaube das Öffnen eines neuen Fensters für die HA-Anmeldung oder öffne die App über „App in eigenem Browserfenster öffnen / installieren“.");
    }
    appWindow.opener = null;
    elements.syncDetail.textContent = "Die HA-Anmeldung wurde in einem eigenen Browserfenster geöffnet. Bitte dort fortfahren.";
    return;
  }
  const hassUrl = location.origin;
  const clientId = `${hassUrl}/`;
  const redirectUrl = new URL(
    `${location.protocol}//${location.host}${location.pathname}${location.search}`,
  );
  redirectUrl.searchParams.set("auth_callback", "1");
  redirectUrl.searchParams.delete("code");
  redirectUrl.searchParams.delete("state");
  redirectUrl.searchParams.delete("error");
  redirectUrl.searchParams.delete("connect_ha");

  const nonce = base64UrlEncode(crypto.getRandomValues(new Uint8Array(32)));
  const state = { hassUrl, clientId, nonce };
  let codeChallenge;
  const metadataResponse = await fetch(`${hassUrl}/.well-known/oauth-authorization-server`);
  if (metadataResponse.ok) {
    const metadata = await metadataResponse.json();
    if (metadata.code_challenge_methods_supported?.includes("S256")) {
      const verifier = base64UrlEncode(crypto.getRandomValues(new Uint8Array(64)));
      const digest = await crypto.subtle.digest(
        "SHA-256",
        new TextEncoder().encode(verifier),
      );
      codeChallenge = base64UrlEncode(new Uint8Array(digest));
      sessionStorage.setItem(`${OAUTH_STATE_PREFIX}${nonce}`, JSON.stringify({ verifier }));
    }
  }

  const encodedState = btoa(JSON.stringify(state));
  const stored = JSON.parse(
    sessionStorage.getItem(`${OAUTH_STATE_PREFIX}${nonce}`) || "{}",
  );
  sessionStorage.setItem(
    `${OAUTH_STATE_PREFIX}${nonce}`,
    JSON.stringify({ ...stored, state: encodedState }),
  );
  const authorization = new URL(`${hassUrl}/auth/authorize`);
  authorization.searchParams.set("response_type", "code");
  authorization.searchParams.set("redirect_uri", redirectUrl.toString());
  authorization.searchParams.set("client_id", clientId);
  authorization.searchParams.set("state", encodedState);
  if (codeChallenge) {
    authorization.searchParams.set("code_challenge", codeChallenge);
    authorization.searchParams.set("code_challenge_method", "S256");
  }
  location.assign(authorization);
}

async function completeAuthorization() {
  const params = new URLSearchParams(location.search);
  if (params.has("error")) {
    history.replaceState(null, "", location.pathname);
    throw new Error("Die Home-Assistant-Anmeldung wurde abgebrochen oder abgelehnt.");
  }
  const code = params.get("code");
  const encodedState = params.get("state");
  if (!code || !encodedState || !params.has("auth_callback")) return;

  const state = JSON.parse(atob(encodedState));
  const key = `${OAUTH_STATE_PREFIX}${state.nonce}`;
  const stored = JSON.parse(sessionStorage.getItem(key) || "null");
  sessionStorage.removeItem(key);
  if (
    !stored ||
    stored.state !== encodedState ||
    state.hassUrl !== location.origin ||
    state.clientId !== `${location.origin}/`
  ) throw new Error("HA-Anmeldung konnte nicht geprüft werden.");
  history.replaceState(
    null,
    "",
    `${location.pathname}${params.get("entry_id") ? `?entry_id=${encodeURIComponent(params.get("entry_id"))}` : ""}`,
  );

  const body = new FormData();
  body.set("grant_type", "authorization_code");
  body.set("code", code);
  body.set("client_id", state.clientId);
  if (stored.verifier) body.set("code_verifier", stored.verifier);
  const response = await fetch(`${state.hassUrl}/auth/token`, {
    method: "POST",
    credentials: "same-origin",
    body,
  });
  if (!response.ok) throw new Error("Home Assistant hat die Anmeldung abgelehnt.");
  const received = await response.json();
  if (
    typeof received.access_token !== "string" ||
    typeof received.refresh_token !== "string" ||
    !Number.isFinite(received.expires_in)
  ) {
    throw new Error("Home Assistant hat ein ungültiges Token zurückgegeben.");
  }
  const tokens = {
    ...received,
    hassUrl: state.hassUrl,
    clientId: state.clientId,
    expires: Date.now() + received.expires_in * 1000,
  };
  localStorage.setItem(TOKEN_KEY, JSON.stringify(tokens));
}

function scheduleReconnect() {
  if (reconnectTimer || authenticationBlocked || !navigator.onLine) return;
  const delay = Math.min(1000 * 2 ** Math.min(reconnectAttempts++, 5), 30000);
  reconnectTimer = window.setTimeout(() => {
    reconnectTimer = undefined;
    connect();
  }, delay);
}

function disconnect(detail) {
  window.clearTimeout(connectionTimer);
  window.clearTimeout(connectionSyncTimer);
  window.clearTimeout(heartbeatTimer);
  heartbeatId = undefined;
  authenticated = false;
  const previous = socket;
  socket = undefined;
  if (previous && previous.readyState < WebSocket.CLOSING) previous.close();
  for (const waiter of waiters.values()) {
    window.clearTimeout(waiter.timer);
    waiter.reject(new Error("Die Verbindung zu Home Assistant wurde unterbrochen. Änderungen bleiben lokal vorgemerkt."));
  }
  waiters.clear();
  updateConnection(pendingOperations.length ? "pending" : "offline", detail);
}

function checkConnection() {
  if (!authenticated || socket?.readyState !== WebSocket.OPEN || heartbeatId !== undefined) return;
  window.clearTimeout(heartbeatTimer);
  heartbeatId = nextMessageId++;
  socket.send(JSON.stringify({ id: heartbeatId, type: "ping" }));
  heartbeatTimer = window.setTimeout(() => {
    disconnect("Home Assistant antwortet nicht. Die Verbindung wird automatisch wiederhergestellt.");
    scheduleReconnect();
  }, 15000);
}

async function connect() {
  if (!database || !navigator.onLine || connecting || authenticationBlocked ||
      (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING))) return;
  window.clearTimeout(reconnectTimer);
  reconnectTimer = undefined;
  let tokens = readTokens();
  if (!tokens) {
    updateConnection(
      pendingOperations.length ? "pending" : "offline",
      "Verbinde die App einmal online mit Home Assistant, damit die Liste geladen wird.",
    );
    elements.connect.hidden = false;
    return;
  }
  elements.connect.hidden = true;
  connecting = true;
  const generation = connectionGeneration;
  try {
    tokens = await refreshTokenIfNeeded(refreshAfterRejection ? { ...tokens, expires: 0 } : tokens);
  } catch (error) {
    updateConnection(pendingOperations.length ? "pending" : "offline",
      authenticationBlocked ? error.message : `Verbindung wird automatisch erneut versucht: ${error.message}`);
    elements.connect.hidden = !authenticationBlocked;
    scheduleReconnect();
    return;
  } finally {
    connecting = false;
  }
  if (generation !== connectionGeneration || !navigator.onLine) {
    scheduleReconnect();
    return;
  }

  const scheme = location.protocol === "https:" ? "wss:" : "ws:";
  const currentSocket = new WebSocket(`${scheme}//${location.host}/api/websocket`);
  socket = currentSocket;
  connectionTimer = window.setTimeout(() => {
    if (socket !== currentSocket) return;
    disconnect("Home Assistant ist nicht erreichbar. Die Verbindung wird automatisch erneut versucht.");
    scheduleReconnect();
  }, 15000);
  currentSocket.addEventListener("message", (event) => {
    if (socket !== currentSocket) return;
    const message = JSON.parse(event.data);
    if (message.type === "auth_required") {
      currentSocket.send(JSON.stringify({ type: "auth", access_token: tokens.access_token }));
    } else if (message.type === "auth_ok") {
      window.clearTimeout(connectionTimer);
      authenticated = true;
      refreshAfterRejection = false;
      reconnectAttempts = 0;
      updateConnection("online", "Verbindung hergestellt. Listen werden synchronisiert.");
      heartbeatTimer = window.setTimeout(checkConnection, 30000);
      const synchronizeWhenIdle = () => {
        if (socket !== currentSocket || !authenticated) return;
        if (busy) {
          connectionSyncTimer = window.setTimeout(synchronizeWhenIdle, 250);
        } else {
          loadRemoteLists().catch(showError);
        }
      };
      synchronizeWhenIdle();
    } else if (message.type === "auth_invalid") {
      authenticationBlocked = refreshAfterRejection;
      refreshAfterRejection = true;
      elements.connect.hidden = !authenticationBlocked;
      disconnect(authenticationBlocked
        ? "Home Assistant hat die Anmeldung abgelehnt. Bitte erneut mit HA verbinden."
        : "Die Anmeldung wird automatisch erneuert.");
      scheduleReconnect();
    } else if (message.type === "pong" && message.id === heartbeatId) {
      heartbeatId = undefined;
      window.clearTimeout(heartbeatTimer);
      heartbeatTimer = window.setTimeout(checkConnection, 30000);
    } else if (message.type === "result") {
      const waiter = waiters.get(message.id);
      if (waiter) {
        waiters.delete(message.id);
        window.clearTimeout(waiter.timer);
        if (message.success) waiter.resolve(message.result);
        else waiter.reject(new Error(message.error?.message || "Synchronisierung fehlgeschlagen."));
      }
    }
  });
  currentSocket.addEventListener("close", () => {
    if (socket !== currentSocket) return;
    disconnect("Verbindung unterbrochen. Die App verbindet sich automatisch erneut.");
    scheduleReconnect();
  });
  currentSocket.addEventListener("error", () => {
    if (socket !== currentSocket) return;
    disconnect("Home Assistant ist nicht erreichbar. Die App verbindet sich automatisch erneut.");
    scheduleReconnect();
  });
}

const waiters = new Map();

document.addEventListener("click", (event) => {
  if (!elements.setup.contains(event.target)) elements.setup.open = false;
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && elements.setup.open) {
    const section = event.target.closest(".setup-section[open]");
    if (section) {
      event.preventDefault();
      section.open = false;
      section.querySelector("summary").focus();
      return;
    }
    elements.setup.open = false;
    elements.setup.querySelector("summary").focus();
  }
});
elements.setup.addEventListener("click", (event) => {
  if (event.target.closest("button, a") && !event.target.closest("#menu-design")) {
    elements.setup.open = false;
    elements.setup.querySelector("summary").focus();
  }
});

elements.connect.addEventListener("click", () => {
  connectHomeAssistant().catch(showError);
});

function sendCommand(type, payload = {}) {
  if (!authenticated || socket?.readyState !== WebSocket.OPEN) {
    return Promise.reject(new Error("Home Assistant ist gerade nicht erreichbar."));
  }
  const id = nextMessageId++;
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => {
      const waiter = waiters.get(id);
      if (waiter) {
        waiters.delete(id);
        reject(new Error("Zeitüberschreitung bei der Synchronisierung."));
      }
    }, 15000);
    waiters.set(id, { resolve, reject, timer });
    socket.send(JSON.stringify({ id, type, ...payload }));
  });
}

function scheduleSynchronization() {
  syncRequested = true;
  if (syncPromise || syncTimer !== undefined || !authenticated) return;
  syncTimer = window.setTimeout(() => {
    syncTimer = undefined;
    if (busy) {
      scheduleSynchronization();
      return;
    }
    synchronize({ full: false }).catch(showError);
  }, 150);
}

async function synchronize({ full = true } = {}) {
  syncRequested = true;
  fullSyncRequested = fullSyncRequested || full;
  if (syncPromise) return syncPromise;
  if (busy || !authenticated || socket?.readyState !== WebSocket.OPEN || !entryId) return;
  window.clearTimeout(syncTimer);
  syncTimer = undefined;
  syncPromise = runSynchronization();
  setBusy(busy);
  let completed = false;
  try {
    await syncPromise;
    completed = true;
  } finally {
    syncPromise = undefined;
    setBusy(busy);
    if (completed && syncRequested) scheduleSynchronization();
  }
}

async function runSynchronization() {
  const warnings = [];
  const sourceWarnings = new Map();
  updateConnection(pendingOperations.length ? "pending" : "online",
    "Listen werden im Hintergrund abgeglichen. Du kannst weiter einkaufen.");
  try {
    do {
      const full = fullSyncRequested;
      syncRequested = false;
      fullSyncRequested = false;
      const ids = new Set([entryId, ...availableLists.map((list) => list.entry_id)]);
      for (const listId of ids) {
        if (!listId) continue;
        const operations = await readQueue(listId);
        if (!full && !operations.length) continue;
        if (full) {
          await saveList(await sendCommand(`${DOMAIN}/get_list`, { entry_id: listId }));
        }
        for (const operation of operations) {
          const changes = {};
          for (const field of ["summary", "status", "description", "due", "metadata"]) {
            if (operation[field] !== undefined) changes[field] = operation[field];
          }
          const snapshot = await sendCommand(`${DOMAIN}/apply_operation`, {
            entry_id: listId, operation_id: operation.id,
            action: operation.type, uid: operation.uid, changes,
          });
          if (snapshot.ack_operation_id !== operation.id || snapshot.entry_id !== listId ||
              !Number.isSafeInteger(snapshot.revision) || snapshot.revision < 0 ||
              !Array.isArray(snapshot.items) ||
              !["applied", "already_exists", "deleted"].includes(snapshot.operation_result)) {
            throw new Error("Die Synchronisationsbestätigung passt nicht zur gesendeten Änderung.");
          }
          await acknowledgeOperation(snapshot, operation.id);
          if (snapshot.operation_result === "deleted") {
            warnings.push("Eine Änderung an einem bereits gelöschten Artikel wurde verworfen.");
          }
        }
        const snapshot = await sendCommand(`${DOMAIN}/sync_source`, { entry_id: listId });
        await saveList(snapshot);
        if (snapshot.source_error) sourceWarnings.set(listId, `${snapshot.name}: ${snapshot.source_error}`);
        else sourceWarnings.delete(listId);
      }
    } while (syncRequested && !busy && authenticated && socket?.readyState === WebSocket.OPEN);
  } finally {
    await loadSelectedList();
    await refreshSyncConflicts();
  }
  warnings.push(...sourceWarnings.values());
  const decisions = syncConflicts.filter(conflict => !conflict.local_only).length;
  const localItems = syncConflicts.filter(conflict => conflict.local_only).length;
  updateConnection(pendingOperations.length ? "pending" : "online", pendingOperations.length
    ? `${pendingOperations.length} Änderungen lokal gespeichert – Übertragung ausstehend.`
    : decisions
    ? `In Home Assistant gespeichert. Für ${decisions} Artikel ist noch eine Entscheidung nötig.`
    : warnings.length
      ? "In Home Assistant gespeichert. Der Abgleich mit einer verbundenen Liste ist noch nicht vollständig."
      : localItems
        ? `Abgleich abgeschlossen. ${localItems} Artikel bleiben nur in der App-Liste.`
        : "App und verbundene Listen sind abgeglichen.");
  elements.message.textContent = [...new Set(warnings)].join(" ");
}

let syncConflicts = [];
const promptedSyncConflicts = new Set();

async function refreshSyncConflicts() {
  const previous = JSON.stringify(syncConflicts);
  const enabledIds = new Set(availableLists.map(list => list.entry_id));
  syncConflicts = (await readCachedLists())
    .filter(list => list.enabled !== false && enabledIds.has(list.entry_id))
    .flatMap(list => [...(list.source_conflicts || []), ...(list.source_local_items || [])]
      .filter(conflict => !(conflict.local_only && conflict.deleted)).map(conflict => ({
      ...conflict, entry_id: list.entry_id, list_name: list.name,
    })));
  elements.resolveSyncConflicts.hidden = !syncConflicts.length;
  const activeConflicts = syncConflicts.filter(conflict => !conflict.local_only).length;
  elements.resolveSyncConflicts.textContent = activeConflicts
    ? `Sync-Konflikte auflösen (${activeConflicts})`
    : `Nur lokale Artikel prüfen (${syncConflicts.length})`;
  if (elements.syncConflicts.open && previous !== JSON.stringify(syncConflicts)) {
    renderSyncConflicts();
    if (!syncConflicts.length) elements.syncConflicts.close();
  }
  if (syncConflicts.some(conflict => !conflict.local_only && !promptedSyncConflicts.has(conflict.token)) &&
      !document.querySelector("dialog[open]")) {
    openSyncConflicts();
  }
}

function openSyncConflicts() {
  elements.syncConflictsMessage.textContent = "";
  renderSyncConflicts();
  for (const conflict of syncConflicts) promptedSyncConflicts.add(conflict.token);
  if (!elements.syncConflicts.open) elements.syncConflicts.showModal();
}

function renderSyncConflicts() {
  elements.syncConflictsContent.replaceChildren();
  for (const conflict of syncConflicts) {
    const section = document.createElement("section");
    const title = document.createElement("h3");
    title.textContent = `${conflict.list_name}: ${conflict.summary}${conflict.deleted ? " (gelöscht)" : ""}`;
    const detail = document.createElement("p");
    detail.textContent = conflict.reason === "multiple"
      ? `„${conflict.summary}“ ist in unserer App-Liste gespeichert. Mehrere neue Einträge in der verbundenen HA-/Alexa-Liste könnten dazugehören. Wir wählen keinen davon automatisch aus.`
      : `„${conflict.summary}“ ist in unserer App-Liste gespeichert. Ob derselbe Artikel auch in der verbundenen HA-/Alexa-Liste angekommen ist, wissen wir noch nicht. Das bedeutet nicht, dass er verloren ist.`;
    if (conflict.deleted) {
      detail.textContent = `Du hast „${conflict.summary}“ in unserer App-Liste gelöscht. Ein früherer Versuch, ihn in der verbundenen HA-/Alexa-Liste anzulegen, ist noch ungeklärt. Es könnte dort noch ein Eintrag übrig sein.`;
    }
    detail.textContent += conflict.candidates.length
      ? " Unten stehen noch nicht verknüpfte Einträge dieser verbundenen Liste. Wähle nur einen Eintrag, der wirklich dazugehört."
      : " Aktuell wurde dort kein noch nicht verknüpfter Eintrag gefunden. Du kannst später erneut prüfen.";
    if (conflict.local_only) {
      detail.textContent = `„${conflict.summary}“ bleibt nur lokal: Er ist in unserer App-Liste und in Home Assistant gespeichert, wird aber nicht mit einem Eintrag der verbundenen HA-/Alexa-Liste abgeglichen. Deine anderen Geräte sehen ihn weiterhin. Hier kannst du diese Entscheidung ändern.`;
    }
    const select = document.createElement("select");
    select.setAttribute("aria-label", `Quellartikel für ${conflict.summary}`);
    select.add(new Option("Quellartikel auswählen", ""));
    for (const [index, candidate] of conflict.candidates.entries()) {
      select.add(new Option(
        `${candidate.summary} – ${candidate.status === "completed" ? "erledigt" : "offen"} (Eintrag ${index + 1})`,
        candidate.uid,
      ));
    }
    const actions = document.createElement("div");
    actions.className = "dialog-actions";
    for (const [action, label, explanation] of [
      ["link", conflict.deleted ? "Gewählten Eintrag löschen" : "Quellartikel zuordnen",
        conflict.deleted
          ? `Beispiel: „${conflict.summary}“ steht noch in Alexa, obwohl du ihn hier gelöscht hast. Nur der oben ausgewählte Eintrag wird dort gelöscht.`
          : `Beispiel: „${conflict.summary}“ steht schon in Alexa. Wähle diesen Eintrag oben aus. Er wird mit unserem Artikel verbunden, statt einen zweiten anzulegen. Name und Erledigt-Status aus unserer App werden übernommen; Notizen und Kategorie bleiben erhalten.`],
      ["retry", "Bewusst erneut anlegen",
        conflict.deleted
          ? "Nicht möglich: Der Artikel wurde hier bereits gelöscht."
          : `Beispiel: „${conflict.summary}“ fehlt auch nach erneutem Prüfen in Alexa. Ein neuer Eintrag wird angelegt. Falls er dort doch schon existiert, entsteht möglicherweise ein Duplikat.`],
      ["local", conflict.deleted ? "Löschung hier abschließen" : "Nur lokal behalten",
        conflict.deleted
          ? "Der Artikel bleibt hier gelöscht. In der verbundenen Liste wird nichts geändert. Diese Rückfrage wird abgeschlossen."
          : `„${conflict.summary}“ bleibt in unserer App-Liste für alle Geräte erhalten. In der verbundenen HA-/Alexa-Liste wird nichts angelegt oder geändert. Ein eventuell schon vorhandener Eintrag dort bleibt unabhängig bestehen.`],
    ]) {
      const choice = document.createElement("div");
      choice.className = "sync-conflict-choice";
      const help = document.createElement("p");
      help.textContent = explanation;
      const button = document.createElement("button");
      button.type = "button";
      button.className = "secondary";
      button.textContent = label;
      button.disabled = (action === "link" && !conflict.candidates.length) ||
        (action === "retry" && conflict.deleted) || (action === "local" && conflict.local_only);
      button.addEventListener("click", () => {
        if (action === "link" && !select.value) {
          elements.syncConflictsMessage.textContent = "Bitte zuerst einen Quellartikel auswählen.";
          return;
        }
        if (action === "retry" && !confirm(
          `„${conflict.summary}“ wirklich erneut in der Quelle anlegen? Falls der erste Versuch bereits erfolgreich war, kann ein Duplikat entstehen.`,
        )) return;
        if (action === "link" && !confirm(
          conflict.deleted
            ? `„${select.selectedOptions[0].textContent}“ wirklich aus der verbundenen HA-/Alexa-Liste löschen? „${conflict.summary}“ bleibt hier gelöscht.`
            : `„${conflict.summary}“ mit „${select.selectedOptions[0].textContent}“ verbinden? Name und Erledigt-Status aus unserer App-Liste werden übernommen. Notizen und Kategorie bleiben erhalten.`,
        )) return;
        resolveSyncConflict(conflict, action, select.value).catch(error => {
          elements.syncConflictsMessage.textContent = error.message;
          if (!elements.syncConflicts.open) showError(error);
        });
      });
      choice.append(button, help);
      actions.append(choice);
    }
    section.append(title, detail, select, actions);
    elements.syncConflictsContent.append(section);
  }
}

async function resolveSyncConflict(conflict, action, sourceUid) {
  if (busy) throw new Error("Bitte warte, bis die Synchronisierung abgeschlossen ist.");
  setBusy(true);
  elements.syncConflictsContent.inert = true;
  elements.syncConflictsMessage.textContent = "Entscheidung wird in HA gespeichert …";
  try {
    if (syncPromise) await syncPromise;
    const snapshot = await sendCommand(`${DOMAIN}/resolve_source_conflict`, {
      entry_id: conflict.entry_id, uid: conflict.uid, token: conflict.token, action,
      ...(action === "link" ? { source_uid: sourceUid } : {}),
    });
    await saveList(snapshot);
    await refreshSyncConflicts();
    renderSyncConflicts();
    elements.syncConflictsMessage.textContent = action === "local"
      ? conflict.deleted
        ? "Die Rückfrage ist abgeschlossen. Der Artikel bleibt hier gelöscht; die verbundene Liste wurde nicht verändert."
        : "Der Artikel bleibt für alle Geräte in unserer App-Liste gespeichert. Die verbundene HA-/Alexa-Liste wird für diesen Artikel nicht verändert."
      : "Entscheidung gespeichert. Der Abgleich wird fortgesetzt.";
    if (!syncConflicts.length) elements.syncConflicts.close();
  } finally {
    elements.syncConflictsContent.inert = false;
    setBusy(false);
  }
  await synchronize();
}

elements.resolveSyncConflicts.addEventListener("click", openSyncConflicts);

async function acknowledgeOperation(snapshot, operationId) {
  return withLocalState(() => new Promise((resolve, reject) => {
    const transaction = database.transaction(["lists", "operations"], "readwrite");
    transaction.objectStore("lists").put(snapshot);
    transaction.objectStore("operations").delete(operationId);
    transaction.oncomplete = resolve;
    transaction.onabort = transaction.onerror = () => reject(
      transaction.error || new Error("Die Synchronisationsbestätigung konnte nicht gespeichert werden."),
    );
  }));
}

async function loadRemoteLists() {
  if (busy) throw new Error("Bitte warte, bis die aktuelle Aktion abgeschlossen ist, und synchronisiere erneut.");
  if (listRefreshPromise) return listRefreshPromise;
  listRefreshPromise = refreshRemoteLists();
  setBusy(busy);
  try {
    await listRefreshPromise;
  } finally {
    listRefreshPromise = undefined;
    setBusy(busy);
  }
}

async function refreshRemoteLists() {
  if (syncPromise) await syncPromise;
  let marketError;
  try {
    try {
      await refreshSupermarkets();
    } catch (error) {
      marketError = error;
    }
    const lists = await sendCommand(`${DOMAIN}/get_lists`);
    await withLocalState(async () => {
      for (const cached of await readCachedLists()) {
        const listed = lists.find((list) => list.entry_id === cached.entry_id);
        await storeRequest("lists", "put", { ...cached, enabled: !!listed, name: listed?.name || cached.name });
      }
    });
    availableLists = lists;
    if (!lists.some((list) => list.entry_id === entryId)) {
      entryId = lists[0]?.entry_id || null;
      if (entryId) localStorage.setItem(ENTRY_KEY, entryId);
      else localStorage.removeItem(ENTRY_KEY);
      const url = new URL(location.href);
      if (entryId) url.searchParams.set("entry_id", entryId);
      else url.searchParams.delete("entry_id");
      history.replaceState(null, "", url);
      elements.openAppBrowser.href = url.href;
      currentItems = [];
      pendingOperations = [];
      render();
      if (entryId) await loadSelectedList();
    }
    renderListSelection();
    loadMarketSelection();
    if (!lists.length) {
      currentItems = [];
      pendingOperations = [];
      elements.listName.textContent = "Liste auswählen";
      render();
      elements.message.textContent = marketError
        ? marketError.message : "Wähle unter Setup → Listen verwalten eine HA-Liste aus.";
      return;
    }
    await synchronize();
  } finally {
    if (marketError) showError(marketError);
  }
}

elements.manageLists.addEventListener("click", async () => {
  showManagementPage(elements.listManagement);
  document.querySelector("#list-management-title").focus();
  elements.managementMessage.textContent = "HA-Listen werden geladen …";
  elements.sourceLists.replaceChildren();
  try {
    const sources = await sendCommand(`${DOMAIN}/get_sources`);
    elements.managementMessage.textContent = sources.length
      ? "" : "Keine HA-To-do-Listen gefunden. Lege eine Liste über Alexa an und stelle sie in HA bereit.";
    for (const source of sources) {
      const form = document.createElement("form");
      form.className = "source-list";
      const label = document.createElement("label");
      const enabled = document.createElement("input");
      enabled.type = "checkbox";
      enabled.checked = source.enabled;
      label.append(enabled, document.createTextNode(source.source_name));
      const details = document.createElement("small");
      details.textContent = `${source.source_entity_id}${source.available ? "" : " – Quelle nicht verfügbar"}`;
      const nameLabel = document.createElement("label");
      const alias = document.createElement("input");
      alias.type = "text";
      alias.value = source.name;
      alias.required = true;
      alias.maxLength = 100;
      alias.setAttribute("aria-label", `Anzeigename: ${source.source_name}`);
      nameLabel.append(document.createTextNode("App-Name"), alias);
      const save = document.createElement("button");
      save.type = "submit";
      save.className = "primary";
      save.textContent = "Übernehmen";
      form.append(label, details, nameLabel, save);
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!alias.value.trim()) {
          alias.setCustomValidity("Bitte gib einen Anzeigenamen ein.");
          alias.reportValidity();
          return;
        }
        if (busy) {
          elements.managementMessage.textContent = "Bitte warte, bis die aktuelle Aktion abgeschlossen ist.";
          return;
        }
        elements.sourceLists.inert = true;
        setBusy(true);
        elements.managementMessage.textContent = "Wird gespeichert …";
        try {
          const result = await sendCommand(`${DOMAIN}/configure_list`, {
            source_entity_id: source.source_entity_id,
            name: alias.value.trim(),
            enabled: enabled.checked,
          });
          if (enabled.checked && result.entry_id) {
            let ready = false;
            for (let attempt = 0; attempt < 10; attempt++) {
              const lists = await sendCommand(`${DOMAIN}/get_lists`);
              if (lists.some((list) => list.entry_id === result.entry_id)) {
                ready = true;
                break;
              }
              await new Promise((resolve) => setTimeout(resolve, 500));
            }
            if (!ready) throw new Error("Liste gespeichert, aber noch nicht geladen. Prüfe die Integration in HA und synchronisiere erneut.");
          }
          setBusy(false);
          await loadRemoteLists();
          elements.managementMessage.textContent = "Gespeichert. Der App-Name gilt für alle Nutzer.";
        } catch (error) {
          elements.managementMessage.textContent = error.message;
        } finally {
          setBusy(false);
          elements.sourceLists.inert = false;
        }
      });
      alias.addEventListener("input", () => alias.setCustomValidity(""));
      elements.sourceLists.append(form);
    }
  } catch (error) {
    elements.managementMessage.textContent = error.message;
  }
});

elements.addForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const summary = elements.newItem.value.trim();
  if (!summary) return;
  elements.newItem.value = "";
  try {
    await enqueue({ type: "add_item", uid: crypto.randomUUID(), summary });
  } catch (error) {
    showError(error);
  }
});

elements.sync.addEventListener("click", () => {
  if (authenticated && socket?.readyState === WebSocket.OPEN) {
    loadRemoteLists().catch(showError);
  } else {
    connect();
  }
});

elements.copySource.addEventListener("click", async () => {
  if (busy) return;
  try {
    if (!authenticated) throw new Error("Home Assistant ist gerade nicht erreichbar.");
    await synchronize();
  } catch (error) {
    showError(error);
  }
});

function resumeConnection() {
  if (authenticated) checkConnection();
  else connect();
}

window.addEventListener("online", resumeConnection);
window.addEventListener("pageshow", resumeConnection);
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "visible") resumeConnection();
});
window.addEventListener("storage", (event) => {
  if (event.storageArea !== localStorage || (event.key !== TOKEN_KEY && event.key !== null)) return;
  connectionGeneration++;
  authenticationBlocked = false;
  refreshAfterRejection = false;
  reconnectAttempts = 0;
  disconnect("Die gespeicherte Anmeldung wurde geändert. Verbindung wird geprüft.");
  connect();
});
window.addEventListener("offline", () => {
  connectionGeneration++;
  window.clearTimeout(reconnectTimer);
  reconnectTimer = undefined;
  disconnect("Keine Netzwerkverbindung. Änderungen werden lokal gespeichert und später synchronisiert.");
});
window.addEventListener("beforeinstallprompt", (event) => {
  event.preventDefault();
  pendingInstallPrompt = event;
  elements.install.hidden = false;
});

elements.install.addEventListener("click", async () => {
  if (!pendingInstallPrompt) {
    elements.installHelp.showModal();
    return;
  }
  pendingInstallPrompt.prompt();
  await pendingInstallPrompt.userChoice;
  pendingInstallPrompt = null;
  elements.install.hidden = true;
});

async function start() {
  window.setInterval(() => {
    if (authenticated && !busy && document.visibilityState === "visible") {
      synchronize().catch(showError);
    }
  }, 30000);
  const appUrl = new URL(location.href);
  const startAuthorization = appUrl.searchParams.get("connect_ha") === "1";
  if (startAuthorization) {
    appUrl.searchParams.delete("connect_ha");
    history.replaceState(null, "", appUrl.href);
  }
  setBusy(true);
  elements.openHomeassistant.href = "/";
  elements.openAppBrowser.href = location.href;
  elements.openAppBrowser.hidden = false;
  try {
    database = await openDatabase();
    loadCachedSupermarkets();
    availableLists = (await readCachedLists())
      .filter((list) => list.enabled !== false)
      .map(({ entry_id, name }) => ({ entry_id, name }));
    if (!availableLists.some((list) => list.entry_id === entryId)) {
      entryId = availableLists[0]?.entry_id || null;
    }
    if (entryId) await loadSelectedList();
    else renderListSelection();
    updateConnection(pendingOperations.length ? "pending" : "offline");
    if ("serviceWorker" in navigator) {
      await navigator.serviceWorker.register("./service-worker.js", { scope: "./" });
    }
    try {
      await completeAuthorization();
    } catch (error) {
      showError(error);
    }
    setBusy(false);
    if (startAuthorization) {
      await connectHomeAssistant().catch(showError);
      return;
    }
    connect();
  } catch (error) {
    showError(error);
    elements.connectionLabel.textContent = "Lokaler Speicher nicht verfügbar";
  }
}

initializeDesign();
start();
