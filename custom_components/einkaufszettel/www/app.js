const STORAGE_NAME = "einkaufszettel-offline-v1";
const ENTRY_KEY = "einkaufszettel.entry_id";
const TOKEN_KEY = "einkaufszettel.auth";
const OAUTH_STATE_PREFIX = "einkaufszettel.oauth.";
const DOMAIN = "einkaufszettel";

const elements = {
  setup: document.querySelector("#setup"),
  addForm: document.querySelector("#add-form"),
  newItem: document.querySelector("#new-item"),
  items: document.querySelector("#items"),
  empty: document.querySelector("#empty"),
  message: document.querySelector("#message"),
  listName: document.querySelector("#list-name"),
  listSelect: document.querySelector("#list-select"),
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
let nextMessageId = 1;
let pendingInstallPrompt;
let currentItems = [];
let pendingOperations = [];
let busy = false;
let lastOperationTime = 0;
let availableLists = [];
let editingUid;

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
  if (socket?.readyState === WebSocket.OPEN) await synchronize();
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
  elements.addForm.inert = value || !entryId;
  elements.sync.disabled = value || !entryId;
  elements.copySource.disabled = value || !entryId;
  elements.items.inert = value;
}

function renderListSelection() {
  elements.listSelect.replaceChildren();
  const lists = [...availableLists];
  if (entryId && !lists.some((list) => list.entry_id === entryId)) {
    lists.unshift({ entry_id: entryId, name: elements.listName.textContent });
  }
  for (const list of lists) {
    const option = document.createElement("option");
    option.value = list.entry_id;
    option.textContent = list.name;
    elements.listSelect.append(option);
  }
  elements.listSelect.value = entryId || "";
  setBusy(busy);
}

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
}

elements.listSelect.addEventListener("change", async () => {
  if (busy) return;
  const previousEntry = entryId;
  setBusy(true);
  try {
    entryId = elements.listSelect.value;
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
});

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
  const response = await fetch(`${tokens.hassUrl}/auth/token`, {
    method: "POST",
    credentials: "same-origin",
    body,
  });
  if (!response.ok) throw new Error("Home Assistant-Anmeldung abgelaufen. Öffne HA erneut.");
  const refreshed = await response.json();
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
  const hassUrl = location.origin;
  const clientId = `${hassUrl}/`;
  const redirectUrl = new URL(
    `${location.protocol}//${location.host}${location.pathname}${location.search}`,
  );
  redirectUrl.searchParams.set("auth_callback", "1");
  redirectUrl.searchParams.delete("code");
  redirectUrl.searchParams.delete("state");
  redirectUrl.searchParams.delete("error");

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

async function connect() {
  if (!navigator.onLine || socket?.readyState === WebSocket.OPEN) return;
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
  try {
    tokens = await refreshTokenIfNeeded(tokens);
  } catch (error) {
    updateConnection("pending", error.message);
    elements.connect.hidden = false;
    return;
  }

  const scheme = location.protocol === "https:" ? "wss:" : "ws:";
  socket = new WebSocket(`${scheme}//${location.host}/api/websocket`);
  socket.addEventListener("message", (event) => {
    const message = JSON.parse(event.data);
    if (message.type === "auth_required") {
      socket.send(JSON.stringify({ type: "auth", access_token: tokens.access_token }));
    } else if (message.type === "auth_ok") {
      updateConnection("online");
      loadRemoteLists().catch(showError);
    } else if (message.type === "auth_invalid") {
      updateConnection("pending", "Home Assistant-Anmeldung abgelaufen. Öffne HA erneut und synchronisiere.");
      elements.connect.hidden = false;
      socket.close();
    } else if (message.type === "result") {
      const waiter = waiters.get(message.id);
      if (waiter) {
        waiters.delete(message.id);
        if (message.success) waiter.resolve(message.result);
        else waiter.reject(new Error(message.error?.message || "Synchronisierung fehlgeschlagen."));
      }
    }
  });
  socket.addEventListener("close", () => {
    if (pendingOperations.length) updateConnection("pending");
  });
  socket.addEventListener("error", () => {
    updateConnection(pendingOperations.length ? "pending" : "offline");
  });
}

const waiters = new Map();

document.addEventListener("click", (event) => {
  if (!elements.setup.contains(event.target)) elements.setup.open = false;
});
document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && elements.setup.open) {
    elements.setup.open = false;
    elements.setup.querySelector("summary").focus();
  }
});
elements.setup.addEventListener("click", (event) => {
  if (event.target.closest("button, a")) {
    elements.setup.open = false;
    elements.setup.querySelector("summary").focus();
  }
});

elements.connect.addEventListener("click", () => {
  connectHomeAssistant().catch(showError);
});

function sendCommand(type, payload = {}) {
  if (socket?.readyState !== WebSocket.OPEN) {
    return Promise.reject(new Error("Home Assistant ist gerade nicht erreichbar."));
  }
  const id = nextMessageId++;
  return new Promise((resolve, reject) => {
    waiters.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, type, ...payload }));
    window.setTimeout(() => {
      const waiter = waiters.get(id);
      if (waiter) {
        waiters.delete(id);
        reject(new Error("Zeitüberschreitung bei der Synchronisierung."));
      }
    }, 15000);
  });
}

async function synchronize() {
  if (busy || socket?.readyState !== WebSocket.OPEN || !entryId) return;
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
  const lists = await sendCommand(`${DOMAIN}/get_lists`);
  availableLists = lists;
  if (!entryId && lists.length) {
    entryId = lists[0].entry_id;
    localStorage.setItem(ENTRY_KEY, entryId);
  }
  renderListSelection();
  if (!lists.length) {
    throw new Error("Keine Einkaufszettel-Liste verfügbar. Binde deine Alexa-/HA-Quellliste zuerst in der HA-Integration ein.");
  }
  await synchronize();
}

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
  if (socket?.readyState === WebSocket.OPEN) {
    synchronize().catch(showError);
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

window.addEventListener("online", connect);
window.addEventListener("offline", () => updateConnection(pendingOperations.length ? "pending" : "offline"));
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
  setBusy(true);
  elements.openHomeassistant.href = "/";
  elements.openAppBrowser.href = location.href;
  elements.openAppBrowser.hidden = false;
  try {
    database = await openDatabase();
    availableLists = (await readCachedLists()).map(({ entry_id, name }) => ({ entry_id, name }));
    if (!entryId && availableLists.length) entryId = availableLists[0].entry_id;
    if (entryId) await loadSelectedList();
    else renderListSelection();
    if ("serviceWorker" in navigator) {
      await navigator.serviceWorker.register("./service-worker.js", { scope: "./" });
    }
    try {
      await completeAuthorization();
    } catch (error) {
      showError(error);
    }
    setBusy(false);
    connect();
  } catch (error) {
    showError(error);
    elements.connectionLabel.textContent = "Lokaler Speicher nicht verfügbar";
  }
}

start();
