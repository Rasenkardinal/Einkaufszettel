const backupElements = Object.fromEntries([...document.querySelectorAll("[id]")].map(element => [element.id, element]));
let backupHass;
let backupBusy = false;
let previewToken = null;
let backupTargets = [];
const MAX_BACKUP_BYTES = 100 * 1024 * 1024;
const message = (text, status = "info") => {
  backupElements["backup-message"].textContent = text;
  backupElements["backup-message"].dataset.status = status;
};
function updateButtons() {
  for (const id of ["backup-download", "backup-upload", "backup-previous", "local-export"]) {
    backupElements[id].disabled = backupBusy || (!backupHass && !id.startsWith("local-"));
  }
  backupElements["restore-apply"].disabled = backupBusy || !backupHass || !previewToken || !backupElements["restore-confirm"].checked;
  backupElements["restore-cancel"].disabled = backupBusy;
  backupElements["resume-apply"].disabled = backupBusy || !backupHass || !backupElements["resume-confirm"].checked ||
    !backupElements["resume-lists"].querySelector("input:checked");
  backupElements["local-clear"].disabled = backupBusy || !backupElements["local-confirm"].checked;
}
async function requestBackup(action = "", options = {}) {
  if (!backupHass) throw Error("Bitte als HA-Administrator in Home Assistant öffnen.");
  const response = await backupHass.fetchWithAuth(`/api/einkaufszettel/backup${action ? "/" + action : ""}`, options);
  if (!response.ok) {
    const text = await response.text();
    let detail = text;
    if (response.headers.get("content-type")?.includes("application/json")) detail = JSON.parse(text).error || text;
    throw Error(`Datensicherung fehlgeschlagen (HTTP ${response.status}): ${detail}`);
  }
  return response;
}
function download(blob, name) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = name;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60000);
}
async function withBackupAction(action) {
  if (backupBusy) return;
  backupBusy = true;
  updateButtons();
  try { await action(); }
  catch (error) { message(error.message, "error"); }
  finally { backupBusy = false; updateButtons(); }
}
async function localData(clear = false) {
  const database = await new Promise((resolve, reject) => {
    const request = indexedDB.open("einkaufszettel-offline-v1", 1);
    request.onupgradeneeded = () => {
      request.result.createObjectStore("lists", {keyPath: "entry_id"});
      request.result.createObjectStore("operations", {keyPath: "id"});
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction(["lists", "operations"], clear ? "readwrite" : "readonly");
      const lists = transaction.objectStore("lists").getAll();
      const operations = transaction.objectStore("operations").getAll();
      if (clear) transaction.objectStore("operations").clear();
      transaction.oncomplete = () => resolve({lists: lists.result, operations: operations.result});
      transaction.onerror = transaction.onabort = () => reject(transaction.error || Error("Lokale Daten konnten nicht gelesen werden."));
    });
  } finally { database.close(); }
}
async function refreshBackupStatus() {
  const status = await (await requestBackup("status")).json();
  backupTargets = status.lists;
  backupElements["fallback-section"].hidden = !status.fallback_available;
  const list = backupElements["resume-lists"];
  list.replaceChildren();
  for (const target of backupTargets.filter(item => item.source_paused)) {
    const label = document.createElement("label");
    const input = document.createElement("input");
    input.type = "checkbox"; input.value = target.entry_id; input.checked = true;
    label.append(input, document.createTextNode(`${target.name} · ${target.source_entity_id}`));
    list.append(label);
  }
  backupElements["resume-section"].hidden = !list.children.length;
  backupElements["resume-confirm"].checked = false;
}
for (const [id, action] of [["backup-download", ""], ["backup-previous", "previous"]]) {
  backupElements[id].addEventListener("click", () => withBackupAction(async () => {
    message("Sicherung wird erstellt …");
    const response = await requestBackup(action);
    const name = response.headers.get("content-disposition")?.match(/filename="([^"]+)"/)?.[1] ||
      `easy-shopping-${new Date().toISOString().slice(0, 10)}.json`;
    download(await response.blob(), name);
    message("Sicherung an den Browser zum Download übergeben.", "success");
  }));
}
backupElements["backup-upload"].addEventListener("click", () => backupElements["backup-file"].click());
backupElements["backup-file"].addEventListener("change", event => withBackupAction(async () => {
  const file = event.target.files[0];
  event.target.value = "";
  previewToken = null;
  backupElements["restore-preview"].hidden = true;
  if (!file) return;
  if (file.size > MAX_BACKUP_BYTES) throw Error("Die Sicherung darf maximal 100 MiB groß sein.");
  message("Datei wird hochgeladen und vollständig geprüft …");
  const preview = await (await requestBackup("preview", {method:"POST", body:file})).json();
  previewToken = preview.token;
  backupElements["preview-summary"].textContent =
    `${new Date(preview.created_at).toLocaleString("de-DE")} · Version ${preview.app_version} · ${preview.lists.length} Listen · ${preview.lists.reduce((n, item) => n + item.items, 0)} Artikel · ${preview.markets} Märkte · ${preview.catalogs} Kataloge`;
  const mappings = backupElements["restore-mapping"];
  mappings.replaceChildren();
  for (const source of preview.lists) {
    const label = document.createElement("label");
    label.className = "mapping-label";
    label.append(document.createTextNode(`${source.name} (${source.source_entity_id}) →`));
    const select = document.createElement("select");
    select.dataset.sourceId = source.entry_id;
    select.setAttribute("aria-label", `Zielliste für ${source.name}`);
    select.append(new Option("Zielliste auswählen", ""));
    for (const target of preview.targets) {
      select.append(new Option(`${target.name} · ${target.source_entity_id}`, target.entry_id));
    }
    select.value = preview.targets.find(target => target.source_entity_id === source.source_entity_id)?.entry_id || "";
    label.append(select); mappings.append(label);
  }
  backupElements["restore-confirm"].checked = false;
  backupElements["restore-preview"].hidden = false;
  backupElements["preview-title"].focus();
  message("Datei geprüft. Zuordnung kontrollieren und Ersetzen bestätigen.");
}));
backupElements["restore-cancel"].addEventListener("click", () => {
  previewToken = null;
  backupElements["restore-preview"].hidden = true;
  message("Wiederherstellung abgebrochen. Keine HA-Daten verändert.");
  updateButtons();
});
backupElements["restore-apply"].addEventListener("click", () => withBackupAction(async () => {
  const local = await localData();
  if (local.operations.length) throw Error("Dieser Browser hat noch Offline-Änderungen. Zuerst synchronisieren oder als lokalen Entwurf sichern und bewusst verwerfen.");
  const mapping = Object.fromEntries([...backupElements["restore-mapping"].querySelectorAll("select")].map(select => [select.dataset.sourceId, select.value]));
  if (Object.values(mapping).some(value => !value) || new Set(Object.values(mapping)).size !== Object.keys(mapping).length) {
    throw Error("Jede gesicherte Liste genau einer anderen Zielliste zuordnen.");
  }
  message("Wiederherstellung läuft. Bitte nicht schließen …");
  await requestBackup("restore", {method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({token:previewToken, mapping, confirm:backupElements["restore-confirm"].checked})});
  previewToken = null;
  backupElements["restore-preview"].hidden = true;
  await refreshBackupStatus();
  message("Daten wiederhergestellt. Quellabgleich bleibt gesperrt. Alle App-Geräte neu laden und Listen vor der Freigabe prüfen.", "success");
}));
backupElements["resume-apply"].addEventListener("click", () => withBackupAction(async () => {
  const entry_ids = [...backupElements["resume-lists"].querySelectorAll("input:checked")].map(input => input.value);
  await requestBackup("resume", {method:"POST", headers:{"Content-Type":"application/json"},
    body:JSON.stringify({entry_ids, confirm:backupElements["resume-confirm"].checked})});
  await refreshBackupStatus();
  message("Quellabgleich für die ausgewählten Listen freigegeben.", "success");
}));
backupElements["local-export"].addEventListener("click", () => withBackupAction(async () => {
  const local = await localData();
  download(new Blob([JSON.stringify({format:"easy-shopping-local-draft", created_at:new Date().toISOString(), ...local})],
    {type:"application/json"}), `easy-shopping-local-draft-${Date.now()}.json`);
  message(`${local.operations.length} ausstehende Änderungen als lokalen Entwurf exportiert.`, "success");
}));
backupElements["local-clear"].addEventListener("click", () => withBackupAction(async () => {
  await localData(true);
  backupElements["local-confirm"].checked = false;
  message("Ausstehende lokale Änderungen verworfen. Die Einkaufsliste neu laden und synchronisieren.", "success");
}));
document.addEventListener("change", updateButtons);
async function initializeBackup() {
  try {
    const root = window.parent !== window ? window.parent.document.querySelector("home-assistant") : null;
    backupHass = root?.hass;
    if (!backupHass || typeof backupHass.fetchWithAuth !== "function") {
      backupHass = null;
      backupElements["login-help"].hidden = false;
      throw Error("Bitte diese Seite innerhalb von Home Assistant öffnen.");
    }
    if (!backupHass.user?.is_admin) {
      backupHass = null;
      throw Error("Die Datensicherung ist nur für HA-Administratoren verfügbar.");
    }
    if (backupHass.themes?.darkMode === false) {
      document.body.dataset.colorMode = "light";
      document.body.dataset.theme = "porcelain-blue";
    }
    await refreshBackupStatus();
    message("Bereit. Sicherung herunterladen oder Datei zur Prüfung auswählen.");
  } catch (error) { message(error.message, "error"); }
  updateButtons();
}
initializeBackup();
