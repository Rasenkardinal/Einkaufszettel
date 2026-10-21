const STORAGE_NAME = "einkaufszettel-offline-v1";
const ENTRY_KEY = "einkaufszettel.entry_id";
const TOKEN_KEY = "einkaufszettel.auth";
const OAUTH_STATE_PREFIX = "einkaufszettel.oauth.";
const DOMAIN = "einkaufszettel";
const DESIGN_KEY = "einkaufszettel.design";
const MARKETS_KEY = "einkaufszettel.supermarkets";
const MARKET_SELECTION_PREFIX = "einkaufszettel.supermarket.";

const elements = {
  setup: document.querySelector("#setup"),
  marketSelect: document.querySelector("#market-select"),
  marketFlyout: document.querySelector("#market-flyout"),
  marketName: document.querySelector("#market-name"),
  manageSupermarkets: document.querySelector("#manage-supermarkets"),
  supermarketManagement: document.querySelector("#supermarket-management"),
  supermarketMessage: document.querySelector("#supermarket-message"),
  supermarketList: document.querySelector("#supermarket-list"),
  addSupermarketForm: document.querySelector("#add-supermarket-form"),
  supermarketNewName: document.querySelector("#supermarket-new-name"),
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
  listName: document.querySelector("#list-name"),
  listSelect: document.querySelector("#list-select"),
  listFlyout: document.querySelector("#list-flyout"),
  editItem: document.querySelector("#edit-item"),
  editItemForm: document.querySelector("#edit-item-form"),
  editSummary: document.querySelector("#edit-summary"),
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
let pendingOperations = [];
let busy = false;
let lastOperationTime = 0;
let availableLists = [];
let editingUid;
let supermarkets = [];
let selectedMarket = "";
let managingSupermarkets = false;

function validateSupermarkets(value) {
  if (!Array.isArray(value) || value.some(market =>
    !market || typeof market.id !== "string" || !market.id ||
    typeof market.name !== "string" || !market.name.trim() || market.name.length > 100
  ) || new Set(value.map(market => market.id)).size !== value.length) {
    throw new Error("Die Supermarktdaten sind ungültig. Bitte erneut mit Home Assistant verbinden.");
  }
  return value;
}

function renderMarketSelection() {
  elements.marketFlyout.replaceChildren();
  for (const market of [{ id: "", name: "Ohne Markt" }, ...supermarkets]) {
    elements.marketFlyout.append(createPickerOption(market.name, market.id === selectedMarket, () => {
      closeFlyout(elements.marketSelect, elements.marketFlyout, true);
      selectedMarket = market.id;
      renderMarketSelection();
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
    const cached = localStorage.getItem(MARKETS_KEY);
    if (cached) supermarkets = validateSupermarkets(JSON.parse(cached));
  } catch (error) {
    showError(error);
  }
  loadMarketSelection();
}

async function refreshSupermarkets() {
  supermarkets = validateSupermarkets(await sendCommand(`${DOMAIN}/get_supermarkets`));
  let cacheError;
  try {
    localStorage.setItem(MARKETS_KEY, JSON.stringify(supermarkets));
  } catch (error) {
    cacheError = new Error(`Supermärkte geladen, aber die Offline-Kopie konnte nicht gespeichert werden: ${error.message}`);
  }
  loadMarketSelection();
  renderSupermarketManagement();
  if (cacheError) throw cacheError;
}

async function changeSupermarket(command, payload) {
  if (managingSupermarkets) return;
  let changed = false;
  managingSupermarkets = true;
  elements.supermarketList.inert = true;
  elements.addSupermarketForm.inert = true;
  elements.supermarketMessage.textContent = "Wird gespeichert …";
  try {
    supermarkets = validateSupermarkets(await sendCommand(`${DOMAIN}/${command}`, payload));
    changed = true;
    elements.supermarketMessage.textContent = "In Home Assistant gespeichert.";
    try {
      localStorage.setItem(MARKETS_KEY, JSON.stringify(supermarkets));
    } catch (error) {
      throw new Error(`In Home Assistant gespeichert, aber die Offline-Kopie konnte nicht gespeichert werden: ${error.message}`);
    }
    elements.supermarketNewName.value = "";
  } catch (error) {
    elements.supermarketMessage.textContent = error.message;
  } finally {
    managingSupermarkets = false;
    elements.supermarketList.inert = false;
    elements.addSupermarketForm.inert = false;
    loadMarketSelection();
    if (changed) renderSupermarketManagement();
  }
}

function renderSupermarketManagement() {
  elements.supermarketList.replaceChildren();
  for (const market of supermarkets) {
    const form = document.createElement("form");
    form.className = "supermarket-row";
    const name = document.createElement("input");
    name.value = market.name;
    name.required = true;
    name.maxLength = 100;
    name.setAttribute("aria-label", `Name: ${market.name}`);
    const actions = document.createElement("div");
    actions.className = "dialog-actions";
    const save = document.createElement("button");
    save.type = "submit";
    save.className = "primary";
    save.textContent = "Umbenennen";
    const remove = document.createElement("button");
    remove.type = "button";
    remove.className = "secondary";
    remove.textContent = "Löschen";
    remove.setAttribute("aria-label", `Supermarkt löschen: ${market.name}`);
    remove.addEventListener("click", () => {
      if (confirm(`Supermarkt „${market.name}“ für alle Nutzer löschen? Die Einkaufslisten bleiben erhalten.`)) {
        changeSupermarket("delete_supermarket", { market_id: market.id });
      }
    });
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!name.value.trim()) {
        name.setCustomValidity("Bitte gib einen Namen ein.");
        name.reportValidity();
        return;
      }
      changeSupermarket("save_supermarket", { market_id: market.id, name: name.value.trim() });
    });
    name.addEventListener("input", () => name.setCustomValidity(""));
    actions.append(save, remove);
    form.append(name, actions);
    elements.supermarketList.append(form);
  }
}

elements.manageSupermarkets.addEventListener("click", async () => {
  elements.supermarketManagement.showModal();
  renderSupermarketManagement();
  elements.supermarketMessage.textContent = "Supermärkte werden geladen …";
  try {
    await refreshSupermarkets();
    elements.supermarketMessage.textContent = supermarkets.length ? "" : "Noch keine Supermärkte angelegt.";
  } catch (error) {
    elements.supermarketMessage.textContent = `Gespeicherte Offline-Kopie. Verwaltung nur online möglich: ${error.message}`;
  }
});

elements.addSupermarketForm.addEventListener("submit", event => {
  event.preventDefault();
  const name = elements.supermarketNewName.value.trim();
  if (!name) {
    elements.supermarketNewName.setCustomValidity("Bitte gib einen Namen ein.");
    elements.supermarketNewName.reportValidity();
    return;
  }
  changeSupermarket("save_supermarket", { market_id: "", name });
});
elements.supermarketNewName.addEventListener("input", () => elements.supermarketNewName.setCustomValidity(""));

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
  await storeRequest("lists", "put", snapshot || {
    entry_id: entryId,
    name: elements.listName.textContent,
    items: currentItems,
    saved_at: Date.now(),
  });
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

async function enqueue(operation) {
  if (busy) throw new Error("Bitte warte, bis die aktuelle Aktion abgeschlossen ist.");
  setBusy(true);
  try {
    const queued = {
      ...operation,
      id: crypto.randomUUID(),
      entry_id: entryId,
      created_at: (lastOperationTime = Math.max(Date.now(), lastOperationTime + 1)),
    };
    await storeRequest("operations", "put", queued);
    pendingOperations.push(queued);
    applyLocalOperation(queued);
    await saveList();
    render();
    updateConnection("offline");
  } finally {
    setBusy(false);
  }
  if (authenticated) await synchronize();
}

function applyLocalOperation(operation) {
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
    if (operation.status !== undefined) changes.status = operation.status;
    if (operation.summary !== undefined) changes.summary = operation.summary;
    currentItems = currentItems.map((item) =>
      item.uid === operation.uid ? { ...item, ...changes } : item,
    );
  } else if (operation.type === "delete_item") {
    currentItems = currentItems.filter((item) => item.uid !== operation.uid);
  }
}

function render() {
  const pendingIds = new Set(
    pendingOperations
      .filter((operation) => operation.type === "add_item")
      .map((operation) => operation.uid),
  );
  elements.items.replaceChildren();
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
    label.textContent = item.summary;
    label.setAttribute("aria-label", `Bearbeiten: ${item.summary}`);
    label.addEventListener("click", () => {
      editingUid = item.uid;
      elements.editSummary.value = item.summary;
      elements.editItem.showModal();
    });
    if (pendingIds.has(item.uid)) label.title = "Wird beim nächsten Verbinden übertragen";
    main.append(checkbox, label);
    const remove = document.createElement("button");
    remove.className = "delete";
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label", `Entfernen: ${item.summary}`);
    remove.addEventListener("click", () => {
      enqueue({ type: "delete_item", uid: item.uid }).catch(showError);
    });
    row.append(main, remove);
    elements.items.append(row);
  }
  elements.empty.hidden = currentItems.length > 0;
  elements.syncDetail.textContent = pendingOperations.length
    ? `${pendingOperations.length} Änderung${pendingOperations.length === 1 ? "" : "en"} ausstehend`
    : "Liste ist auf diesem Gerät gespeichert.";
  setBusy(busy);
}

function setBusy(value) {
  busy = value;
  elements.listSelect.disabled = value || !availableLists.length;
  if (elements.listSelect.disabled) closeFlyout(elements.listSelect, elements.listFlyout);
  elements.marketSelect.disabled = value || !entryId;
  if (elements.marketSelect.disabled) closeFlyout(elements.marketSelect, elements.marketFlyout);
  elements.addForm.inert = value || !entryId;
  elements.sync.disabled = value;
  elements.copySource.disabled = value || !entryId;
  elements.items.inert = value;
  elements.manageLists.disabled = value;
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
  const cached = await storeRequest("lists", "get");
  elements.listName.textContent = cached?.name ||
    availableLists.find((list) => list.entry_id === entryId)?.name || "Liste laden";
  currentItems = cached?.items || [];
  pendingOperations = await readQueue();
  for (const operation of pendingOperations) applyLocalOperation(operation);
  lastOperationTime = pendingOperations.reduce(
    (latest, operation) => Math.max(latest, operation.created_at), 0,
  );
  render();
  renderListSelection();
  loadMarketSelection();
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
    await enqueue({ type: "update_item", uid: editingUid, summary });
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

async function synchronize() {
  if (busy || !authenticated || socket?.readyState !== WebSocket.OPEN || !entryId) return;
  setBusy(true);
  try {
    const ids = new Set([entryId, ...availableLists.map((list) => list.entry_id)]);
    for (const listId of ids) {
      let snapshot = await sendCommand(`${DOMAIN}/get_list`, { entry_id: listId });
      await saveList(snapshot);
      const operations = await readQueue(listId);
      for (const operation of operations) {
        const payload = { ...operation };
        delete payload.id;
        delete payload.created_at;
        delete payload.type;
        snapshot = await sendCommand(`${DOMAIN}/${operation.type}`, payload);
        await saveList(snapshot);
        await storeRequest("operations", "delete", operation.id);
      }
    }
    await loadSelectedList();
    updateConnection("online", "Alle Änderungen wurden synchronisiert.");
    elements.message.textContent = "";
  } finally {
    try {
      await loadSelectedList();
    } finally {
      setBusy(false);
    }
  }
}

async function loadRemoteLists() {
  if (busy) throw new Error("Bitte warte, bis die aktuelle Aktion abgeschlossen ist, und synchronisiere erneut.");
  setBusy(true);
  let marketError;
  try {
    try {
      await refreshSupermarkets();
    } catch (error) {
      marketError = error;
    }
    const lists = await sendCommand(`${DOMAIN}/get_lists`);
    for (const cached of await readCachedLists()) {
      const listed = lists.find((list) => list.entry_id === cached.entry_id);
      await saveList({ ...cached, enabled: !!listed, name: listed?.name || cached.name });
    }
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
  } finally {
    setBusy(false);
  }
  try {
    await synchronize();
  } finally {
    if (marketError) showError(marketError);
  }
}

elements.manageLists.addEventListener("click", async () => {
  elements.listManagement.showModal();
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
  setBusy(true);
  try {
    const result = await sendCommand(`${DOMAIN}/copy_source`, { entry_id: entryId });
    currentItems = result.items;
    await saveList();
    for (const operation of pendingOperations) applyLocalOperation(operation);
    render();
    elements.message.textContent = "Neue Artikel aus der Quellliste übernommen.";
  } catch (error) {
    showError(error);
  } finally {
    setBusy(false);
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
