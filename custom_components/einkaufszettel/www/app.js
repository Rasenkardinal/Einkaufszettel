const STORAGE_NAME = "einkaufszettel-offline-v1";
const ENTRY_KEY = "einkaufszettel.entry_id";
const TOKEN_KEY = "einkaufszettel.auth";
const OAUTH_STATE_PREFIX = "einkaufszettel.oauth.";
const DOMAIN = "einkaufszettel";
const DESIGN_KEY = "einkaufszettel.design";
const MARKETS_KEY = "einkaufszettel.supermarkets";
const MARKET_SELECTION_PREFIX = "einkaufszettel.supermarket.";
const CATALOG_KEY = "einkaufszettel.catalog";
const MODE_KEY = "einkaufszettel.mode";

const elements = {
  appVersion: document.querySelector("#app-version"),
  setup: document.querySelector("#setup"),
  marketSelect: document.querySelector("#market-select"),
  marketBonusCard: document.querySelector("#market-bonus-card"),
  bonusCardDialog: document.querySelector("#bonus-card-dialog"),
  closeBonusCard: document.querySelector("#close-bonus-card"),
  bonusCardDialogImage: document.querySelector("#bonus-card-dialog-image"),
  itemPhotoDialog: document.querySelector("#item-photo-dialog"),
  closeItemPhoto: document.querySelector("#close-item-photo"),
  itemPhotoViewport: document.querySelector("#item-photo-viewport"),
  itemPhotoImage: document.querySelector("#item-photo-image"),
  marketFlyout: document.querySelector("#market-flyout"),
  marketName: document.querySelector("#market-name"),
  manageSupermarkets: document.querySelector("#manage-supermarkets"),
  manageProducts: document.querySelector("#manage-products"),
  catalogPage: document.querySelector("#catalog-page"),
  catalogClose: document.querySelector("#catalog-close"),
  catalogTitle: document.querySelector("#catalog-title"),
  catalogHelp: document.querySelector("#catalog-help"),
  catalogHelpTrigger: document.querySelector("#catalog-page .management-help-trigger"),
  catalogHelpPopover: document.querySelector("#catalog-help-popover"),
  catalogMessage: document.querySelector("#catalog-message"),
  catalogContent: document.querySelector("#catalog-content"),
  catalogFixedActions: document.querySelector("#catalog-fixed-actions"),
  catalogBack: document.querySelector("#catalog-back"),
  manageCategories: document.querySelector("#manage-categories"),
  productMergeConfirm: document.querySelector("#product-merge-confirm"),
  productMergeDescription: document.querySelector("#product-merge-description"),
  confirmProductMerge: document.querySelector("#confirm-product-merge"),
  designOptions: document.querySelector("#design-options"),
  designName: document.querySelector("#design-name"),
  designMessage: document.querySelector("#design-message"),
  manageLists: document.querySelector("#manage-lists"),
  listManagement: document.querySelector("#list-management"),
  listManagementHelp: document.querySelector("#list-management-help"),
  listManagementHelpTrigger: document.querySelector("#list-management .management-help-trigger"),
  listManagementHelpPopover: document.querySelector("#list-management-help-popover"),
  appConfirm: document.querySelector("#app-confirm"),
  appConfirmTitle: document.querySelector("#app-confirm-title"),
  appConfirmDescription: document.querySelector("#app-confirm-description"),
  acceptAppConfirm: document.querySelector("#accept-app-confirm"),
  managementMessage: document.querySelector("#management-message"),
  sourceLists: document.querySelector("#source-lists"),
  addForm: document.querySelector("#add-form"),
  openCommonItems: document.querySelector("#open-common-items"),
  commonItemsDialog: document.querySelector("#common-items-dialog"),
  commonItemsList: document.querySelector("#common-items-list"),
  commonItemsListTitle: document.querySelector("#common-items-list-title"),
  commonItemsListCount: document.querySelector("#common-items-list-count"),
  commonItemsEmpty: document.querySelector("#common-items-empty"),
  commonItemsSelection: document.querySelector("#common-items-selection"),
  cancelCommonItems: document.querySelector("#cancel-common-items"),
  closeCommonItems: document.querySelector("#close-common-items"),
  addCommonItems: document.querySelector("#add-common-items"),
  modeToggle: document.querySelector("#mode-toggle"),
  newItem: document.querySelector("#new-item"),
  productSuggestions: document.querySelector("#product-suggestions"),
  items: document.querySelector("#items"),
  endShoppingTemplate: document.querySelector("#end-shopping-action-template"),
  cashierReminder: document.querySelector("#cashier-reminder"),
  cashierReminderOk: document.querySelector("#cashier-reminder-ok"),
  cashierBonusCard: document.querySelector("#cashier-bonus-card"),
  cashierBonusCardImage: document.querySelector("#cashier-bonus-card-image"),
  endShoppingDialog: document.querySelector("#end-shopping-confirm"),
  endShoppingCancel: document.querySelector("#cancel-end-shopping"),
  endShoppingConfirm: document.querySelector("#end-shopping-confirm-button"),
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
  editItemTitle: document.querySelector("#edit-item-title"),
  editSummary: document.querySelector("#edit-summary"),
  editCategory: document.querySelector("#edit-category"),
  editCategoryPicker: document.querySelector(".category-picker"),
  editCategoryTrigger: document.querySelector("#edit-category-trigger"),
  editCategoryValue: document.querySelector("#edit-category-value"),
  editCategoryFlyout: document.querySelector("#edit-category-flyout"),
  editCategorySearch: document.querySelector("#edit-category-search"),
  editCategoryOptions: document.querySelector("#edit-category-options"),
  editCategoryUnavailable: document.querySelector("#edit-category-unavailable"),
  editCategoryEmpty: document.querySelector("#edit-category-empty"),
  editQuantity: document.querySelector("#edit-quantity"),
  editNotes: document.querySelector("#edit-notes"),
  editImageUpload: document.querySelector("#edit-image-upload"),
  editImageCamera: document.querySelector("#edit-image-camera"),
  editImageChoose: document.querySelector("#edit-image-choose"),
  editImageTake: document.querySelector("#edit-image-take"),
  editImagePreview: document.querySelector("#edit-image-preview"),
  editImageRemove: document.querySelector("#edit-image-remove"),
  editImageMessage: document.querySelector("#edit-image-message"),
  cancelEdit: document.querySelector("#cancel-edit"),
  connectionDot: document.querySelector("#connection-dot"),
  connectionLabel: document.querySelector("#connection-label"),
  syncDetail: document.querySelector("#sync-detail"),
  syncActions: document.querySelector(".sync-actions"),
  sync: document.querySelector("#sync"),
  syncDetailsToggle: document.querySelector("#sync-details-toggle"),
  syncFlyout: document.querySelector("#sync-flyout"),
  copySource: document.querySelector("#copy-source"),
  connect: document.querySelector("#connect"),
  install: document.querySelector("#install"),
  installHelp: document.querySelector("#install-help"),
  openHomeassistant: document.querySelector("#open-homeassistant"),
  openAppBrowser: document.querySelector("#open-app-browser"),
};
const MAX_IMAGE_BYTES = 512 * 1024;
const MAX_IMAGE_INPUT_BYTES = 12 * 1024 * 1024;

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
let startupConnecting = false;
let startupConnectionTimer;
let startupConnectionMessage = "";
let syncAnimationFrame;
let syncAnimationStarted = 0;
let syncAnimationFinishAt;
const reducedSyncMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
reducedSyncMotion.addEventListener("change", updateSyncAnimation);
let heartbeatTimer;
let heartbeatId;
let connectionGeneration = 0;
let nextMessageId = 1;
let pendingInstallPrompt;
let currentItems = [];
let deletedUids = new Set();
let pendingOperations = [];
let busy = false;
let longPressTouchPointerId = null;
let suppressLongPressClick = false;
let touchGateTimer;
let longPressTouchDialog = null;

function releaseLongPressTouchGate(restoreFocus = true) {
  window.clearTimeout(touchGateTimer);
  const dialog = longPressTouchDialog;
  longPressTouchDialog = null;
  if (!dialog) return;
  dialog.inert = false;
  dialog.classList.remove("touch-gated");
  if (!restoreFocus || !dialog.open) return;
  (dialog === elements.editItem ? elements.editItemTitle
    : dialog === elements.cashierReminder ? elements.cashierReminderOk
      : elements.endShoppingCancel)
    .focus({ preventScroll: true });
}

document.addEventListener("pointerdown", event => {
  if (longPressTouchPointerId !== null) {
    event.preventDefault();
    event.stopImmediatePropagation();
    return;
  }
  if (longPressTouchDialog?.inert) releaseLongPressTouchGate();
  suppressLongPressClick = false;
}, true);

document.addEventListener("pointermove", event => {
  if (longPressTouchPointerId === null) return;
  event.preventDefault();
  event.stopImmediatePropagation();
}, true);

document.addEventListener("pointerup", event => {
  if (longPressTouchPointerId === null) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  if (event.pointerId !== longPressTouchPointerId) return;
  longPressTouchPointerId = null;
  suppressLongPressClick = true;
  touchGateTimer = window.setTimeout(releaseLongPressTouchGate, 0);
}, true);

document.addEventListener("pointercancel", event => {
  if (event.pointerId !== longPressTouchPointerId) return;
  event.preventDefault();
  event.stopImmediatePropagation();
  longPressTouchPointerId = null;
  suppressLongPressClick = false;
  releaseLongPressTouchGate();
}, true);

document.addEventListener("click", event => {
  if (event.detail === 0 || (longPressTouchPointerId === null && !suppressLongPressClick)) return;
  suppressLongPressClick = false;
  event.preventDefault();
  event.stopImmediatePropagation();
  releaseLongPressTouchGate();
}, true);

window.addEventListener("blur", () => {
  longPressTouchPointerId = null;
  suppressLongPressClick = false;
  releaseLongPressTouchGate(false);
});
let syncPromise;
let syncRequested = false;
let fullSyncRequested = false;
let syncTimer;
let listRefreshPromise;
let lastOperationTime = 0;
let availableLists = [];
let editingUid;
let editingCategory;
let editingImage = null;
let editingImageRequest = 0;
let editingTrigger;
let supermarkets = [];
let catalogs = {};
let activeCatalogId = "supermarket";
let selectedMarket = "";
let planningMode = true;
let managingSupermarkets = false;
let categories = [];
let products = [];
let productAliases = {};
let dismissedProductSuggestions = [];
let catalogView;
let catalogDraft;
let catalogDirty = false;
let pendingAppConfirmation;
let catalogRequest = 0;
let pendingProductMerge;
let catalogProductQuery = "";
let productManagementScroll;
let serviceWorkerRegistration;
const nameOrder = new Intl.Collator("de", { sensitivity: "base", numeric: true });

function validateSupermarkets(value) {
  if (!Array.isArray(value) || value.some(market =>
    !market || typeof market.id !== "string" || !market.id ||
    typeof market.name !== "string" || !market.name.trim() || market.name.length > 100 ||
    (market.catalog_id !== undefined && (typeof market.catalog_id !== "string" || !market.catalog_id)) ||
    ["deposit_receipt_hint", "show_bonus_card"].some(key =>
      market[key] !== undefined && typeof market[key] !== "boolean") ||
    (market.bonus_card !== undefined && (
      typeof market.bonus_card !== "string" ||
      !/^data:image\/(?:png|jpeg|webp);base64,[A-Za-z0-9+/]+={0,2}$/.test(market.bonus_card) ||
      market.bonus_card.length > 4 * Math.ceil(MAX_IMAGE_BYTES / 3) + 32
    )) ||
    (market.category_ids !== undefined && (!Array.isArray(market.category_ids) ||
      market.category_ids.some(id => typeof id !== "string") ||
      new Set(market.category_ids).size !== market.category_ids.length))
  ) || new Set(value.map(market => market.id)).size !== value.length) {
    throw new Error("Die Supermarktdaten sind ungültig. Bitte erneut mit Home Assistant verbinden.");
  }
  return value;
}

function applyCatalog(value) {
  const nextMarkets = validateSupermarkets(value.supermarkets);
  const nextCatalogs = value.catalogs || {
    supermarket: {
      id: "supermarket", name: "Supermarkt",
      categories: value.categories || [], products: value.products || [],
      product_aliases: value.product_aliases || {},
      dismissed_product_suggestions: value.dismissed_product_suggestions || [],
    },
    hardware: { id: "hardware", name: "Baumarkt", categories: [], products: [] },
    tasks: { id: "tasks", name: "Aufgaben", categories: [], products: [] },
  };
  if (!nextCatalogs || typeof nextCatalogs !== "object" || Array.isArray(nextCatalogs) ||
      Object.entries(nextCatalogs).some(([id, catalog]) =>
        !id || !catalog || catalog.id !== id || typeof catalog.name !== "string" ||
        !catalog.name.trim() || !Array.isArray(catalog.categories) || !Array.isArray(catalog.products))) {
    throw new Error("Die Artikelkataloge sind ungültig. Bitte erneut laden.");
  }
  const catalogNames = Object.values(nextCatalogs).map(catalog => catalog.name.toLocaleLowerCase("de"));
  if (new Set(catalogNames).size !== catalogNames.length) {
    throw new Error("Die Artikelkataloge enthalten doppelte Namen. Bitte erneut laden.");
  }
  for (const catalog of Object.values(nextCatalogs)) {
    const catalogCategories = validateSupermarkets(catalog.categories);
    const categoryIds = new Set(catalogCategories.map(category => category.id));
    if (catalog.products.some(product =>
      !product || typeof product.name !== "string" || !productNameKey(product.name) ||
      product.key !== productNameKey(product.name) ||
      !validProductUsage(product.usage === undefined ? {} : product.usage) ||
      (product.usage_adjustment !== undefined &&
        (!Number.isSafeInteger(product.usage_adjustment) || productUsageCount(product) < 0)) ||
      (product.category_known !== undefined && typeof product.category_known !== "boolean") ||
      (product.category_known === false && product.category_id !== null) ||
      (product.category_id !== null && !categoryIds.has(product.category_id))
    ) || new Set(catalog.products.map(product => product.key)).size !== catalog.products.length) {
      throw new Error("Die Produktzuordnungen sind ungültig. Bitte erneut laden.");
    }
    const productKeys = new Set(catalog.products.map(product => product.key));
    const aliases = catalog.product_aliases || {};
    if (!aliases || typeof aliases !== "object" || Array.isArray(aliases) ||
        Object.entries(aliases).some(([key, target]) =>
          !key || productNameKey(key) !== key || productKeys.has(key) ||
          typeof target !== "string" || productNameKey(target) !== target || !productKeys.has(target))) {
      throw new Error("Die Artikelzuordnungen sind ungültig. Bitte erneut laden.");
    }
    const dismissed = catalog.dismissed_product_suggestions || [];
    if (!Array.isArray(dismissed) || dismissed.some(pair =>
      !Array.isArray(pair) || pair.length !== 2 || pair[0] === pair[1] ||
      pair.some(key => typeof key !== "string" || !productKeys.has(key)))) {
      throw new Error("Die bestätigten Ähnlichkeitshinweise sind ungültig. Bitte erneut laden.");
    }
    const dismissedKeys = dismissed.map(pair => JSON.stringify([...pair].sort()));
    if (new Set(dismissedKeys).size !== dismissedKeys.length) {
      throw new Error("Die bestätigten Ähnlichkeitshinweise sind ungültig. Bitte erneut laden.");
    }
  }
  if (nextMarkets.some(market => {
    const catalog = nextCatalogs[market.catalog_id || "supermarket"];
    return !catalog || (market.category_ids || []).some(id =>
      id && !catalog.categories.some(category => category.id === id));
  })) {
    throw new Error("Ein Supermarkt verweist auf unbekannte Kategorien oder Kataloge. Bitte erneut laden.");
  }
  const nextCatalogId = value.catalog_id || "supermarket";
  const activeCatalog = nextCatalogs[nextCatalogId];
  if (!activeCatalog) throw new Error("Der aktive Artikelkatalog fehlt. Bitte erneut laden.");
  const nextCategories = validateSupermarkets(activeCatalog.categories);
  const nextProducts = activeCatalog.products;
  const aliases = activeCatalog.product_aliases || {};
  const dismissedSuggestions = activeCatalog.dismissed_product_suggestions || [];
  supermarkets = nextMarkets;
  catalogs = nextCatalogs;
  activeCatalogId = nextCatalogId;
  categories = nextCategories;
  products = nextProducts;
  productAliases = aliases;
  dismissedProductSuggestions = dismissedSuggestions;
  applyProductCategories();
}

function activateCatalog(catalogId) {
  const catalog = catalogs[catalogId || "supermarket"];
  if (!catalog) throw new Error("Der gewählte Artikelkatalog ist nicht verfügbar. Bitte erneut laden.");
  activeCatalogId = catalog.id;
  categories = catalog.categories;
  products = catalog.products;
  productAliases = catalog.product_aliases || {};
  dismissedProductSuggestions = catalog.dismissed_product_suggestions || [];
  applyProductCategories();
}

function catalogIdForView() {
  if (catalogDraft?.catalog_id && catalogDraft.catalog_id !== "__new") {
    return catalogDraft.catalog_id;
  }
  return supermarkets.find(market => market.id === selectedMarket)?.catalog_id || "supermarket";
}

function productNameKey(name) {
  return name.trim().replace(/\s+/gu, " ").toLowerCase().replace(/ß/gu, "ss").replace(/ς/gu, "σ");
}

function canonicalProductKey(name) {
  const key = productNameKey(name);
  return productAliases[key] || key;
}

function validProductUsage(usage) {
  return !!usage && typeof usage === "object" && !Array.isArray(usage) &&
    Object.entries(usage).every(([id, stats]) => id && stats &&
      Number.isSafeInteger(stats.added) && stats.added >= 0 &&
      Number.isFinite(stats.last_added) && stats.last_added >= 0 &&
      stats.weeks && typeof stats.weeks === "object" && !Array.isArray(stats.weeks) &&
      Object.entries(stats.weeks).every(([week, count]) =>
        /^\d{4}-W(0[1-9]|[1-4]\d|5[0-3])$/u.test(week) && Number.isSafeInteger(count) && count >= 0));
}

function rememberProduct(name, categoryId, categoryKnown = true) {
  const key = canonicalProductKey(name);
  const known = products.find(item => item.key === key);
  const product = {
    ...known,
    key,
    name: known?.name || name,
    category_id: categoryId,
    category_known: categoryKnown,
  };
  products = [...products.filter(item => item.key !== key), product];
  if (catalogs[activeCatalogId]) catalogs[activeCatalogId].products = products;
}

function applyProductCategories() {
  currentItems = currentItems.map(item => {
    if ((item.metadata?.catalog_id || "supermarket") !== activeCatalogId) return item;
    const product = products.find(record => record.key === canonicalProductKey(item.summary));
    if (!product) {
      if (!item.metadata?.category_id) return item;
      const metadata = { ...item.metadata };
      delete metadata.category_id;
      return { ...item, metadata };
    }
    return {
      ...item,
      summary: product.name,
      ...(product.category_known !== false
        ? { metadata: { ...item.metadata, category_id: product.category_id } }
        : {}),
    };
  });
}

function cacheCatalog() {
  localStorage.setItem(CATALOG_KEY, JSON.stringify({
    catalog_id: activeCatalogId,
    catalogs,
    supermarkets,
    categories,
    products,
    product_aliases: productAliases,
    dismissed_product_suggestions: dismissedProductSuggestions,
  }));
}

function renderMarketSelection() {
  elements.marketFlyout.replaceChildren();
  for (const market of [{ id: "", name: "Ohne Markt" }, ...supermarkets]) {
    elements.marketFlyout.append(createPickerOption(market.name, market.id === selectedMarket, () => {
      closeFlyout(elements.marketSelect, elements.marketFlyout, true);
      selectedMarket = market.id;
      activateCatalog(market.catalog_id || "supermarket");
      cacheCatalog();
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
  elements.marketBonusCard.hidden = !market?.bonus_card;
  elements.marketBonusCard.setAttribute("aria-label", `Bonuskarte / APP-Code für ${market?.name || "Supermarkt"} anzeigen`);
}

elements.marketBonusCard.addEventListener("click", () => {
  const market = supermarkets.find(value => value.id === selectedMarket);
  if (!market?.bonus_card) return;
  elements.bonusCardDialogImage.src = market.bonus_card;
  elements.bonusCardDialogImage.alt = `Bonuskarte oder APP-Code für ${market.name}`;
  elements.bonusCardDialog.showModal();
});

elements.closeBonusCard.addEventListener("click", () => elements.bonusCardDialog.close());
elements.bonusCardDialog.addEventListener("click", event => {
  if (event.target === elements.bonusCardDialog) elements.bonusCardDialog.close();
});

let itemPhotoZoom = { scale: 1, x: 0, y: 0 };
const itemPhotoPointers = new Map();
let itemPhotoGesture = null;
const MAX_ITEM_PHOTO_ZOOM = 5;

function applyItemPhotoZoom(scale, x = itemPhotoZoom.x, y = itemPhotoZoom.y) {
  const viewport = elements.itemPhotoViewport;
  const image = elements.itemPhotoImage;
  const nextScale = Math.min(MAX_ITEM_PHOTO_ZOOM, Math.max(1, scale));
  const maxX = Math.max(0, (image.offsetWidth * nextScale - viewport.clientWidth) / 2);
  const maxY = Math.max(0, (image.offsetHeight * nextScale - viewport.clientHeight) / 2);
  itemPhotoZoom = {
    scale: nextScale,
    x: Math.min(maxX, Math.max(-maxX, nextScale === 1 ? 0 : x)),
    y: Math.min(maxY, Math.max(-maxY, nextScale === 1 ? 0 : y)),
  };
  image.style.transform = `translate(${itemPhotoZoom.x}px, ${itemPhotoZoom.y}px) scale(${itemPhotoZoom.scale})`;
  viewport.dataset.zoomed = String(itemPhotoZoom.scale > 1);
}

function resetItemPhotoZoom() {
  itemPhotoZoom = { scale: 1, x: 0, y: 0 };
  itemPhotoPointers.clear();
  itemPhotoGesture = null;
  elements.itemPhotoImage.style.transform = "";
  elements.itemPhotoViewport.dataset.zoomed = "false";
}

function openItemPhoto(item) {
  if (!item.metadata?.image) return;
  resetItemPhotoZoom();
  elements.itemPhotoImage.src = item.metadata.image;
  elements.itemPhotoImage.alt = `Foto von ${item.summary}`;
  elements.itemPhotoDialog.showModal();
}

elements.closeItemPhoto.addEventListener("click", () => elements.itemPhotoDialog.close());
elements.itemPhotoDialog.addEventListener("click", event => {
  if (event.target === elements.itemPhotoDialog) elements.itemPhotoDialog.close();
});
elements.itemPhotoDialog.addEventListener("close", () => {
  resetItemPhotoZoom();
  elements.itemPhotoImage.removeAttribute("src");
});
elements.itemPhotoViewport.addEventListener("pointerdown", event => {
  if (event.pointerType === "mouse" && event.button !== 0) return;
  if (event.pointerType === "mouse" && event.isTrusted) {
    event.currentTarget.setPointerCapture(event.pointerId);
  }
  itemPhotoPointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (itemPhotoPointers.size === 2) {
    const [first, second] = [...itemPhotoPointers.values()];
    itemPhotoGesture = {
      type: "pinch",
      distance: Math.hypot(second.x - first.x, second.y - first.y),
      centerX: (first.x + second.x) / 2,
      centerY: (first.y + second.y) / 2,
      ...itemPhotoZoom,
    };
  } else if (itemPhotoZoom.scale > 1) {
    itemPhotoGesture = {
      type: "pan",
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      offsetX: itemPhotoZoom.x,
      offsetY: itemPhotoZoom.y,
      scale: itemPhotoZoom.scale,
    };
  } else {
    itemPhotoGesture = null;
  }
});
elements.itemPhotoViewport.addEventListener("pointermove", event => {
  if (!itemPhotoPointers.has(event.pointerId)) return;
  itemPhotoPointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
  if (itemPhotoGesture?.type === "pinch" && itemPhotoPointers.size >= 2) {
    const [first, second] = [...itemPhotoPointers.values()];
    const centerX = (first.x + second.x) / 2;
    const centerY = (first.y + second.y) / 2;
    const distance = Math.hypot(second.x - first.x, second.y - first.y);
    applyItemPhotoZoom(
      itemPhotoGesture.scale * distance / Math.max(itemPhotoGesture.distance, 1),
      itemPhotoGesture.x + centerX - itemPhotoGesture.centerX,
      itemPhotoGesture.y + centerY - itemPhotoGesture.centerY,
    );
    event.preventDefault();
  } else if (itemPhotoGesture?.type === "pan" && itemPhotoGesture.pointerId === event.pointerId) {
    applyItemPhotoZoom(
      itemPhotoGesture.scale,
      itemPhotoGesture.offsetX + event.clientX - itemPhotoGesture.startX,
      itemPhotoGesture.offsetY + event.clientY - itemPhotoGesture.startY,
    );
    event.preventDefault();
  }
});
function finishItemPhotoPointer(event) {
  itemPhotoPointers.delete(event.pointerId);
  if (itemPhotoPointers.size < 2) {
    itemPhotoGesture = null;
    if (itemPhotoZoom.scale > 1 && itemPhotoPointers.size === 1) {
      const [pointerId, pointer] = [...itemPhotoPointers.entries()][0];
      itemPhotoGesture = {
        type: "pan",
        pointerId,
        startX: pointer.x,
        startY: pointer.y,
        offsetX: itemPhotoZoom.x,
        offsetY: itemPhotoZoom.y,
        scale: itemPhotoZoom.scale,
      };
    }
  }
}
elements.itemPhotoViewport.addEventListener("pointerup", finishItemPhotoPointer);
elements.itemPhotoViewport.addEventListener("pointercancel", finishItemPhotoPointer);
elements.itemPhotoViewport.addEventListener("wheel", event => {
  event.preventDefault();
  const rect = elements.itemPhotoViewport.getBoundingClientRect();
  const factor = event.deltaY < 0 ? 1.2 : 1 / 1.2;
  const scale = Math.min(MAX_ITEM_PHOTO_ZOOM, Math.max(1, itemPhotoZoom.scale * factor));
  const pointX = event.clientX - rect.left - rect.width / 2 - itemPhotoZoom.x;
  const pointY = event.clientY - rect.top - rect.height / 2 - itemPhotoZoom.y;
  const ratio = scale / itemPhotoZoom.scale;
  applyItemPhotoZoom(scale, itemPhotoZoom.x - pointX * (ratio - 1), itemPhotoZoom.y - pointY * (ratio - 1));
}, { passive: false });
elements.itemPhotoViewport.addEventListener("dblclick", event => {
  const rect = elements.itemPhotoViewport.getBoundingClientRect();
  const scale = itemPhotoZoom.scale > 1 ? 1 : 2.5;
  const ratio = scale / itemPhotoZoom.scale;
  const pointX = event.clientX - rect.left - rect.width / 2 - itemPhotoZoom.x;
  const pointY = event.clientY - rect.top - rect.height / 2 - itemPhotoZoom.y;
  applyItemPhotoZoom(scale, itemPhotoZoom.x - pointX * (ratio - 1), itemPhotoZoom.y - pointY * (ratio - 1));
});

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
  activateCatalog(supermarkets.find(market => market.id === selectedMarket)?.catalog_id || "supermarket");
  renderMarketSelection();
}

function loadCachedSupermarkets() {
  try {
    const catalog = localStorage.getItem(CATALOG_KEY);
    if (catalog) applyCatalog(JSON.parse(catalog));
    else {
      const cached = localStorage.getItem(MARKETS_KEY);
      if (cached) applyCatalog({ supermarkets: JSON.parse(cached), categories: [], products: [] });
    }
  } catch (error) {
    showError(error);
  }
  loadMarketSelection();
}

async function refreshSupermarkets(requestedCatalogId = catalogIdForView()) {
  const catalog = await sendCommand(`${DOMAIN}/get_catalog`, { catalog_id: requestedCatalogId });
  await withLocalState(async () => {
    applyCatalog(catalog);
    if (database) replayProductAssignments(await readQueue(null));
    cacheCatalog();
    loadMarketSelection();
    activateCatalog(catalogIdForView());
    render();
  });
}

function replayProductAssignments(operations) {
  for (const operation of operations) {
    if (operation.type === "add_item" && operation.summary &&
        (operation.metadata?.catalog_id || "supermarket") === activeCatalogId) {
      const known = products.find(product => product.key === canonicalProductKey(operation.summary));
      rememberProduct(operation.summary, known?.category_id ?? null, known ? known.category_known !== false : false);
    }
    if (operation.product_name && Object.hasOwn(operation.metadata || {}, "category_id") &&
        (operation.metadata?.catalog_id || "supermarket") === activeCatalogId) {
      rememberProduct(operation.product_name, operation.metadata.category_id);
    }
  }
}

function setMessage(element, text, status = "error") {
  element.textContent = text;
  element.dataset.status = text ? status : "";
}

function button(text, action, className = "secondary") {
  const element = document.createElement("button");
  element.type = "button";
  element.className = className;
  element.textContent = text;
  element.addEventListener("click", action);
  return element;
}

function chevron(className = "", down = false) {
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("class", `chevron ${className}`.trim());
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("fill", "none");
  icon.setAttribute("stroke", "currentColor");
  icon.setAttribute("stroke-width", "2");
  icon.setAttribute("stroke-linecap", "round");
  icon.setAttribute("stroke-linejoin", "round");
  icon.setAttribute("aria-hidden", "true");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", down ? "m6 9 6 6 6-6" : "m9 6 6 6-6 6");
  icon.append(path);
  return icon;
}

function itemPhotoIcon() {
  const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  icon.setAttribute("class", "item-photo-icon");
  icon.setAttribute("viewBox", "0 0 24 24");
  icon.setAttribute("fill", "none");
  icon.setAttribute("stroke", "currentColor");
  icon.setAttribute("stroke-width", "2");
  icon.setAttribute("aria-hidden", "true");
  const frame = document.createElementNS("http://www.w3.org/2000/svg", "rect");
  frame.setAttribute("x", "3");
  frame.setAttribute("y", "5");
  frame.setAttribute("width", "18");
  frame.setAttribute("height", "14");
  frame.setAttribute("rx", "3");
  const sun = document.createElementNS("http://www.w3.org/2000/svg", "circle");
  sun.setAttribute("cx", "8.5");
  sun.setAttribute("cy", "10");
  sun.setAttribute("r", "1.5");
  const landscape = document.createElementNS("http://www.w3.org/2000/svg", "path");
  landscape.setAttribute("d", "m21 15-5-5L5 19");
  icon.append(frame, sun, landscape);
  return icon;
}

function navigationButton(text, action, className) {
  const element = button("", action, className);
  const label = document.createElement("span");
  label.className = "navigation-label";
  label.textContent = text;
  element.append(label, chevron());
  return element;
}

function requestAppConfirmation({ title, description, confirmLabel = "Löschen", productName, onConfirm }) {
  elements.appConfirmTitle.textContent = title;
  elements.appConfirmDescription.textContent = description;
  elements.acceptAppConfirm.textContent = confirmLabel;
  elements.appConfirm.classList.toggle("danger-confirmation", confirmLabel === "Löschen");
  elements.appConfirm.classList.toggle("product-confirmation", !!productName);
  const help = document.querySelector("#app-confirm-help-trigger");
  help.hidden = !productName;
  setHelpPopover(help, document.querySelector("#app-confirm-help"), false);
  const name = document.querySelector("#app-confirm-product");
  name.textContent = productName || "";
  name.hidden = !productName;
  pendingAppConfirmation = onConfirm;
  elements.appConfirm.showModal();
}

elements.acceptAppConfirm.addEventListener("click", () => {
  const confirm = pendingAppConfirmation;
  pendingAppConfirmation = null;
  elements.appConfirm.close("confirm");
  confirm?.();
});
elements.appConfirm.addEventListener("close", () => {
  pendingAppConfirmation = null;
});

function setHelpPopover(trigger, popover, open) {
  trigger.setAttribute("aria-expanded", String(open));
  popover.hidden = !open;
}

const helpPopovers = [
  [elements.catalogHelpTrigger, elements.catalogHelpPopover],
  [elements.listManagementHelpTrigger, elements.listManagementHelpPopover],
  [document.querySelector("#app-confirm-help-trigger"), document.querySelector("#app-confirm-help")],
  [document.querySelector("#product-merge-help-trigger"), document.querySelector("#product-merge-help")],
];
for (const [trigger, popover] of helpPopovers) {
  trigger.addEventListener("click", () => {
    const opening = trigger.getAttribute("aria-expanded") !== "true";
    for (const [otherTrigger, otherPopover] of helpPopovers) setHelpPopover(otherTrigger, otherPopover, false);
    setHelpPopover(trigger, popover, opening);
  });
}
elements.listManagementHelpPopover.textContent = elements.listManagementHelp.textContent;
document.addEventListener("pointerdown", event => {
  for (const [trigger, popover] of helpPopovers) {
    if (trigger.getAttribute("aria-expanded") === "true" &&
      !trigger.contains(event.target) && !popover.contains(event.target)) {
      setHelpPopover(trigger, popover, false);
    }
  }
});
document.addEventListener("keydown", event => {
  if (event.key !== "Escape") return;
  for (const [trigger, popover] of helpPopovers) {
    if (trigger.getAttribute("aria-expanded") === "true") {
      setHelpPopover(trigger, popover, false);
      trigger.focus();
      event.preventDefault();
    }
  }
});

function paragraph(text, className = "management-help") {
  const element = document.createElement("p");
  element.className = className;
  element.textContent = text;
  return element;
}

function showManagementPage(page) {
  cancelCategoryDrag?.();
  setHelpPopover(elements.catalogHelpTrigger, elements.catalogHelpPopover, false);
  setHelpPopover(elements.listManagementHelpTrigger, elements.listManagementHelpPopover, false);
  document.querySelector("main.app").hidden = true;
  elements.catalogPage.hidden = page !== elements.catalogPage;
  elements.listManagement.hidden = page !== elements.listManagement;
  elements.setup.open = false;
  window.scrollTo(0, 0);
}

function requestDiscardChanges(action) {
  const dialog = document.querySelector("#discard-changes");
  if (dialog.open) return;
  dialog.returnValue = "";
  const form = dialog.querySelector("form");
  const handleSubmit = event => {
    if (event.submitter?.value !== "discard") return;
    catalogDirty = false;
    action();
  };
  form.addEventListener("submit", handleSubmit);
  dialog.addEventListener("close", () => form.removeEventListener("submit", handleSubmit), { once: true });
  dialog.showModal();
}

function leaveManagement() {
  if (managingSupermarkets) return;
  cancelCategoryDrag?.();
  if (catalogDirty) {
    requestDiscardChanges(leaveManagement);
    return;
  }
  cancelCategoryDrag?.();
  catalogRequest++;
  catalogDirty = false;
  catalogView = undefined;
  productManagementScroll = undefined;
  elements.catalogPage.hidden = true;
  elements.listManagement.hidden = true;
  document.querySelector("main.app").hidden = false;
  elements.listSelect.focus();
}

function openCatalog(view, record) {
  if (managingSupermarkets) return;
  cancelCategoryDrag?.();
  if (catalogDirty) {
    requestDiscardChanges(() => openCatalog(view, record));
    return;
  }
  if (catalogView === "products" && view !== "products") {
    productManagementScroll = {
      x: window.scrollX,
      y: window.scrollY,
      content: elements.catalogContent.scrollTop,
    };
  }
  const restoreProductScroll = view === "products" && catalogView !== "products"
    ? productManagementScroll : null;
  cancelCategoryDrag?.();
  catalogDirty = false;
  catalogView = view;
  catalogDraft = record ? { ...record, category_ids: [...(record.category_ids || [])] } : { id: "", name: "", category_ids: [] };
  activateCatalog(catalogIdForView());
  showManagementPage(elements.catalogPage);
  renderCatalogPage();
  if (restoreProductScroll) restoreProductManagementScroll(restoreProductScroll);
}

function restoreProductManagementScroll(position) {
  productManagementScroll = undefined;
  window.requestAnimationFrame(() => {
    window.scrollTo(position.x, position.y);
    elements.catalogContent.scrollTop = position.content;
  });
}

async function loadCatalogPage(view) {
  if (managingSupermarkets) return;
  cancelCategoryDrag?.();
  if (catalogDirty) {
    requestDiscardChanges(() => loadCatalogPage(view));
    return;
  }
  openCatalog(view);
  const request = ++catalogRequest;
  setMessage(elements.catalogMessage, "Katalog wird geladen …", "info");
  try {
    await refreshSupermarkets();
    if (request === catalogRequest && catalogView === view && !catalogDirty) {
      renderCatalogPage();
      setMessage(elements.catalogMessage, "");
    }
  } catch (error) {
    if (request === catalogRequest) {
      setMessage(elements.catalogMessage, `Offline-Kopie. Der Katalog konnte nicht aktualisiert werden: ${error.message}`);
    }
  }
}

async function openCategoryProducts(category) {
  if (managingSupermarkets) return;
  cancelCategoryDrag?.();
  if (catalogDirty) {
    requestDiscardChanges(() => openCategoryProducts(category));
    return;
  }
  openCatalog("category-products", category);
  if (catalogView !== "category-products" || catalogDraft.id !== category.id) return;
  const request = ++catalogRequest;
  setMessage(elements.catalogMessage, "Produktzuordnungen werden geladen …", "info");
  try {
    await refreshSupermarkets();
    if (request === catalogRequest && catalogView === "category-products" && catalogDraft.id === category.id) {
      renderCatalogPage();
    }
  } catch (error) {
    if (request === catalogRequest && catalogView === "category-products") {
      setMessage(elements.catalogMessage, `Offline-Kopie. Zuordnungen konnten nicht aktualisiert werden: ${error.message}`);
    }
  }
}

async function saveCatalog(command, payload, nextView) {
  if (managingSupermarkets) return;
  const productScroll = catalogView === "products" && nextView === "products"
    ? { x: window.scrollX, y: window.scrollY, content: elements.catalogContent.scrollTop }
    : nextView === "products" ? productManagementScroll : null;
  managingSupermarkets = true;
  elements.catalogContent.inert = true;
  elements.catalogFixedActions.inert = true;
  elements.catalogBack.disabled = true;
  elements.catalogClose.disabled = true;
  setMessage(elements.catalogMessage, "Wird gespeichert …", "info");
  let saved = false;
  try {
    const requestPayload = { catalog_id: catalogIdForView(), ...payload };
    const result = await sendCommand(`${DOMAIN}/${command}`, requestPayload);
    if (command.endsWith("supermarket")) {
      supermarkets = validateSupermarkets(result);
      if (command === "save_supermarket") {
        catalogDraft.catalog_id = requestPayload.catalog_id;
        catalogDraft.catalog_name = "";
      }
      await refreshSupermarkets(requestPayload.catalog_id);
    } else {
      applyCatalog(result);
    }
    saved = true;
    if (database) replayProductAssignments(await readQueue(null));
    catalogDirty = false;
    catalogView = nextView;
    cacheCatalog();
    setMessage(elements.catalogMessage, "In Home Assistant gespeichert.", "success");
  } catch (error) {
    setMessage(elements.catalogMessage, saved
      ? `In Home Assistant gespeichert, aber Offline-Kopie fehlgeschlagen: ${error.message}`
      : error.message);
  } finally {
    managingSupermarkets = false;
    elements.catalogContent.inert = false;
    elements.catalogFixedActions.inert = false;
    elements.catalogBack.disabled = false;
    elements.catalogClose.disabled = false;
    if (saved) {
      const message = elements.catalogMessage.textContent;
      const status = elements.catalogMessage.dataset.status;
      loadMarketSelection();
      activateCatalog(catalogIdForView());
      render();
      renderCatalogPage();
      setMessage(elements.catalogMessage, message, status);
      if (productScroll) restoreProductManagementScroll(productScroll);
    }
  }
}

function productUsageCount(product) {
  return (product.usage_adjustment || 0) + Object.values(product.usage || {}).reduce(
    (total, stats) => total + Math.max(stats.added, Object.values(stats.weeks).reduce((sum, count) => sum + count, 0)),
    0,
  );
}

function productEditDistance(first, second) {
  const previous = Array.from({ length: second.length + 1 }, (_, index) => index);
  for (let row = 1; row <= first.length; row++) {
    let diagonal = previous[0];
    previous[0] = row;
    for (let column = 1; column <= second.length; column++) {
      const above = previous[column];
      previous[column] = Math.min(
        previous[column] + 1,
        previous[column - 1] + 1,
        diagonal + (first[row - 1] === second[column - 1] ? 0 : 1),
      );
      diagonal = above;
    }
  }
  return previous[second.length];
}

function similarProduct(product) {
  const matches = products.filter(candidate => candidate.key !== product.key)
    .map(candidate => ({
      product: candidate,
      distance: productEditDistance(product.key, candidate.key),
    }))
    .sort((a, b) => a.distance - b.distance || nameOrder.compare(a.product.name, b.product.name));
  if (!matches.length) return null;
  const [best, next] = matches;
  const threshold = Math.max(1, Math.floor(Math.max(product.key.length, best.product.key.length) * 0.22));
  if (best.distance > threshold || next?.distance === best.distance) return null;
  return best.product;
}

let productDeleteRequest = 0;

async function openProductDelete(product) {
  const request = ++productDeleteRequest;
  try {
    const info = await sendCommand(`${DOMAIN}/get_product_delete_info`, { product_key: product.key });
    if (request !== productDeleteRequest) return;
    if (!info || info.product?.key !== product.key || typeof info.product.name !== "string" ||
        !validProductUsage(info.product.usage === undefined ? {} : info.product.usage) ||
        !Array.isArray(info.lists) || info.lists.some(list =>
          !list || typeof list.entry_id !== "string" || typeof list.name !== "string")) {
      throw new Error("Die betroffenen Einkaufslisten konnten nicht geprüft werden. Bitte erneut laden.");
    }
    const count = productUsageCount(info.product);
    const lines = [];
    if (count) lines.push(`Statistik für diesen Artikel wird ebenfalls gelöscht! Bisher ${count} ${count === 1 ? "Verwendung" : "Verwendungen"}.`);
    if (info.lists.length) lines.push(
      `Der Artikel wird auch aus ${info.lists.length === 1 ? "der Liste" : "den Listen"} ${info.lists.map(list => `„${list.name}“`).join(", ")} entfernt.`,
      "Verbundene HA-/Alexa-Listen werden beim nächsten Abgleich aktualisiert."
    );
    lines.push("Diese Aktion kann nicht rückgängig gemacht werden.");
    requestAppConfirmation({
      title: "Artikel löschen?",
      productName: info.product.name,
      description: lines.join("\n\n"),
      onConfirm: () => saveCatalog("delete_product", {
        product_key: product.key, confirmed_lists: info.lists,
      }, "products"),
    });
  } catch (error) {
    if (request === productDeleteRequest) setMessage(elements.catalogMessage, error.message);
  }
}

function productManagementRow(product, suggestion) {
  const row = document.createElement("article");
  row.className = "product-management-row" + (suggestion ? " product-comparison" : "");
  row.dataset.productName = product.name.toLocaleLowerCase("de");
  const heading = document.createElement("div");
  heading.className = "product-management-heading";
  const name = document.createElement("span");
  name.className = "product-management-name";
  name.append(document.createTextNode(product.name));
  const usage = document.createElement("span");
  usage.className = "product-management-usage";
  const count = productUsageCount(product);
  usage.textContent = `${count} ${count === 1 ? "Verwendung" : "Verwendungen"}`;
  name.append(usage);
  const renameButton = suggestion
    ? button("Umbenennen", () => openCatalog("product-edit", product), "secondary product-rename")
    : navigationButton("Umbenennen", () => openCatalog("product-edit", product), "secondary product-outline-action");
  renameButton.setAttribute("aria-label", `${product.name} umbenennen`);
  const renameIcon = document.createElement("span");
  renameIcon.className = "product-rename-icon";
  renameIcon.textContent = "✎";
  renameIcon.setAttribute("aria-hidden", "true");
  const renameArrow = chevron();
  if (suggestion) {
    renameButton.prepend(renameIcon);
    renameButton.append(renameArrow);
  }
  heading.append(name);
  if (suggestion) heading.append(renameButton);
  row.append(heading);
  if (suggestion) {
    const suggestionBox = document.createElement("section");
    suggestionBox.className = "product-similar";
    suggestionBox.append(paragraph("Sind diese Artikel identisch?", "product-similar-label"));
    const target = document.createElement("div");
    target.className = "product-similar-target";
    const sourceName = document.createElement("strong");
    sourceName.textContent = product.name;
    const comparisonArrow = document.createElement("span");
    comparisonArrow.className = "product-similar-arrow";
    comparisonArrow.textContent = "↔";
    comparisonArrow.setAttribute("aria-hidden", "true");
    const targetName = document.createElement("strong");
    targetName.textContent = suggestion.name;
    const targetCount = productUsageCount(suggestion);
    targetName.title = `${targetCount} ${targetCount === 1 ? "Verwendung" : "Verwendungen"}`;
    target.append(sourceName, comparisonArrow, targetName);
    const suggestionActions = document.createElement("div");
    suggestionActions.className = "product-similar-actions";
    suggestionActions.append(button("Kein Fehler", () => {
      saveCatalog("dismiss_product_suggestion", {
        product_key: product.key,
        similar_key: suggestion.key,
      }, "products");
    }, "secondary product-similar-dismiss"), button("Zusammenführen …", () => {
      openCatalog("product-merge", product);
      catalogDraft.target_key = suggestion.key;
      renderCatalogPage();
    }, "secondary"));
    suggestionBox.append(target, suggestionActions);
    suggestionBox.append(paragraph("„Kein Fehler“ blendet diesen Vergleich dauerhaft aus.", "product-merge-help"));
    row.append(suggestionBox);
  }
  const actions = document.createElement("div");
  actions.className = "product-management-actions";
  const statisticsButton = navigationButton("Statistik", () => openCatalog("product-statistics", product),
    suggestion ? "secondary" : "secondary product-outline-action");
  const deleteButton = button("Löschen", () => openProductDelete(product), "secondary danger-button");
  deleteButton.title = "Artikel, Statistik und Einträge auf den bestätigten Listen löschen.";
  if (!suggestion) {
    const primaryActions = document.createElement("div");
    primaryActions.className = "product-management-buttons";
    const mergeButton = navigationButton("Zusammenführen", () => openCatalog("product-merge", product), "secondary product-outline-action product-merge-action");
    primaryActions.append(renameButton, mergeButton, statisticsButton, deleteButton);
    row.append(primaryActions);
  }
  if (suggestion) {
    actions.append(statisticsButton, deleteButton);
    row.append(actions);
  }
  return row;
}

function renderProductManagement() {
  elements.catalogTitle.textContent = "Artikel verwalten";
  elements.catalogHelp.textContent = "Artikel und Suchvorschläge im Katalog des gewählten Marktes. Umbenennen und Zusammenführen übernehmen auch die bisherige Statistik. Löschen entfernt die Statistik und Einträge auf den im Dialog genannten Listen.";
  const search = document.createElement("input");
  search.className = "product-search";
  search.type = "search";
  search.placeholder = "Artikel suchen …";
  search.setAttribute("aria-label", "Artikel suchen");
  search.autocomplete = "off";
  search.value = catalogProductQuery;
  const count = document.createElement("p");
  count.className = "product-list-summary";
  const updateCount = () => {
    const query = productNameKey(catalogProductQuery);
    const visible = records.filter(product => productNameKey(product.name).includes(query)).length;
    count.textContent = `${visible} Artikel`;
  };
  const records = [...products].sort((a, b) => nameOrder.compare(a.name, b.name));
  const possibleTypos = records
    .map(product => ({ product, similar: similarProduct(product) }))
    .filter(value => value.similar &&
      productUsageCount(value.product) < productUsageCount(value.similar) &&
      !dismissedProductSuggestions.some(pair =>
        pair.includes(value.product.key) && pair.includes(value.similar.key)));
  const suggestions = document.createElement("section");
  if (possibleTypos.length) {
    suggestions.append(paragraph("Mögliche Schreibfehler", "section-label"));
    for (const { product, similar } of possibleTypos) {
      suggestions.append(productManagementRow(product, similar));
    }
  }
  const list = document.createElement("section");
  list.append(paragraph("Alle Artikel", "section-label"));
  for (const product of records) list.append(productManagementRow(product));
  const empty = paragraph("Noch keine Artikel im Katalog angelegt.");
  empty.hidden = records.length > 0;
  elements.catalogContent.append(search, count, suggestions, list, empty);
  search.addEventListener("input", () => {
    catalogProductQuery = search.value;
    const query = productNameKey(catalogProductQuery);
    elements.catalogContent.querySelectorAll(".product-management-row").forEach(row => {
      row.hidden = !productNameKey(row.dataset.productName).includes(query);
    });
    updateCount();
  });
  updateCount();
  elements.catalogFixedActions.append(
    button("Abbrechen", leaveManagement),
    button("Hinzufügen", () => openCatalog("product-edit", { key: "", name: "" }), "primary"),
  );
  elements.catalogFixedActions.hidden = false;
}

function renderProductStatistics() {
  const product = products.find(item => item.key === catalogDraft.key);
  elements.catalogTitle.textContent = "Statistik bearbeiten";
  elements.catalogHelp.textContent = "Gesamtzahl über alle Einkaufslisten. Wochenstatistik und listenbezogene Häufigkeiten bleiben unverändert. Neue Verwendungen zählen weiter.";
  if (!product) {
    setMessage(elements.catalogMessage, "Der Artikel wurde inzwischen geändert. Bitte die Übersicht neu öffnen.");
    return;
  }
  const form = document.createElement("form");
  form.className = "management-form";
  const label = document.createElement("label");
  label.htmlFor = "product-usage-count";
  label.textContent = `${product.name} · Verwendungen insgesamt`;
  const input = document.createElement("input");
  input.id = "product-usage-count";
  input.type = "number";
  input.min = "0";
  input.max = "2147483647";
  input.step = "1";
  input.required = true;
  input.value = catalogDraft.statisticsCount ?? productUsageCount(product);
  input.addEventListener("input", () => {
    catalogDraft.statisticsCount = input.value;
    catalogDirty = true;
    input.setCustomValidity("");
  });
  const actions = document.createElement("div");
  actions.className = "page-actions";
  const save = button("Speichern", () => {}, "primary");
  save.type = "submit";
  actions.append(button("Abbrechen", () => openCatalog("products")), save);
  form.append(label, input);
  appendCatalogFormActions(form, actions);
  form.addEventListener("submit", event => {
    event.preventDefault();
    const count = input.valueAsNumber;
    if (!Number.isInteger(count) || count < 0 || count > 2147483647) {
      input.setCustomValidity("Bitte gib eine ganze Zahl von 0 bis 2147483647 ein.");
      input.reportValidity();
      return;
    }
    saveCatalog("set_product_statistics", { product_key: product.key, count }, "products");
  });
  elements.catalogContent.append(form);
}

function renderProductEdit() {
  const product = products.find(item => item.key === catalogDraft.key);
  const creating = !catalogDraft.key;
  if (!creating && !product) {
    setMessage(elements.catalogMessage, "Der Artikel wurde inzwischen geändert. Bitte die Übersicht neu öffnen.");
    return;
  }
  elements.catalogTitle.textContent = creating ? "Artikel hinzufügen" : "Artikel umbenennen";
  elements.catalogHelp.textContent = creating
    ? "Lege einen Artikel für Suchvorschläge an. Er wird noch keiner Einkaufsliste hinzugefügt."
    : `${catalogDraft.name} · ${productUsageCount(product)} Verwendungen. Der neue Name wird auch in bestehenden Listen und Statistiken übernommen.`;
  const form = document.createElement("form");
  form.className = "management-form";
  const label = document.createElement("label");
  label.className = "visually-hidden";
  label.htmlFor = "product-name";
  label.textContent = "Artikelname";
  const input = document.createElement("input");
  input.id = "product-name";
  input.required = true;
  input.maxLength = 200;
  input.autocomplete = "off";
  input.value = creating ? "" : catalogDraft.name;
  if (creating) input.placeholder = "Neuer Artikel";
  input.addEventListener("input", () => {
    catalogDraft.name = input.value;
    catalogDirty = true;
  });
  const actions = document.createElement("div");
  actions.className = "page-actions";
  const save = button("Speichern", () => {}, "primary");
  save.type = "submit";
  actions.append(button("Abbrechen", () => openCatalog("products")), save);
  form.append(label, input);
  appendCatalogFormActions(form, actions);
  form.addEventListener("submit", event => {
    event.preventDefault();
    const name = input.value.trim();
    if (!name) {
      input.setCustomValidity("Bitte gib einen Namen ein.");
      input.reportValidity();
      return;
    }
    saveCatalog(
      creating ? "create_product" : "rename_product",
      creating ? { name } : { product_key: product.key, name },
      "products",
    );
  });
  elements.catalogContent.append(form);
}

function renderProductMerge() {
  const source = products.find(item => item.key === catalogDraft.key);
  if (!source) {
    setMessage(elements.catalogMessage, "Der Artikel wurde inzwischen geändert. Bitte die Übersicht neu öffnen.");
    return;
  }
  elements.catalogTitle.textContent = "Artikel zusammenführen";
  elements.catalogHelp.textContent = "Wähle den Artikelnamen, der künftig in Listen, Statistik und Suchvorschlägen verwendet wird.";
  const form = document.createElement("form");
  form.className = "management-form";
  const label = document.createElement("label");
  label.id = "product-merge-label";
  label.htmlFor = "product-merge-trigger";
  label.textContent = "Behalten als";
  label.className = "visually-hidden";
  const picker = document.createElement("div");
  picker.className = "category-picker";
  const selectedTarget = products.find(item => item.key === catalogDraft.target_key && item.key !== source.key);
  const value = document.createElement("span");
  value.id = "product-merge-value";
  value.textContent = selectedTarget?.name || "Zielartikel auswählen …";
  const trigger = document.createElement("button");
  trigger.id = "product-merge-trigger";
  trigger.type = "button";
  trigger.className = "category-picker-trigger";
  trigger.setAttribute("role", "combobox");
  trigger.setAttribute("aria-labelledby", "product-merge-label product-merge-value");
  trigger.setAttribute("aria-expanded", "false");
  trigger.setAttribute("aria-haspopup", "listbox");
  trigger.setAttribute("aria-controls", "product-merge-options");
  const arrow = chevron("category-picker-arrow", true);
  trigger.append(value, arrow);
  const flyout = document.createElement("div");
  flyout.id = "product-merge-flyout";
  flyout.className = "category-picker-flyout";
  flyout.hidden = true;
  const options = document.createElement("div");
  options.id = "product-merge-options";
  options.className = "category-options";
  options.setAttribute("role", "listbox");
  options.setAttribute("aria-labelledby", "product-merge-label");
  const hiddenValue = document.createElement("input");
  hiddenValue.id = "product-merge-target";
  hiddenValue.type = "hidden";
  hiddenValue.value = selectedTarget?.key || "";
  const targetProducts = [...products].filter(item => item.key !== source.key)
    .sort((a, b) => nameOrder.compare(a.name, b.name));
  if (!targetProducts.length) {
    setMessage(elements.catalogMessage, "Zum Zusammenführen müssen mindestens zwei Artikel vorhanden sein.");
    return;
  }
  const optionButtons = targetProducts.map(product => {
    const option = button("", () => {
      hiddenValue.value = product.key;
      catalogDraft.target_key = product.key;
      value.textContent = product.name;
      optionButtons.forEach(candidate => {
        const selected = candidate.dataset.productKey === product.key;
        candidate.setAttribute("aria-selected", String(selected));
        candidate.tabIndex = selected ? 0 : -1;
      });
      trigger.setCustomValidity("");
      closePicker(true);
      updatePreview();
    }, "category-option");
    option.type = "button";
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", String(product.key === hiddenValue.value));
    option.tabIndex = product.key === hiddenValue.value ? 0 : -1;
    option.dataset.productKey = product.key;
    const optionName = document.createElement("span");
    optionName.className = "category-option-name";
    optionName.textContent = product.name;
    const check = document.createElement("span");
    check.className = "category-option-check";
    check.textContent = "✓";
    check.setAttribute("aria-hidden", "true");
    option.append(optionName, check);
    options.append(option);
    return option;
  });
  function closePicker(focusTrigger = false) {
    flyout.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
    document.removeEventListener("pointerdown", handleOutsidePointerDown);
    if (focusTrigger) trigger.focus();
  }
  function handleOutsidePointerDown(event) {
    if (!picker.contains(event.target)) closePicker();
  }
  function openPicker() {
    flyout.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
    document.addEventListener("pointerdown", handleOutsidePointerDown);
    (optionButtons.find(option => option.dataset.productKey === hiddenValue.value) || optionButtons[0])?.focus();
  }
  trigger.addEventListener("click", () => {
    if (flyout.hidden) openPicker();
    else closePicker();
  });
  trigger.addEventListener("keydown", event => {
    if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
      event.preventDefault();
      if (flyout.hidden) openPicker();
    }
  });
  options.addEventListener("keydown", event => {
    const currentIndex = optionButtons.indexOf(document.activeElement);
    let nextIndex;
    if (event.key === "ArrowDown") nextIndex = Math.min(optionButtons.length - 1, currentIndex + 1);
    else if (event.key === "ArrowUp") nextIndex = Math.max(0, currentIndex - 1);
    else if (event.key === "Home") nextIndex = 0;
    else if (event.key === "End") nextIndex = optionButtons.length - 1;
    else if (event.key === "Escape") {
      event.preventDefault();
      closePicker(true);
      return;
    } else if (event.key === "Tab") {
      closePicker();
      return;
    } else return;
    event.preventDefault();
    optionButtons[nextIndex]?.focus();
  });
  flyout.append(options);
  picker.append(trigger, flyout, hiddenValue);
  const preview = paragraph("Wähle einen Zielartikel, um die Statistikübernahme anzusehen.", "product-merge-preview");
  const updatePreview = () => {
    const target = products.find(item => item.key === hiddenValue.value);
    preview.replaceChildren();
    if (!target) {
      preview.textContent = "Wähle einen Zielartikel, um die Statistikübernahme anzusehen.";
      return;
    }
    const sourceCount = productUsageCount(source);
    const targetCount = productUsageCount(target);
    const text = document.createElement("span");
    text.append(
      document.createTextNode(`${sourceCount} ${sourceCount === 1 ? "Verwendung" : "Verwendungen"} von `),
    );
    const sourceName = document.createElement("strong");
    sourceName.textContent = source.name;
    const targetName = document.createElement("strong");
    targetName.textContent = target.name;
    text.append(sourceName, document.createTextNode(" gehen zu "), targetName,
      document.createTextNode(`. Danach hat der Zielartikel ${sourceCount + targetCount} Verwendungen. Listen und Statistik bleiben erhalten.`));
    preview.append(text);
  };
  updatePreview();
  const actions = document.createElement("div");
  actions.className = "page-actions";
  const submit = button("Weiter …", () => {}, "primary");
  submit.type = "submit";
  actions.append(button("Abbrechen", () => openCatalog("products")), submit);
  form.addEventListener("submit", event => {
    event.preventDefault();
    const target = products.find(item => item.key === hiddenValue.value);
    if (!target) {
      trigger.setCustomValidity("Bitte wähle einen Zielartikel.");
      trigger.reportValidity();
      return;
    }
    pendingProductMerge = { product_key: source.key, target_key: target.key };
    document.querySelector("#product-merge-names").textContent = `${source.name} → ${target.name}`;
    elements.productMergeDescription.textContent =
      `${productUsageCount(source)} + ${productUsageCount(target)} = ${productUsageCount(source) + productUsageCount(target)} Verwendungen. Wochenstatistiken werden zusammengeführt. Bestehende Einkaufslisten verwenden anschließend ${target.name}.`;
    setHelpPopover(document.querySelector("#product-merge-help-trigger"), document.querySelector("#product-merge-help"), false);
    elements.productMergeConfirm.showModal();
  });
  form.append(paragraph(source.name, "market-context"), label, picker, preview);
  appendCatalogFormActions(form, actions);
  elements.catalogContent.append(form);
}

let cancelCategoryDrag;
let marketSelectionSnapshot;

function appendCatalogFormActions(form, actions) {
  form.id = "catalog-editor-form";
  for (const control of actions.querySelectorAll('button[type="submit"]')) {
    control.setAttribute("form", form.id);
  }
  elements.catalogFixedActions.append(...actions.children);
  elements.catalogFixedActions.hidden = false;
}

function renderCatalogPage() {
  cancelCategoryDrag?.();
  const content = elements.catalogContent;
  content.replaceChildren();
  elements.catalogFixedActions.replaceChildren();
  elements.catalogFixedActions.hidden = true;
  const hasFixedActions = catalogView !== "market-edit";
  elements.catalogPage.classList.toggle("has-fixed-actions", hasFixedActions);
  elements.catalogPage.classList.toggle("market-editor", catalogView === "market-edit");
  elements.catalogPage.classList.add("clean-market-view");
  elements.catalogPage.dataset.view = catalogView;
  elements.catalogPage.classList.toggle("market-card-editor", catalogView === "market-bonus-card");
  const close = elements.catalogClose;
  close.hidden = false;
  close.disabled = managingSupermarkets;
  close.onclick = () => elements.catalogBack.click();
  setMessage(elements.catalogMessage, "");
  const isMarket = catalogView?.startsWith("market");
  const isList = catalogView === "markets" || catalogView === "categories" || catalogView === "products";
  const noun = isMarket ? "Supermarkt" : "Kategorie";
  elements.catalogBack.querySelector("span").textContent = catalogView === "products" ? "Zurück zur Liste"
    : isList ? "Zurück zur Liste"
    : catalogView === "market-order" ? "Supermarkt bearbeiten"
    : catalogView === "market-select" ? "Marktkategorien"
    : catalogView === "market-bonus-card" ? "Bonuskarten oder APP-Codes"
    : catalogView === "category-products" ? "Kategorie bearbeiten"
    : ["product-edit", "product-merge", "product-statistics"].includes(catalogView) ? "Artikel verwalten"
    : isMarket ? "Supermärkte" : "Produktkategorien";
  elements.catalogBack.onclick = () => {
    if (isList) leaveManagement();
    else if (catalogView === "category-products") openCatalog("category-edit", catalogDraft);
    else if (catalogView === "market-order" || catalogView === "market-bonus-card") openCatalog("market-edit", catalogDraft);
    else if (["product-edit", "product-merge", "product-statistics"].includes(catalogView)) openCatalog("products");
    else if (catalogView === "market-select") {
      leaveMarketCategorySelection(false);
    } else openCatalog(isMarket ? "markets" : "categories");
  };
  elements.catalogHelp.textContent = "Artikelkataloge werden gemeinsam für alle Nutzer gespeichert. Alle angemeldeten HA-Nutzer können sie bearbeiten. Speichern benötigt eine Verbindung; Änderungen gelten für alle Nutzer.";
  if (catalogView === "products") {
    renderProductManagement();
  } else if (catalogView === "product-statistics") {
    renderProductStatistics();
  } else if (catalogView === "product-edit") {
    renderProductEdit();
  } else if (catalogView === "product-merge") {
    renderProductMerge();
  } else if (isList) {
    elements.catalogTitle.textContent = isMarket ? "Supermärkte" : "Produktkategorien";
    elements.catalogFixedActions.append(
      button("Abbrechen", leaveManagement),
      button("Hinzufügen", () => openCatalog(isMarket ? "market-edit" : "category-edit"), "primary")
    );
    elements.catalogFixedActions.hidden = false;
    const records = [...(isMarket ? supermarkets : categories)].sort((a, b) => nameOrder.compare(a.name, b.name));
    const list = document.createElement("div");
    list.className = "management-list";
    for (const record of records) {
      list.append(navigationButton(record.name, () => openCatalog(isMarket ? "market-edit" : "category-edit", record), "management-link"));
    }
    content.append(list);
    if (!records.length) content.append(paragraph(`Noch keine ${isMarket ? "Supermärkte" : "Produktkategorien"} angelegt.`));
  } else if (catalogView === "category-products") {
    elements.catalogTitle.textContent = "Zugeordnete Produkte";
    elements.catalogHelp.textContent = `${catalogDraft.name} · Dauerhafte Zuordnungen für alle Einkaufslisten, auch wenn das Produkt gerade nicht auf einer Liste steht. Entfernen löst nur die Kategoriezuordnung; Einkaufsartikel bleiben erhalten.`;
    const list = document.createElement("div");
    list.className = "management-list";
    const assigned = products.filter(product => product.category_id === catalogDraft.id)
      .sort((a, b) => nameOrder.compare(a.name, b.name));
    for (const product of assigned) {
      const row = document.createElement("div");
      row.className = "category-product-row";
      const name = document.createElement("span");
      name.textContent = product.name;
      const remove = button("Entfernen", () => requestAppConfirmation({
        title: "Produktzuordnung entfernen?",
        confirmLabel: "Entfernen",
        description: `„${product.name}“ dauerhaft aus der Kategorie „${catalogDraft.name}“ entfernen? Bestehende Einkaufsartikel bleiben erhalten und erscheinen ohne Kategorie. Auch beim erneuten Hinzufügen wird diese Kategorie nicht mehr automatisch zugeordnet.`,
        onConfirm: () => saveCatalog("remove_category_product", {
          category_id: catalogDraft.id,
          product_key: product.key,
        }, "category-products"),
      }));
      remove.setAttribute("aria-label", `Kategoriezuordnung entfernen: ${product.name}`);
      row.append(name, remove);
      list.append(row);
    }
    content.append(paragraph(catalogDraft.name, "market-context"), list);
    elements.catalogFixedActions.append(button("Zurück", () => openCatalog("category-edit", catalogDraft)));
    elements.catalogFixedActions.hidden = false;
    if (!assigned.length) content.append(paragraph("Dieser Kategorie sind noch keine Produkte zugeordnet."));
  } else if (catalogView === "market-order" || catalogView === "market-select") {
    renderMarketCategories();
  } else if (catalogView === "market-bonus-card") {
    renderMarketBonusCard();
  } else {
    elements.catalogTitle.textContent = `${isMarket ? noun : "Produktkategorie"} ${catalogDraft.id ? "bearbeiten" : "hinzufügen"}`;
    if (!isMarket) {
      elements.catalogHelp.textContent = "Kategoriename bearbeiten und zugeordnete Produkte verwalten. Speichern übernimmt den Namen für alle Nutzer. Löschen entfernt die Kategorie; die Produkte bleiben erhalten.";
    }
    const form = document.createElement("form");
    form.className = "management-form";
    const label = document.createElement("label");
    label.className = "visually-hidden";
    label.htmlFor = "catalog-name";
    label.textContent = isMarket ? "Supermarktname" : "Kategoriename";
    const input = document.createElement("input");
    input.id = "catalog-name";
    input.required = true;
    input.maxLength = 100;
    input.autocomplete = "off";
    input.value = catalogDraft.name;
    if (!catalogDraft.id) input.placeholder = isMarket ? "Neuer Supermarkt" : "Neue Kategorie";
    input.addEventListener("input", () => {
      input.setCustomValidity("");
      catalogDraft.name = input.value;
      catalogDirty = true;
    });
    form.append(label, input);
    if (!isMarket && catalogDraft.id) {
      form.append(navigationButton("Zugeordnete Produkte", () => {
        const category = categories.find(record => record.id === catalogDraft.id);
        if (!category) {
          setMessage(elements.catalogMessage, "Die Kategorie wurde inzwischen entfernt. Bitte die Kategorienübersicht neu öffnen.");
          return;
        }
        openCategoryProducts(category);
      }, "management-link category-navigation"));
    }
    if (isMarket && catalogDraft.id) {
      const openMarketOrder = () => {
        if (catalogDirty) {
          requestDiscardChanges(openMarketOrder);
          return;
        }
        catalogDirty = false;
        catalogDraft = { ...supermarkets.find(m => m.id === catalogDraft.id), category_ids: [...catalogDraft.category_ids] };
        catalogView = "market-order";
        renderCatalogPage();
      };
      form.append(navigationButton("Produktkategorien für diesen Markt bearbeiten", openMarketOrder, "management-link category-navigation"));
      form.append(navigationButton("Bonuskarten oder APP-Codes einbinden", () => {
        if (catalogDirty) {
          requestDiscardChanges(() => openCatalog("market-bonus-card", supermarkets.find(m => m.id === catalogDraft.id)));
          return;
        }
        openCatalog("market-bonus-card", supermarkets.find(m => m.id === catalogDraft.id));
      }, "management-link category-navigation"));
    }
    let customCatalogNameInput;
    if (isMarket) {
      const catalogPreview = document.createElement("details");
      catalogPreview.className = "market-catalog-preview";
      const summary = document.createElement("summary");
      const summaryText = document.createElement("span");
      summaryText.textContent = "Artikelkatalog";
      const currentCatalog = paragraph("Supermarkt", "market-catalog-current");
      summaryText.append(currentCatalog);
      summary.append(summaryText, chevron());
      const previewContent = document.createElement("div");
      previewContent.className = "market-catalog-preview-content";
      const picker = document.createElement("div");
      picker.className = "category-picker market-catalog-picker-control";
      const catalogLabel = document.createElement("p");
      catalogLabel.className = "market-catalog-picker-label";
      catalogLabel.id = "market-catalog-picker-label";
      catalogLabel.textContent = "Verwendeter Katalog";
      const pickerValue = document.createElement("span");
      pickerValue.id = "market-catalog-picker-value";
      pickerValue.textContent = "Supermarkt";
      const trigger = button("", () => {}, "category-picker-trigger");
      trigger.id = "market-catalog-picker-trigger";
      trigger.setAttribute("role", "combobox");
      trigger.setAttribute("aria-labelledby", `${catalogLabel.id} ${pickerValue.id}`);
      trigger.setAttribute("aria-expanded", "false");
      trigger.setAttribute("aria-haspopup", "listbox");
      trigger.setAttribute("aria-controls", "market-catalog-picker-options");
      trigger.append(pickerValue, chevron("category-picker-arrow", true));
      const flyout = document.createElement("div");
      flyout.id = "market-catalog-picker-flyout";
      flyout.className = "category-picker-flyout";
      flyout.hidden = true;
      const listbox = document.createElement("div");
      listbox.id = "market-catalog-picker-options";
      listbox.className = "category-options";
      listbox.setAttribute("role", "listbox");
      listbox.setAttribute("aria-labelledby", catalogLabel.id);
      const catalogChoices = [
        ...Object.values(catalogs).map(catalog => [catalog.id, catalog.name]),
        ["__new", "Neuen eigenen Katalog anlegen …"],
      ];
      let selectedCatalog = catalogDraft.catalog_id || "supermarket";
      const customLabel = document.createElement("label");
      customLabel.htmlFor = "market-catalog-custom-name";
      customLabel.textContent = "Name des eigenen Katalogs";
      customLabel.hidden = selectedCatalog !== "__new";
      const customName = document.createElement("input");
      customCatalogNameInput = customName;
      customName.id = "market-catalog-custom-name";
      customName.type = "text";
      customName.maxLength = 100;
      customName.placeholder = "z. B. Garten";
      customName.value = catalogDraft.catalog_name || "";
      customName.hidden = selectedCatalog !== "__new";
      const updateCatalogName = () => {
        const name = selectedCatalog === "__new"
          ? customName.value.trim() || "Eigener Katalog"
          : catalogs[selectedCatalog]?.name || "";
        pickerValue.textContent = name;
        currentCatalog.textContent = name;
      };
      const optionButtons = catalogChoices.map(([value, text]) => {
        const option = button("", () => {
          const previousCatalog = catalogDraft.catalog_id || "supermarket";
          selectedCatalog = value;
          catalogDraft.catalog_id = value;
          catalogDraft.catalog_name = value === "__new" ? customName.value : "";
          catalogDirty ||= previousCatalog !== value;
          customLabel.hidden = customName.hidden = value !== "__new";
          optionButtons.forEach(candidate => {
            const selected = candidate.dataset.catalogValue === value;
            candidate.setAttribute("aria-selected", String(selected));
            candidate.tabIndex = selected ? 0 : -1;
          });
          updateCatalogName();
          closePicker(true);
        }, "category-option");
        option.type = "button";
        option.setAttribute("role", "option");
        option.setAttribute("aria-selected", String(value === selectedCatalog));
        option.tabIndex = value === selectedCatalog ? 0 : -1;
        option.dataset.catalogValue = value;
        const name = document.createElement("span");
        name.className = "category-option-name";
        name.textContent = text;
        const check = document.createElement("span");
        check.className = "category-option-check";
        check.textContent = "✓";
        check.setAttribute("aria-hidden", "true");
        option.append(name, check);
        listbox.append(option);
        return option;
      });
      function closePicker(focusTrigger = false) {
        flyout.hidden = true;
        trigger.setAttribute("aria-expanded", "false");
        document.removeEventListener("pointerdown", handleOutsidePointerDown);
        if (focusTrigger) trigger.focus();
      }
      function handleOutsidePointerDown(event) {
        if (!picker.contains(event.target)) closePicker();
      }
      function openPicker() {
        flyout.hidden = false;
        trigger.setAttribute("aria-expanded", "true");
        document.addEventListener("pointerdown", handleOutsidePointerDown);
        (optionButtons.find(option => option.dataset.catalogValue === selectedCatalog) || optionButtons[0])?.focus();
      }
      trigger.addEventListener("click", () => {
        if (flyout.hidden) openPicker();
        else closePicker();
      });
      trigger.addEventListener("keydown", event => {
        if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
          event.preventDefault();
          if (flyout.hidden) openPicker();
        }
      });
      listbox.addEventListener("keydown", event => {
        const currentIndex = optionButtons.indexOf(document.activeElement);
        let nextIndex;
        if (event.key === "ArrowDown") nextIndex = Math.min(optionButtons.length - 1, currentIndex + 1);
        else if (event.key === "ArrowUp") nextIndex = Math.max(0, currentIndex - 1);
        else if (event.key === "Home") nextIndex = 0;
        else if (event.key === "End") nextIndex = optionButtons.length - 1;
        else if (event.key === "Escape") {
          event.preventDefault();
          closePicker(true);
          return;
        } else if (event.key === "Tab") {
          closePicker();
          return;
        } else return;
        event.preventDefault();
        optionButtons[nextIndex]?.focus();
      });
      customName.addEventListener("input", () => {
        catalogDraft.catalog_name = customName.value;
        catalogDirty = true;
        updateCatalogName();
      });
      flyout.append(listbox);
      picker.append(catalogLabel, trigger, flyout);
      previewContent.append(picker, customLabel, customName);
      updateCatalogName();
      catalogPreview.append(summary, previewContent);
      form.append(catalogPreview);
      const options = document.createElement("div");
      options.className = "market-checkout-options";
      for (const [key, text] of [
        ["deposit_receipt_hint", "Pfandbon Hinweis"],
        ["show_bonus_card", "Anzeige Bonuskarte"],
      ]) {
        const label = document.createElement("label");
        label.className = "market-checkout-option";
        const name = document.createElement("span");
        name.textContent = text;
        const toggle = document.createElement("input");
        toggle.type = "checkbox";
        toggle.id = `market-${key}`;
        toggle.className = "market-option-switch";
        toggle.setAttribute("role", "switch");
        toggle.checked = catalogDraft[key] !== false;
        toggle.addEventListener("change", () => {
          catalogDraft[key] = toggle.checked;
          catalogDirty = true;
        });
        label.append(name, toggle);
        options.append(label);
      }
      form.append(options);
    }
    if (catalogDraft.id) {
      const danger = document.createElement("section");
      danger.className = "danger-section";
      danger.append(button("Löschen", () => requestAppConfirmation({
        title: `${noun} löschen?`,
        description: isMarket
          ? `„${catalogDraft.name}“ endgültig für alle Nutzer aus der Marktauswahl entfernen? Einkaufslisten bleiben erhalten.`
          : `„${catalogDraft.name}“ endgültig für alle Nutzer löschen? Die Kategorie und ihre Marktzuordnungen werden entfernt. Artikel bleiben erhalten und erscheinen ohne Kategorie.`,
        onConfirm: () => saveCatalog(
          isMarket ? "delete_supermarket" : "delete_category",
          { [isMarket ? "market_id" : "category_id"]: catalogDraft.id },
          isMarket ? "markets" : "categories",
        ),
      }), "secondary danger-button"));
      form.append(danger);
    }
    const actions = document.createElement("div");
    actions.className = "page-actions";
    const save = button("Speichern", () => {});
    save.type = "submit";
    save.className = "primary";
    actions.append(button("Abbrechen", () => openCatalog(isMarket ? "markets" : "categories")), save);
    if (isMarket) form.append(actions);
    else appendCatalogFormActions(form, actions);
    form.addEventListener("submit", event => {
      event.preventDefault();
      if (!input.value.trim()) {
        input.setCustomValidity("Bitte gib einen Namen ein.");
        input.reportValidity();
        return;
      }
      let selectedCatalogId = catalogDraft.catalog_id || "supermarket";
      let selectedCatalogName = "";
      if (isMarket && selectedCatalogId === "__new") {
        selectedCatalogName = customCatalogNameInput.value.trim();
        if (!selectedCatalogName) {
          customCatalogNameInput.setCustomValidity("Bitte gib einen Namen für den eigenen Katalog ein.");
          customCatalogNameInput.reportValidity();
          return;
        }
        customCatalogNameInput.setCustomValidity("");
        selectedCatalogId = crypto.randomUUID().replaceAll("-", "");
      }
      saveCatalog(isMarket ? "save_supermarket" : "save_category",
        {
          [isMarket ? "market_id" : "category_id"]: catalogDraft.id,
          name: input.value.trim(),
          ...(isMarket ? {
            catalog_id: selectedCatalogId,
            ...(selectedCatalogName ? { catalog_name: selectedCatalogName } : {}),
            deposit_receipt_hint: catalogDraft.deposit_receipt_hint !== false,
            show_bonus_card: catalogDraft.show_bonus_card !== false,
          } : {}),
        },
        isMarket ? "markets" : "categories");
    });
    content.append(form);
  }
  elements.catalogHelpPopover.textContent = elements.catalogHelp.textContent;
  elements.catalogHelp.hidden = true;
  elements.catalogHelpTrigger.hidden = !elements.catalogHelp.textContent;
  setHelpPopover(elements.catalogHelpTrigger, elements.catalogHelpPopover, false);
  elements.catalogTitle.focus();
}

function leaveMarketCategorySelection(apply) {
  if (!apply && marketSelectionSnapshot) {
    catalogDraft.category_ids = [...marketSelectionSnapshot.categoryIds];
    catalogDirty = marketSelectionSnapshot.dirty;
  }
  marketSelectionSnapshot = null;
  catalogView = "market-order";
  renderCatalogPage();
}

function renderMarketBonusCard() {
  const content = elements.catalogContent;
  const market = supermarkets.find(value => value.id === catalogDraft.id);
  if (!market) {
    setMessage(elements.catalogMessage, "Der Supermarkt wurde inzwischen entfernt. Bitte die Übersicht neu öffnen.");
    return;
  }
  elements.catalogTitle.textContent = "Bonuskarte / APP-Code";
  elements.catalogHelp.textContent = `${catalogDraft.name} · Ein Bild wird gemeinsam in Home Assistant gespeichert und ist auf allen Geräten verfügbar.`;
  content.append(paragraph(catalogDraft.name, "market-context"));
  const form = document.createElement("form");
  form.className = "management-form bonus-card-form";
  const upload = document.createElement("input");
  upload.type = "file";
  upload.accept = "image/png,image/jpeg,image/webp";
  upload.className = "visually-hidden";
  upload.tabIndex = -1;
  const camera = document.createElement("input");
  camera.type = "file";
  camera.accept = "image/*";
  camera.setAttribute("capture", "environment");
  camera.className = "visually-hidden";
  camera.tabIndex = -1;
  const preview = document.createElement("img");
  preview.className = "bonus-card-preview";
  preview.alt = `Bonuskarte oder APP-Code für ${catalogDraft.name}`;
  preview.hidden = !catalogDraft.bonus_card;
  if (catalogDraft.bonus_card) preview.src = catalogDraft.bonus_card;
  const status = paragraph("PNG, JPEG oder WebP · maximal 512 KiB nach Bildoptimierung.", "management-help");
  const choose = button("Bild aus Dateien auswählen", () => upload.click(), "primary full-width");
  const takePhoto = button("QR-Code fotografieren", () => camera.click(), "secondary full-width");
  const removeSection = document.createElement("section");
  removeSection.className = "bonus-card-remove-section";
  const remove = button("Bild entfernen", () => {
    delete catalogDraft.bonus_card;
    preview.removeAttribute("src");
    preview.hidden = true;
    remove.hidden = true;
    removeSection.hidden = true;
    catalogDirty = true;
    status.textContent = "Bild entfernt. Speichere, um die Änderung zu übernehmen.";
  }, "secondary danger-button bonus-card-remove");
  remove.hidden = !catalogDraft.bonus_card;
  const processFile = async file => {
    if (!file) return;
    try {
      const image = await prepareImageData(file);
      catalogDraft.bonus_card = image;
      preview.src = image;
      preview.hidden = false;
      remove.hidden = false;
      removeSection.hidden = false;
      catalogDirty = true;
      status.textContent = "Bild bereit. Speichere, um es auf allen Geräten verfügbar zu machen.";
      setMessage(elements.catalogMessage, "");
    } catch (error) {
      setMessage(elements.catalogMessage, error.message);
    }
  };
  upload.addEventListener("change", () => processFile(upload.files[0]));
  camera.addEventListener("change", () => processFile(camera.files[0]));
  const actions = [
    button("Abbrechen", () => openCatalog("market-edit", supermarkets.find(value => value.id === catalogDraft.id))),
    button("Speichern", () => saveCatalog("save_market_bonus_card", {
      market_id: catalogDraft.id, bonus_card: catalogDraft.bonus_card || "",
    }, "market-edit"), "primary"),
  ];
  removeSection.append(remove);
  removeSection.hidden = remove.hidden;
  form.append(upload, camera, choose, takePhoto, preview, status, removeSection);
  content.append(form);
  elements.catalogFixedActions.append(...actions);
  elements.catalogFixedActions.hidden = false;
}

async function prepareImageData(file) {
  if (!/^image\/(?:png|jpeg|webp)$/.test(file.type) || file.size > MAX_IMAGE_INPUT_BYTES) {
    throw new Error("Bitte wähle ein PNG-, JPEG- oder WebP-Bild bis maximal 12 MiB.");
  }
  let bitmap;
  try {
    bitmap = await createImageBitmap(file);
    const sourceDimension = Math.max(bitmap.width, bitmap.height);
    const dimensions = [...new Set([1280, 1024, 768, 512].map(limit =>
      Math.max(1, Math.min(sourceDimension, limit))))];
    for (const dimension of dimensions) {
      const scale = dimension / sourceDimension;
      const canvas = document.createElement("canvas");
      canvas.width = Math.max(1, Math.round(bitmap.width * scale));
      canvas.height = Math.max(1, Math.round(bitmap.height * scale));
      const context = canvas.getContext("2d");
      if (!context) throw new Error("Bildverarbeitung ist in diesem Browser nicht verfügbar.");
      context.drawImage(bitmap, 0, 0, canvas.width, canvas.height);
      const candidates = [
        canvas.toDataURL("image/png"),
        ...[0.92, 0.86, 0.8].map(quality => canvas.toDataURL("image/webp", quality)),
      ];
      const image = candidates.find(value =>
        Math.ceil((value.length - value.indexOf(",") - 1) * 3 / 4) <= MAX_IMAGE_BYTES);
      if (image) return image;
    }
    throw new Error("Das Bild ist nach der Optimierung noch zu groß. Bitte wähle ein kleineres Bild.");
  } catch (error) {
    if (error instanceof Error && (
      error.message.includes("zu groß") || error.message.includes("nicht verfügbar")
    )) throw error;
    throw new Error("Das Bild konnte nicht gelesen oder optimiert werden.");
  } finally {
    bitmap?.close();
  }
}

function renderMarketCategories() {
  const content = elements.catalogContent;
  const selecting = catalogView === "market-select";
  elements.catalogTitle.textContent = selecting ? "Kategorien auswählen" : "Produktkategorien bearbeiten";
  elements.catalogHelp.textContent = selecting
    ? `Kategorien aus dem gemeinsamen Kategoriespeicher auswählen. Damit legst Du die verwendeten Produktgruppen bzw. Regale für ${catalogDraft.name} fest. Die Liste ist alphabetisch sortiert. Mit „Übernehmen“ kehrst du zur Reihenfolge dieses Marktes zurück.`
    : `${catalogDraft.name} · Diese Reihenfolge gilt nur für diesen Markt.`;
  if (!selecting) content.append(paragraph(catalogDraft.name, "market-context"));
  if (selecting) {
    const selected = new Set(catalogDraft.category_ids);
    for (const category of [...categories].sort((a, b) => nameOrder.compare(a.name, b.name))) {
      const label = document.createElement("label");
      label.className = "category-choice";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.checked = selected.has(category.id);
      checkbox.addEventListener("change", () => {
        if (checkbox.checked) {
          const uncategorizedIndex = catalogDraft.category_ids.indexOf("");
          const insertAt = uncategorizedIndex === catalogDraft.category_ids.length - 1
            ? uncategorizedIndex
            : catalogDraft.category_ids.length;
          catalogDraft.category_ids.splice(insertAt, 0, category.id);
        } else {
          catalogDraft.category_ids = catalogDraft.category_ids.filter(id => id !== category.id);
        }
        catalogDirty = true;
      });
      label.append(checkbox, document.createTextNode(category.name));
      content.append(label);
    }
    if (!categories.length) content.append(paragraph("Noch keine Kategorien im Speicher. Bitte zuerst unter Produktkategorien verwalten anlegen."));
    elements.catalogFixedActions.append(
      button("Abbrechen", () => leaveMarketCategorySelection(false)),
      button("Übernehmen", () => leaveMarketCategorySelection(true), "primary"),
    );
    elements.catalogFixedActions.hidden = false;
    return;
  }
  const categorySelection = navigationButton("Kategorien für diesen Markt", () => {
    marketSelectionSnapshot = {
      categoryIds: [...catalogDraft.category_ids],
      dirty: catalogDirty,
    };
    catalogView = "market-select";
    renderCatalogPage();
  }, "management-link category-selection-button");
  content.append(categorySelection);
  if (!catalogDraft.category_ids.includes("")) catalogDraft.category_ids.push("");
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
    if (id && !category) return;
    const categoryName = id ? category.name : "Ohne Kategorie";
    const row = document.createElement("li");
    row.className = "category-order-row";
    row.dataset.categoryId = id;
    const position = () => catalogDraft.category_ids.indexOf(id);
    const grip = button("⠿", () => {}, "text-button move-grip");
    grip.setAttribute("aria-label", `${categoryName} verschieben; Pfeiltasten hoch und runter`);
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
    name.textContent = `${index + 1}. ${categoryName}`;
    const up = button("↑", () => move(position(), position() - 1), "secondary move-button");
    up.disabled = index === 0;
    up.setAttribute("aria-label", `${categoryName} nach oben`);
    const down = button("↓", () => move(position(), position() + 1), "secondary move-button");
    down.disabled = index === catalogDraft.category_ids.length - 1;
    down.setAttribute("aria-label", `${categoryName} nach unten`);
    row.append(grip, name, up, down);
    if (id) {
      const remove = button("×", () => {
        catalogDraft.category_ids = catalogDraft.category_ids.filter(key => key !== id);
        catalogDirty = true;
        renderCatalogPage();
      }, "text-button move-button");
      remove.setAttribute("aria-label", `${categoryName} aus diesem Markt entfernen`);
      row.append(remove);
    } else {
      const spacer = document.createElement("span");
      spacer.className = "move-button";
      spacer.setAttribute("aria-hidden", "true");
      row.append(spacer);
    }
    list.append(row);
  });
  content.append(list);
  initializeCategorySorting(list);
  if (!catalogDraft.category_ids.some(Boolean)) content.append(paragraph("Noch keine Kategorien für diesen Markt ausgewählt."));
  elements.catalogFixedActions.append(button("Abbrechen", () => openCatalog("market-edit", supermarkets.find(m => m.id === catalogDraft.id))),
    button("Speichern", () => saveCatalog("save_market_categories", {
      market_id: catalogDraft.id, category_ids: catalogDraft.category_ids,
    }, "markets"), "primary"));
  elements.catalogFixedActions.hidden = false;
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
      const id = row.dataset.categoryId;
      const category = categories.find(value => value.id === id);
      row.querySelector(".order-name").textContent = `${index + 1}. ${id ? category.name : "Ohne Kategorie"}`;
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
      grip, row, id: row.dataset.categoryId,
      name: row.dataset.categoryId ? categories.find(value => value.id === row.dataset.categoryId).name : "Ohne Kategorie",
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
elements.manageProducts.addEventListener("click", () => loadCatalogPage("products"));
elements.confirmProductMerge.addEventListener("click", () => {
  if (!pendingProductMerge) return;
  const payload = pendingProductMerge;
  pendingProductMerge = undefined;
  elements.productMergeConfirm.close();
  saveCatalog("merge_product", payload, "products");
});
elements.productMergeConfirm.addEventListener("close", () => {
  if (elements.productMergeConfirm.returnValue !== "confirm") pendingProductMerge = undefined;
});
document.querySelector("#lists-back").addEventListener("click", leaveManagement);
window.addEventListener("beforeunload", event => {
  if (catalogDirty || managingSupermarkets) { event.preventDefault(); event.returnValue = ""; }
});

let planningViewportWidth = window.innerWidth;
let planningViewportHeight = window.innerHeight;

function fitPlanningDock() {
  const app = document.querySelector("main.app");
  const viewport = window.visualViewport;
  if (planningViewportWidth !== window.innerWidth) {
    planningViewportWidth = window.innerWidth;
    planningViewportHeight = window.innerHeight;
  }
  planningViewportHeight = Math.max(planningViewportHeight, window.innerHeight);
  const visibleHeight = viewport ? viewport.height : window.innerHeight;
  const keyboardOpen = planningViewportHeight - visibleHeight > 150 &&
    (document.activeElement === elements.newItem || elements.addForm.classList.contains("keyboard-open"));
  elements.addForm.classList.toggle("keyboard-open", keyboardOpen);
  const visibleBottom = viewport ? viewport.offsetTop + viewport.height : window.innerHeight;
  const offset = Math.max(0, window.innerHeight - visibleBottom);
  elements.addForm.style.setProperty("--planning-dock-offset", `${offset}px`);
  const height = elements.addForm.getBoundingClientRect().height;
  if (height) app.style.setProperty("--planning-dock-height", `${height}px`);
  elements.addForm.style.setProperty("--planning-suggestion-height", `${Math.max(0, visibleHeight - height - 16)}px`);
}

window.addEventListener("resize", fitPlanningDock);
elements.newItem.addEventListener("focus", fitPlanningDock);
window.visualViewport?.addEventListener("resize", fitPlanningDock);
window.visualViewport?.addEventListener("scroll", fitPlanningDock);
new ResizeObserver(fitPlanningDock).observe(elements.addForm);

function updateModeView() {
  elements.addForm.hidden = !planningMode;
  document.querySelector("main.app").classList.toggle("planning-mode", planningMode);
  fitPlanningDock();
  closeProductSuggestions();
  const action = planningMode ? "Einkaufen" : "Weiter planen";
  const mode = planningMode ? "Planungsmodus" : "Einkaufsmodus";
  elements.modeToggle.setAttribute("aria-label", `${action} – aktuell ${mode}`);
  elements.modeToggle.title = `${mode} · ${action}`;
  elements.modeToggle.querySelector("svg").innerHTML = planningMode
    ? '<path d="M3 3h2l3 12h11l2-8H6"/><circle cx="9" cy="20" r="1"/><circle cx="18" cy="20" r="1"/>'
    : '<path d="m15 5 4 4M4 20l4-1L20 7a2.8 2.8 0 0 0-4-4L4 15z"/>';
}

function initializeMode() {
  try {
    const mode = localStorage.getItem(MODE_KEY) || "planning";
    if (!["planning", "shopping"].includes(mode)) {
      throw new Error("Der gespeicherte Ansichtsmodus ist unbekannt. Bitte wähle den Modus erneut.");
    }
    planningMode = mode === "planning";
  } catch (error) {
    showError(error);
  }
  updateModeView();
}

elements.modeToggle.addEventListener("click", () => {
  planningMode = !planningMode;
  updateModeView();
  render();
  try {
    localStorage.setItem(MODE_KEY, planningMode ? "planning" : "shopping");
  } catch (error) {
    showError(new Error(`Der Ansichtsmodus konnte nicht auf diesem Gerät gespeichert werden: ${error.message}`));
  }
});

const additionalDesigns = [
  ["deep-ocean", "Deep Ocean", "dark", "#67dfed"],
  ["copper-night", "Copper Night", "dark", "#eeb184"],
  ["arctic-graphite", "Arctic Graphite", "dark", "#b4d5ee"],
  ["velvet-berry", "Velvet Berry", "dark", "#f2a9d1"],
  ["petrol-brass", "Petrol Brass", "dark", "#e1cd87"],
  ["cobalt-ink", "Cobalt Ink", "dark", "#9fbaff"],
  ["olive-stone", "Olive Stone", "dark", "#d6db9d"],
  ["espresso-cream", "Espresso Cream", "dark", "#ead4b8"],
  ["porcelain-blue", "Porcelain Blue", "light", "#2456a6"],
  ["sage-paper", "Sage Paper", "light", "#446536"],
  ["warm-linen", "Warm Linen", "light", "#9b492e"],
  ["rose-quartz", "Rose Quartz", "light", "#963b68"],
  ["glacier-mint", "Glacier Mint", "light", "#17695c"],
  ["lavender-mist", "Lavender Mist", "light", "#7046a2"],
  ["sand-sea", "Sand & Sea", "light", "#216779"],
  ["lemon-notebook", "Lemon Notebook", "light", "#74600e"],
  ["skyline", "Skyline", "light", "#21638b"],
  ["apricot-studio", "Apricot Studio", "light", "#a04729"],
  ["pistachio", "Pistachio", "light", "#486526"],
  ["nordic-grey", "Nordic Grey", "light", "#40586d"],
  ["lilac-ink", "Lilac & Ink", "light", "#574181"],
  ["coral-chalk", "Coral Chalk", "light", "#ad4035"],
  ["aqua-glass", "Aqua Glass", "light", "#176878"],
  ["ivory-burgundy", "Ivory Burgundy", "light", "#823b52"],
];
const lastDesigns = { dark: "mono", light: "porcelain-blue" };
for (const [theme, name, mode, accent] of additionalDesigns) {
  const label = document.createElement("label");
  label.className = "design-row";
  const input = document.createElement("input");
  input.type = "radio";
  input.name = "design";
  input.value = theme;
  input.dataset.mode = mode;
  const swatch = document.createElement("span");
  swatch.className = "design-swatch";
  swatch.style.setProperty("--swatch", accent);
  swatch.setAttribute("aria-hidden", "true");
  const text = document.createElement("span");
  text.textContent = name;
  const check = document.createElement("span");
  check.className = "design-check";
  check.textContent = "✓";
  check.setAttribute("aria-hidden", "true");
  label.hidden = mode === "light";
  label.append(input, swatch, text, check);
  elements.designOptions.append(label);
}

function designOption(theme) {
  const option = [...elements.designOptions.querySelectorAll("input")].find(input => input.value === theme);
  if (!option) {
    throw new Error("Das gespeicherte Farbschema ist unbekannt. Bitte wähle unter Menü → Design ein neues aus.");
  }
  return option;
}

function applyDesign(theme) {
  const selected = designOption(theme);
  const mode = selected.dataset.mode || "dark";
  document.body.dataset.theme = theme;
  document.body.dataset.colorMode = mode;
  lastDesigns[mode] = theme;
  for (const input of document.querySelectorAll('#design-mode input')) {
    input.checked = input.value === mode;
  }
  for (const option of elements.designOptions.querySelectorAll("input")) {
    option.checked = option.value === theme;
    option.parentElement.hidden = (option.dataset.mode || "dark") !== mode;
    if (option.checked) elements.designName.textContent = option.parentElement.querySelector("span:not([aria-hidden])").textContent;
  }
  document.querySelector('meta[name="theme-color"]').content =
    getComputedStyle(document.body).getPropertyValue("--bg").trim();
}

function initializeDesign() {
  try {
    for (const mode of ["dark", "light"]) {
      const remembered = localStorage.getItem(`${DESIGN_KEY}.${mode}`);
      if (remembered) {
        if ((designOption(remembered).dataset.mode || "dark") !== mode) {
          throw new Error("Das gespeicherte Farbschema passt nicht zur Helligkeit. Bitte wähle unter Menü → Design ein neues aus.");
        }
        lastDesigns[mode] = remembered;
      }
    }
    const theme = localStorage.getItem(DESIGN_KEY) || "mono";
    applyDesign(theme);
  } catch (error) {
    showError(error);
  }
}

function saveDesign(theme) {
  applyDesign(theme);
  setMessage(elements.designMessage, "");
  try {
    localStorage.setItem(DESIGN_KEY, theme);
    localStorage.setItem(`${DESIGN_KEY}.${document.body.dataset.colorMode}`, theme);
  } catch (error) {
    const message = `Das Farbschema konnte nicht auf diesem Gerät gespeichert werden: ${error.message}`;
    setMessage(elements.designMessage, message);
    showError(new Error(message));
  }
}

elements.designOptions.addEventListener("change", event => saveDesign(event.target.value));
document.querySelector("#design-mode").addEventListener("change", event => {
  saveDesign(lastDesigns[event.target.value]);
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
          .filter((operation) => listId === null || operation.entry_id === listId)
          .sort((a, b) => a.created_at - b.created_at || a.id.localeCompare(b.id)),
      );
    };
    request.onerror = () => reject(request.error);
  });
}

async function enqueue(operation, listId = entryId) {
  if (!listId) throw new Error("Bitte wähle zuerst eine Einkaufsliste aus.");
  const queuedOperation = operation.type === "add_item"
    ? {
      ...operation,
      metadata: { ...operation.metadata, catalog_id: operation.metadata?.catalog_id || activeCatalogId },
    }
    : operation;
  const queued = {
    ...queuedOperation,
    id: crypto.randomUUID(),
    entry_id: listId,
    created_at: (lastOperationTime = Math.max(Date.now(), lastOperationTime + 1)),
    product_name: operation.summary || currentItems.find(item => item.uid === operation.uid)?.summary,
  };
  await withLocalState(async () => {
    await storeRequest("operations", "put", queued);
    if (entryId === listId) {
      pendingOperations.push(queued);
      applyLocalOperation(queued);
      cacheCatalog();
      render();
      updateConnection("pending");
    }
  });
  if (authenticated) scheduleSynchronization();
}

function applyLocalOperation(operation) {
  if (deletedUids.has(operation.uid)) return;
  if (operation.type === "add_item") {
    const itemCatalogId = operation.metadata?.catalog_id || "supermarket";
    const itemCatalog = catalogs[itemCatalogId];
    const key = itemCatalog?.product_aliases?.[productNameKey(operation.summary)] || productNameKey(operation.summary);
    const known = itemCatalog?.products.find(product => product.key === key);
    if (itemCatalogId === activeCatalogId) {
      rememberProduct(operation.summary, known?.category_id ?? null, known ? known.category_known !== false : false);
    }
    if (!currentItems.some((item) => item.uid === operation.uid)) {
      currentItems.push({
        uid: operation.uid,
        summary: operation.summary,
        status: "needs_action",
        metadata: operation.metadata || {},
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
  if (operation.type !== "delete_item" && Object.hasOwn(operation.metadata || {}, "category_id")) {
    const item = currentItems.find(item => item.uid === operation.uid);
    if (item && (item.metadata?.catalog_id || "supermarket") === activeCatalogId) {
      rememberProduct(item.summary, operation.metadata.category_id);
    }
  }
  applyProductCategories();
}

function enableItemLongPress(label, openDetails) {
  let press = null;
  function cancelPress() {
    if (press) window.clearTimeout(press.timer);
    press = null;
  }
  label.addEventListener("pointerdown", event => {
    cancelPress();
    if (busy || event.button !== 0 || !event.isPrimary) return;
    press = { id: event.pointerId, type: event.pointerType, x: event.clientX, y: event.clientY };
    press.timer = window.setTimeout(() => {
      const { id, type } = press;
      cancelPress();
      if (label.isConnected && !busy && !document.hidden) {
        if (type === "touch") longPressTouchPointerId = id;
        openDetails();
      }
    }, 500);
  });
  label.addEventListener("pointermove", event => {
    if (press && event.pointerId === press.id &&
        Math.hypot(event.clientX - press.x, event.clientY - press.y) >= 10) cancelPress();
  });
  for (const type of ["pointerup", "pointercancel", "pointerleave", "lostpointercapture"]) {
    label.addEventListener(type, cancelPress);
  }
  label.addEventListener("contextmenu", event => event.preventDefault());
  label.addEventListener("click", event => {
    if (event.detail === 0 && !busy) openDetails();
  });
}

function openEndShoppingConfirmation(touchGated = false) {
  if (elements.endShoppingDialog.open) return;
  const gateDialog = touchGated && longPressTouchPointerId !== null;
  elements.endShoppingDialog.returnValue = "";
  elements.endShoppingDialog.inert = gateDialog;
  elements.endShoppingDialog.classList.toggle("touch-gated", gateDialog);
  elements.endShoppingDialog.showModal();
  longPressTouchDialog = gateDialog ? elements.endShoppingDialog : null;
  if (!gateDialog) elements.endShoppingCancel.focus({ preventScroll: true });
}

function openCashierReminder(touchGated = false) {
  if (elements.cashierReminder.open) return;
  const gateDialog = touchGated && longPressTouchPointerId !== null;
  const market = supermarkets.find(value => value.id === selectedMarket);
  const showReceipt = market?.deposit_receipt_hint !== false;
  const showCard = market?.show_bonus_card !== false && !!market?.bonus_card;
  if (!showReceipt && !showCard) {
    openEndShoppingConfirmation(touchGated);
    return;
  }
  document.querySelector("#cashier-reminder-title").textContent = showReceipt
    ? "Pfandbon nicht vergessen!" : "Bonuskarte / APP-Code";
  document.querySelector("#cashier-reminder-description").hidden = !showReceipt;
  elements.cashierBonusCard.hidden = !showCard;
  if (showCard) {
    elements.cashierBonusCardImage.src = market.bonus_card;
    elements.cashierBonusCardImage.alt = `Bonuskarte oder APP-Code für ${market.name}`;
  } else {
    elements.cashierBonusCardImage.removeAttribute("src");
  }
  elements.cashierReminder.returnValue = "";
  elements.cashierReminder.inert = gateDialog;
  elements.cashierReminder.classList.toggle("touch-gated", gateDialog);
  elements.cashierReminder.showModal();
  longPressTouchDialog = gateDialog ? elements.cashierReminder : null;
  if (!gateDialog) elements.cashierReminderOk.focus({ preventScroll: true });
}

elements.cashierReminder.addEventListener("close", () => {
  elements.cashierReminder.classList.remove("touch-gated");
  elements.cashierReminder.inert = false;
});

elements.cashierReminderOk.addEventListener("click", event => {
  event.preventDefault();
  elements.cashierReminder.close();
  openEndShoppingConfirmation();
});

function enableEndShoppingLongPress(button) {
  let press = null;
  function cancelPress() {
    if (press) window.clearTimeout(press.timer);
    press = null;
  }
  button.addEventListener("pointerdown", event => {
    cancelPress();
    if (busy || planningMode || event.button !== 0 || !event.isPrimary) return;
    press = { id: event.pointerId, type: event.pointerType, x: event.clientX, y: event.clientY };
    press.timer = window.setTimeout(() => {
      const { id, type } = press;
      cancelPress();
      if (!button.isConnected || busy || planningMode || document.hidden) return;
      suppressLongPressClick = true;
      if (type === "touch") longPressTouchPointerId = id;
      openCashierReminder(type === "touch");
    }, 550);
  });
  button.addEventListener("pointermove", event => {
    if (press && event.pointerId === press.id &&
        Math.hypot(event.clientX - press.x, event.clientY - press.y) >= 10) cancelPress();
  });
  for (const type of ["pointerup", "pointercancel", "pointerleave", "lostpointercapture"]) {
    button.addEventListener(type, cancelPress);
  }
  button.addEventListener("contextmenu", event => event.preventDefault());
}

elements.endShoppingConfirm.addEventListener("click", () => {
  const completedItems = currentItems
    .filter(item => item.status === "completed")
    .map(item => ({ type: "delete_item", uid: item.uid }));
  (async () => {
    for (const operation of completedItems) await enqueue(operation);
  })().catch(showError);
});

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
  applyProductCategories();
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
  const uncategorized = { id: "", name: "Ohne Kategorie" };
  const displayCategories = planningMode ? [uncategorized, ...sortedCategories] : [...sortedCategories];
  if (!planningMode) {
    const uncategorizedOrder = order.indexOf("");
    if (uncategorizedOrder < 0) {
      displayCategories.push(uncategorized);
    } else {
      const insertAt = sortedCategories.findIndex(category => {
        const categoryOrder = order.indexOf(category.id);
        return categoryOrder < 0 || categoryOrder > uncategorizedOrder;
      });
      displayCategories.splice(insertAt < 0 ? displayCategories.length : insertAt, 0, uncategorized);
    }
  }
  for (const category of displayCategories) {
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
    label.dataset.uid = item.uid;
    const title = document.createElement("span");
    title.className = "item-title";
    const summary = document.createElement("span");
    summary.textContent = item.summary;
    title.append(summary);
    label.append(title);
    const hasPhoto = Boolean(item.metadata?.image);
    const details = [item.metadata?.quantity, ...(hasPhoto ? [] : [item.description])]
      .filter(Boolean).join(" · ");
    if (hasPhoto) {
      const photoMeta = document.createElement("span");
      photoMeta.className = "item-photo-meta";
      if (details) {
        const note = document.createElement("span");
        note.className = "item-note";
        note.textContent = details;
        photoMeta.append(note);
      }
      label.append(photoMeta);
      label.classList.add("has-photo");
      const photoButton = document.createElement("button");
      photoButton.type = "button";
      photoButton.className = "item-photo-button";
      photoButton.setAttribute("aria-label", `Foto von ${item.summary} anzeigen`);
      photoButton.append(itemPhotoIcon());
      photoButton.addEventListener("click", () => openItemPhoto(item));
      main.classList.add("has-photo");
      main.append(checkbox, label, photoButton);
    } else if (details) {
      const note = document.createElement("span");
      note.className = "item-note";
      note.textContent = details;
      label.append(note);
      label.classList.add("has-note");
    }
    label.setAttribute("aria-label", `Bearbeiten: ${item.summary}`);
    label.setAttribute("aria-description", "Zum Bearbeiten lange drücken oder Enter bzw. die Leertaste drücken. Zum Löschen nach links wischen oder die Entf-Taste drücken.");
    label.setAttribute("aria-keyshortcuts", "Delete");
    enableItemLongPress(label, () => {
      editingUid = item.uid;
      elements.editSummary.value = item.summary;
      elements.editQuantity.value = item.metadata?.quantity || "";
      elements.editNotes.value = item.description || "";
      closeEditCategoryFlyout();
      elements.editCategoryOptions.replaceChildren();
      const editCategories = [
        { id: "", name: "Ohne Kategorie" },
        ...[...categories].sort((a, b) => nameOrder.compare(a.name, b.name)),
      ];
      for (const category of editCategories) {
        const option = document.createElement("button");
        option.type = "button";
        option.className = "category-option";
        option.setAttribute("role", "option");
        option.dataset.categoryId = category.id;
        option.dataset.categoryName = category.name;
        option.setAttribute("aria-selected", "false");
        option.tabIndex = -1;
        const name = document.createElement("span");
        name.className = "category-option-name";
        name.textContent = category.name;
        const check = document.createElement("span");
        check.className = "category-option-check";
        check.textContent = "✓";
        check.setAttribute("aria-hidden", "true");
        option.append(name, check);
        elements.editCategoryOptions.append(option);
      }
      const categoryId = item.metadata?.category_id || "";
      editingImageRequest++;
      editingImage = item.metadata?.image || null;
      elements.editImageUpload.value = "";
      elements.editImageCamera.value = "";
      elements.editImageMessage.textContent = "";
      elements.editImageMessage.dataset.status = "";
      elements.editItemForm.querySelector('[type="submit"]').disabled = false;
      elements.editImagePreview.hidden = !editingImage;
      if (editingImage) elements.editImagePreview.src = editingImage;
      else elements.editImagePreview.removeAttribute("src");
      elements.editImageRemove.hidden = !editingImage;
      elements.editCategory.value = categoryId;
      const currentCategory = categories.find(category => category.id === categoryId);
      elements.editCategoryValue.textContent = currentCategory?.name ||
        (categoryId ? "Nicht verfügbare Kategorie" : "Ohne Kategorie");
      elements.editCategoryUnavailable.hidden = !categoryId || !!currentCategory;
      elements.editCategorySearch.value = "";
      elements.editCategoryOptions.querySelectorAll(".category-option").forEach(option => {
        const selected = option.dataset.categoryId === categoryId;
        option.setAttribute("aria-selected", String(selected));
        option.tabIndex = selected ? 0 : -1;
        option.hidden = false;
        option.addEventListener("click", () => {
          elements.editCategory.value = option.dataset.categoryId;
          elements.editCategoryValue.textContent = option.dataset.categoryName;
          elements.editCategoryOptions.querySelectorAll(".category-option").forEach(candidate => {
            const selected = candidate === option;
            candidate.setAttribute("aria-selected", String(selected));
            candidate.tabIndex = selected ? 0 : -1;
          });
          closeEditCategoryFlyout(true);
        });
      });
      elements.editCategoryUnavailable.textContent = categoryId && !currentCategory
        ? "Diese Kategorie ist nicht mehr verfügbar. Wähle eine andere Kategorie oder „Ohne Kategorie“."
        : "";
      elements.editCategoryEmpty.hidden = true;
      editingCategory = categoryId;
      editingTrigger = label;
      const touchGated = longPressTouchPointerId !== null;
      elements.editItem.inert = touchGated;
      elements.editItem.classList.toggle("touch-gated", touchGated);
      elements.editItem.showModal();
      longPressTouchDialog = touchGated ? elements.editItem : null;
      if (!touchGated) elements.editItemTitle.focus({ preventScroll: true });
    });
    label.addEventListener("keydown", event => {
      if (event.key !== "Delete") return;
      event.preventDefault();
      requestAppConfirmation({
        title: "Artikel löschen?",
        description: `„${item.summary}“ wirklich aus der Einkaufsliste löschen?`,
        onConfirm: () => enqueue({ type: "delete_item", uid: item.uid }).catch(showError),
      });
    });
    if (pendingIds.has(item.uid)) label.title = "Lokal gespeichert – Übertragung an Home Assistant ausstehend";
    if (!hasPhoto) main.append(checkbox, label);
    row.append(main);
    enableItemSwipeDelete(row, item.uid);
    const categoryId = categories.some(c => c.id === item.metadata?.category_id) ? item.metadata.category_id : "";
    groupLists.get(categoryId).append(row);
  }
  elements.empty.hidden = currentItems.length > 0;
  if (!planningMode) {
    const endShoppingItem = elements.endShoppingTemplate.content.cloneNode(true);
    const endShoppingAction = endShoppingItem.querySelector(".end-shopping-action");
    enableEndShoppingLongPress(endShoppingAction);
    endShoppingAction.addEventListener("click", event => {
      if (busy || planningMode) return;
      if (event.detail !== 0) {
        event.preventDefault();
        return;
      }
      openCashierReminder();
    });
    elements.items.append(endShoppingItem);
  }
  elements.syncDetail.textContent = pendingOperations.length
    ? `${pendingOperations.length} Änderung${pendingOperations.length === 1 ? "" : "en"} ausstehend`
    : syncPromise ? "Listen werden im Hintergrund abgeglichen. Du kannst weiter einkaufen."
      : "Liste ist auf diesem Gerät gespeichert.";
  setBusy(busy);
  renderProductSuggestions();
  if (elements.commonItemsDialog.open) {
    if (entryId !== commonItemsListId) closeCommonItems();
    else renderCommonItems();
  }
}

function drawSyncSpinner(seconds) {
  const paths = elements.sync.querySelectorAll(".sync-spinner path");
  const phase = (seconds / 1.8) % 1;
  const angle = seconds / 1.8 * Math.PI * 2 - Math.PI / 2;
  const length = .4 + (.5 - .5 * Math.cos(phase * Math.PI * 2)) * 1.7;
  for (let i = 0; i < 2; i++) {
    const start = angle + i * Math.PI, end = start + length;
    const x = 12 + 8 * Math.cos(end), y = 12 + 8 * Math.sin(end);
    paths[i * 2]?.setAttribute("d", `M${12 + 8 * Math.cos(start)} ${12 + 8 * Math.sin(start)} A8 8 0 0 1 ${x} ${y}`);
    const tx = -Math.sin(end), ty = Math.cos(end), nx = Math.cos(end), ny = Math.sin(end);
    paths[i * 2 + 1]?.setAttribute("d", `M${x - tx * 2.3 + nx * 2} ${y - ty * 2.3 + ny * 2} L${x} ${y} L${x - tx * 2.3 - nx * 2} ${y - ty * 2.3 - ny * 2}`);
  }
}

function updateSyncAnimation() {
  const active = startupConnecting || !!syncPromise || !!listRefreshPromise;
  if (reducedSyncMotion.matches || (!active && syncAnimationFrame === undefined)) {
    window.cancelAnimationFrame(syncAnimationFrame);
    syncAnimationFrame = undefined;
    syncAnimationFinishAt = undefined;
    elements.syncActions.classList.toggle("syncing", active);
    drawSyncSpinner(.9);
    return;
  }
  elements.syncActions.classList.add("syncing");
  if (!active) {
    if (syncAnimationFinishAt === undefined) {
      const elapsed = (performance.now() - syncAnimationStarted) / 1000 + .3;
      syncAnimationFinishAt = .9 + Math.max(0, Math.ceil((elapsed - .9) / 1.8)) * 1.8;
    }
    return;
  }
  syncAnimationFinishAt = undefined;
  if (syncAnimationFrame !== undefined) return;
  syncAnimationStarted = performance.now();
  const animate = timestamp => {
    const elapsed = (timestamp - syncAnimationStarted) / 1000 + .3;
    if (syncAnimationFinishAt !== undefined && elapsed >= syncAnimationFinishAt) {
      syncAnimationFrame = undefined;
      syncAnimationFinishAt = undefined;
      elements.syncActions.classList.remove("syncing");
      drawSyncSpinner(.9);
      return;
    }
    drawSyncSpinner(elapsed);
    syncAnimationFrame = window.requestAnimationFrame(animate);
  };
  drawSyncSpinner(.3);
  syncAnimationFrame = window.requestAnimationFrame(animate);
}

function setBusy(value) {
  busy = value;
  if (value) closeProductSuggestions();
  const blocked = value;
  elements.listSelect.disabled = blocked || !availableLists.length;
  if (elements.listSelect.disabled) closeFlyout(elements.listSelect, elements.listFlyout);
  elements.marketSelect.disabled = blocked || !entryId;
  if (elements.marketSelect.disabled) closeFlyout(elements.marketSelect, elements.marketFlyout);
  elements.addForm.inert = blocked || !entryId;
  elements.sync.disabled = blocked || !!syncPromise || !!listRefreshPromise;
  updateSyncAnimation();
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

function closeEditCategoryFlyout(focus = false) {
  elements.editCategoryFlyout.hidden = true;
  elements.editCategoryTrigger.setAttribute("aria-expanded", "false");
  if (focus) elements.editCategoryTrigger.focus();
}

function openEditCategoryFlyout() {
  elements.editCategorySearch.value = "";
  elements.editCategoryOptions.querySelectorAll(".category-option").forEach(option => {
    option.hidden = false;
  });
  elements.editCategoryEmpty.hidden = true;
  elements.editCategoryFlyout.hidden = false;
  elements.editCategoryTrigger.setAttribute("aria-expanded", "true");
}

elements.editCategoryTrigger.addEventListener("click", () => {
  if (elements.editCategoryFlyout.hidden) openEditCategoryFlyout();
  else closeEditCategoryFlyout();
});
elements.editCategoryTrigger.addEventListener("keydown", event => {
  if (event.key !== "ArrowDown" && event.key !== "ArrowUp") return;
  event.preventDefault();
  if (elements.editCategoryFlyout.hidden) openEditCategoryFlyout();
  const selected = elements.editCategoryOptions.querySelector('[aria-selected="true"]:not([hidden])');
  (selected || elements.editCategoryOptions.querySelector(".category-option:not([hidden])"))?.focus();
});
elements.editCategoryOptions.addEventListener("keydown", event => {
  const options = [...elements.editCategoryOptions.querySelectorAll(".category-option:not([hidden])")];
  if (!options.length || !["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) return;
  event.preventDefault();
  const current = options.indexOf(document.activeElement);
  const next = event.key === "Home" ? 0 : event.key === "End" ? options.length - 1 :
    (current + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length;
  options[next].focus();
});
elements.editCategoryOptions.addEventListener("click", event => {
  if (event.target.closest(".category-option")) return;
  closeEditCategoryFlyout();
});
elements.editCategorySearch.addEventListener("input", () => {
  const query = elements.editCategorySearch.value.trim().toLocaleLowerCase("de");
  let visible = 0;
  for (const option of elements.editCategoryOptions.querySelectorAll(".category-option")) {
    option.hidden = !option.dataset.categoryName.toLocaleLowerCase("de").includes(query);
    if (!option.hidden) visible += 1;
  }
  elements.editCategoryEmpty.hidden = visible > 0;
});
elements.editCategorySearch.addEventListener("keydown", event => {
  if (event.key === "ArrowDown") {
    const first = elements.editCategoryOptions.querySelector(".category-option:not([hidden])");
    if (first) {
      event.preventDefault();
      first.focus();
    }
  }
});
elements.editCategoryPicker.addEventListener("focusout", event => {
  if (!elements.editCategoryPicker.contains(event.relatedTarget)) closeEditCategoryFlyout();
});
document.addEventListener("click", event => {
  if (!elements.editCategoryPicker.contains(event.target)) closeEditCategoryFlyout();
});
elements.editItem.addEventListener("keydown", event => {
  if (event.key === "Escape" && !elements.editCategoryFlyout.hidden) {
    event.preventDefault();
    event.stopPropagation();
    closeEditCategoryFlyout(true);
  }
});
elements.editItem.addEventListener("close", () => {
  closeEditCategoryFlyout();
  const trigger = editingTrigger?.isConnected
    ? editingTrigger
    : [...elements.items.querySelectorAll(".item-name")].find(label => label.dataset.uid === editingUid);
  trigger?.focus({ preventScroll: true });
  editingTrigger = undefined;
});

function closeEditItem() {
  const trigger = editingTrigger;
  elements.editItem.close();
  window.setTimeout(() => {
    const target = trigger?.isConnected
      ? trigger
      : [...elements.items.querySelectorAll(".item-name")].find(label => label.dataset.uid === editingUid);
    target?.focus({ preventScroll: true });
  }, 0);
}

elements.syncDetailsToggle.addEventListener("click", () => {
  const open = elements.syncFlyout.hidden;
  if (open) {
    closeFlyout(elements.listSelect, elements.listFlyout);
    closeFlyout(elements.marketSelect, elements.marketFlyout);
  }
  elements.syncFlyout.hidden = !open;
  elements.syncDetailsToggle.setAttribute("aria-expanded", String(open));
});
elements.syncDetailsToggle.addEventListener("keydown", event => {
  if (event.key !== "ArrowDown") return;
  event.preventDefault();
  closeFlyout(elements.listSelect, elements.listFlyout);
  closeFlyout(elements.marketSelect, elements.marketFlyout);
  elements.syncFlyout.hidden = false;
  elements.syncDetailsToggle.setAttribute("aria-expanded", "true");
  elements.syncFlyout.focus();
});
elements.syncActions.addEventListener("focusout", event => {
  if (!elements.syncActions.contains(event.relatedTarget)) {
    elements.syncFlyout.hidden = true;
    elements.syncDetailsToggle.setAttribute("aria-expanded", "false");
  }
});
document.addEventListener("click", event => {
  if (elements.syncActions.contains(event.target)) return;
  elements.syncFlyout.hidden = true;
  elements.syncDetailsToggle.setAttribute("aria-expanded", "false");
});
document.addEventListener("keydown", event => {
  if (event.key !== "Escape" || elements.syncFlyout.hidden) return;
  event.preventDefault();
  elements.syncFlyout.hidden = true;
  elements.syncDetailsToggle.setAttribute("aria-expanded", "false");
  elements.syncDetailsToggle.focus();
});

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
    elements.syncFlyout.hidden = true;
    elements.syncDetailsToggle.setAttribute("aria-expanded", "false");
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
    const allOperations = await readQueue(null);
    if (entryId !== listId) return;
    deletedUids = new Set(cached?.deleted_uids || []);
    elements.listName.textContent = cached?.name ||
      availableLists.find((list) => list.entry_id === listId)?.name || "Liste laden";
    currentItems = cached?.items || [];
    pendingOperations = operations;
    for (const operation of pendingOperations) applyLocalOperation(operation);
    replayProductAssignments(allOperations);
    applyProductCategories();
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
    setMessage(elements.message, "");
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

elements.cancelEdit.addEventListener("click", closeEditItem);
function updateEditingImage(image) {
  editingImage = image;
  elements.editImagePreview.hidden = !image;
  elements.editImageRemove.hidden = !image;
  if (image) elements.editImagePreview.src = image;
  else elements.editImagePreview.removeAttribute("src");
}

async function selectItemImage(file) {
  if (!file) return;
  const request = ++editingImageRequest;
  const uid = editingUid;
  const saveButton = elements.editItemForm.querySelector('[type="submit"]');
  saveButton.disabled = true;
  elements.editImageMessage.dataset.status = "info";
  elements.editImageMessage.textContent = "Bild wird verarbeitet …";
  try {
    const image = await prepareImageData(file);
    if (request !== editingImageRequest || uid !== editingUid || !elements.editItem.open) return;
    updateEditingImage(image);
    elements.editImageMessage.dataset.status = "info";
    elements.editImageMessage.textContent = "Bild bereit. Beim Speichern wird es mit dem Artikel übernommen.";
  } catch (error) {
    if (request !== editingImageRequest || uid !== editingUid || !elements.editItem.open) return;
    elements.editImageMessage.dataset.status = "error";
    elements.editImageMessage.textContent = error.message;
  } finally {
    if (request === editingImageRequest && uid === editingUid && elements.editItem.open) {
      saveButton.disabled = false;
    }
  }
}

elements.editImageChoose.addEventListener("click", () => elements.editImageUpload.click());
elements.editImageTake.addEventListener("click", () => elements.editImageCamera.click());
elements.editImageUpload.addEventListener("change", () => {
  const file = elements.editImageUpload.files[0];
  elements.editImageUpload.value = "";
  selectItemImage(file);
});
elements.editImageCamera.addEventListener("change", () => {
  const file = elements.editImageCamera.files[0];
  elements.editImageCamera.value = "";
  selectItemImage(file);
});
elements.editImageRemove.addEventListener("click", () => {
  editingImageRequest++;
  updateEditingImage(null);
  elements.editImageMessage.dataset.status = "info";
  elements.editImageMessage.textContent = "Bild entfernt. Speichere, um die Änderung zu übernehmen.";
  elements.editItemForm.querySelector('[type="submit"]').disabled = false;
});
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
        ...(elements.editCategory.value !== editingCategory
          ? { category_id: elements.editCategory.value || null } : {}),
        quantity: elements.editQuantity.value.trim() || null,
        image: editingImage,
      },
    });
    closeEditItem();
  } catch (error) {
    showError(error);
    closeEditItem();
  }
});
elements.editSummary.addEventListener("input", () => elements.editSummary.setCustomValidity(""));

function updateConnection(state, detail) {
  if (state === "online") finishStartupConnection();
  if (startupConnecting) {
    state = "connecting";
    detail = "Verbindung zu Home Assistant wird hergestellt.";
  }
  elements.connectionDot.className = `dot ${state}`;
  elements.syncActions.dataset.status = state;
  elements.connectionLabel.textContent =
    state === "online"
      ? "Mit Home Assistant verbunden"
      : state === "connecting"
        ? "Verbindung wird hergestellt"
      : state === "pending"
        ? "Synchronisierung ausstehend"
        : "Offline – lokale Liste";
  if (detail) elements.syncDetail.textContent = detail;
}

function showError(error) {
  if (startupConnecting && error instanceof ConnectionUnavailableError) return;
  setMessage(elements.message, error instanceof Error ? error.message : String(error));
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

class ConnectionUnavailableError extends Error {}

function beginStartupConnection() {
  startupConnecting = true;
  updateConnection("connecting");
  setBusy(busy);
  startupConnectionTimer = window.setTimeout(() => {
    finishStartupConnection();
    updateConnection(pendingOperations.length ? "pending" : "offline",
      "Home Assistant ist nicht erreichbar. Die Verbindung wird automatisch erneut versucht.");
    startupConnectionMessage = "Home Assistant ist nicht erreichbar. Die Verbindung wird automatisch erneut versucht.";
    if (!elements.message.textContent) showError(new ConnectionUnavailableError(startupConnectionMessage));
  }, 5000);
}

function finishStartupConnection() {
  window.clearTimeout(startupConnectionTimer);
  startupConnecting = false;
  if (startupConnectionMessage && elements.message.textContent === startupConnectionMessage) {
    setMessage(elements.message, "");
  }
  startupConnectionMessage = "";
  setBusy(busy);
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
    finishStartupConnection();
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

function fitSetupMenu(section) {
  if (!elements.setup.open) return;
  const menu = elements.setup.querySelector(".setup-actions");
  const viewport = window.visualViewport;
  const bottom = viewport ? viewport.offsetTop + viewport.height : window.innerHeight;
  menu.style.setProperty("--setup-available-height", `${Math.max(0, bottom - menu.getBoundingClientRect().top - 16)}px`);
  if (!section?.open) return;
  const box = menu.getBoundingClientRect();
  const content = section.getBoundingClientRect();
  const top = box.top + menu.clientTop + 8;
  const visibleBottom = box.top + menu.clientTop + menu.clientHeight - 8;
  if (content.height > visibleBottom - top || content.top < top) {
    menu.scrollTop += content.top - top;
  } else if (content.bottom > visibleBottom) {
    menu.scrollTop += content.bottom - visibleBottom;
  }
}

elements.setup.addEventListener("toggle", () => fitSetupMenu());
elements.setup.querySelectorAll(".setup-section").forEach(section => {
  section.addEventListener("toggle", () => fitSetupMenu(section));
});
window.addEventListener("resize", () => fitSetupMenu());
window.addEventListener("scroll", () => fitSetupMenu(), { passive: true });
window.visualViewport?.addEventListener("resize", () => fitSetupMenu());
window.visualViewport?.addEventListener("scroll", () => fitSetupMenu());

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
    return Promise.reject(new ConnectionUnavailableError("Home Assistant ist gerade nicht erreichbar."));
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
    await refreshSupermarkets();
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
  setMessage(elements.message, [...new Set(warnings)].join(" "));
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
  setMessage(elements.syncConflictsMessage, "");
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
          setMessage(elements.syncConflictsMessage, "Bitte zuerst einen Quellartikel auswählen.");
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
          setMessage(elements.syncConflictsMessage, error.message);
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
  setMessage(elements.syncConflictsMessage, "Entscheidung wird in HA gespeichert …", "info");
  try {
    if (syncPromise) await syncPromise;
    const snapshot = await sendCommand(`${DOMAIN}/resolve_source_conflict`, {
      entry_id: conflict.entry_id, uid: conflict.uid, token: conflict.token, action,
      ...(action === "link" ? { source_uid: sourceUid } : {}),
    });
    await saveList(snapshot);
    await refreshSyncConflicts();
    renderSyncConflicts();
    setMessage(elements.syncConflictsMessage, action === "local"
      ? conflict.deleted
        ? "Die Rückfrage ist abgeschlossen. Der Artikel bleibt hier gelöscht; die verbundene Liste wurde nicht verändert."
        : "Der Artikel bleibt für alle Geräte in unserer App-Liste gespeichert. Die verbundene HA-/Alexa-Liste wird für diesen Artikel nicht verändert."
      : "Entscheidung gespeichert. Der Abgleich wird fortgesetzt.", "success");
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
      setMessage(elements.message, marketError
        ? marketError.message : "Wähle unter Einstellungen → Synchronisation → Listen verwalten eine HA-Liste aus.",
      marketError ? "error" : "info");
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
  setMessage(elements.managementMessage, "HA-Listen werden geladen …", "info");
  elements.sourceLists.replaceChildren();
  try {
    const sources = await sendCommand(`${DOMAIN}/get_sources`);
    setMessage(elements.managementMessage, sources.length
      ? "" : "Keine HA-To-do-Listen gefunden. Lege eine Liste über Alexa an und stelle sie in HA bereit.", "info");
    for (const source of sources) {
      const form = document.createElement("form");
      form.className = "source-list";
      const heading = document.createElement("div");
      heading.className = "source-list-heading";
      const sourceText = document.createElement("div");
      sourceText.className = "source-list-text";
      const sourceName = document.createElement("span");
      sourceName.className = "source-list-name";
      sourceName.textContent = source.source_name;
      const label = document.createElement("label");
      label.className = "source-list-toggle";
      const enabled = document.createElement("input");
      enabled.type = "checkbox";
      enabled.className = "market-option-switch";
      enabled.setAttribute("role", "switch");
      enabled.setAttribute("aria-label", `${source.source_name} für die App aktivieren`);
      enabled.checked = source.enabled;
      label.append(enabled);
      const details = document.createElement("small");
      details.textContent = source.source_entity_id;
      const state = document.createElement("span");
      state.className = "source-list-state";
      const updateState = () => {
        state.textContent = enabled.checked ? "Für die App aktiviert" : "Für die App deaktiviert";
      };
      enabled.addEventListener("change", updateState);
      updateState();
      sourceText.append(sourceName, details, state);
      heading.append(sourceText, label);
      const nameLabel = document.createElement("label");
      nameLabel.className = "source-list-alias";
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
      form.append(heading);
      if (!source.available) form.append(paragraph("Quelle nicht verfügbar", "source-list-unavailable"));
      form.append(nameLabel, save);
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (!alias.value.trim()) {
          alias.setCustomValidity("Bitte gib einen Anzeigenamen ein.");
          alias.reportValidity();
          return;
        }
        if (busy) {
          setMessage(elements.managementMessage, "Bitte warte, bis die aktuelle Aktion abgeschlossen ist.", "info");
          return;
        }
        elements.sourceLists.inert = true;
        setBusy(true);
        setMessage(elements.managementMessage, "Wird gespeichert …", "info");
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
          setMessage(elements.managementMessage, "Gespeichert. Der App-Name gilt für alle Nutzer.", "success");
        } catch (error) {
          setMessage(elements.managementMessage, error.message);
        } finally {
          setBusy(false);
          elements.sourceLists.inert = false;
        }
      });
      alias.addEventListener("input", () => alias.setCustomValidity(""));
      elements.sourceLists.append(form);
    }
  } catch (error) {
    setMessage(elements.managementMessage, error.message);
  }
});

let suggestionIndex = -1;
let suggestionMatches = [];
const addingProducts = new Set();
const commonItemsTypes = {
  frequent: "Häufigste",
  recent: "Kürzlich",
  regular: "Regelmäßig",
};
let commonItemsType = "frequent";
let commonItemsListId = "";
let commonItemsSelection = new Set();

function closeProductSuggestions() {
  elements.productSuggestions.hidden = true;
  elements.newItem.setAttribute("aria-expanded", "false");
  elements.newItem.removeAttribute("aria-activedescendant");
  suggestionIndex = -1;
}

function openProductKeys() {
  return new Set(currentItems
    .filter(item => item.status === "needs_action" &&
      (item.metadata?.catalog_id || "supermarket") === activeCatalogId)
    .map(item => canonicalProductKey(item.summary)));
}

function onListMark() {
  const mark = document.createElement("span");
  mark.className = "on-list-mark";
  mark.textContent = "✓";
  mark.setAttribute("aria-hidden", "true");
  return mark;
}

function onListBadge() {
  const badge = document.createElement("span");
  badge.className = "on-list-badge";
  badge.textContent = "Auf der Liste";
  return badge;
}

function renderProductSuggestions() {
  if (document.activeElement !== elements.newItem || elements.addForm.hidden || busy || !entryId) {
    closeProductSuggestions();
    return;
  }
  const query = productNameKey(elements.newItem.value);
  if (!query) {
    closeProductSuggestions();
    return;
  }
  const open = openProductKeys();
  const pending = new Map();
  for (const operation of pendingOperations) {
    if (operation.type !== "add_item" ||
        (operation.metadata?.catalog_id || "supermarket") !== activeCatalogId) continue;
    const key = canonicalProductKey(operation.summary);
    const previous = pending.get(key) || { added: 0, last_added: 0 };
    pending.set(key, { added: previous.added + 1, last_added: Math.max(previous.last_added, operation.created_at) });
  }
  const rank = product => {
    const stored = product.usage?.[entryId];
    const local = pending.get(product.key);
    return { added: (stored?.added || 0) + (local?.added || 0),
      last: Math.max(stored?.last_added || 0, local?.last_added || 0) };
  };
  suggestionMatches = products.filter(product => product.key.startsWith(query))
    .sort((a, b) => Number(open.has(b.key)) - Number(open.has(a.key)) ||
      rank(b).added - rank(a).added || rank(b).last - rank(a).last || nameOrder.compare(a.name, b.name));
  suggestionIndex = -1;
  elements.newItem.removeAttribute("aria-activedescendant");
  elements.productSuggestions.replaceChildren();
  suggestionMatches.forEach((product, index) => {
    const option = button(product.name, () => addSuggestedProduct(product.name), "product-suggestion");
    const name = document.createElement("span");
    name.className = "product-suggestion-name";
    name.textContent = product.name;
    option.replaceChildren(name);
    if (open.has(product.key)) {
      option.disabled = true;
      option.classList.add("already-on-list");
      option.setAttribute("aria-disabled", "true");
      option.setAttribute("aria-label", `${product.name}, bereits auf der Liste`);
      option.prepend(onListMark());
      option.append(onListBadge());
    }
    option.id = `product-suggestion-${index}`;
    option.setAttribute("role", "option");
    option.setAttribute("aria-selected", "false");
    option.tabIndex = -1;
    option.title = product.name;
    option.addEventListener("pointerdown", event => {
      if (event.button === 0) event.preventDefault();
    });
    elements.productSuggestions.append(option);
  });
  elements.productSuggestions.hidden = !suggestionMatches.length;
  elements.newItem.setAttribute("aria-expanded", String(!!suggestionMatches.length));
}

async function addSuggestedProduct(name) {
  const summary = name.trim();
  const listId = entryId;
  const identity = `${listId}:${canonicalProductKey(summary)}`;
  if (!summary || busy || addingProducts.has(identity)) return false;
  if (openProductKeys().has(canonicalProductKey(summary))) {
    closeProductSuggestions();
    showError(new Error(`„${summary}“ steht bereits offen auf der Liste.`));
    return false;
  }
  addingProducts.add(identity);
  const original = elements.newItem.value;
  elements.newItem.value = "";
  closeProductSuggestions();
  try {
    await enqueue({ type: "add_item", uid: crypto.randomUUID(), summary }, listId);
    return true;
  } catch (error) {
    if (entryId === listId && !elements.newItem.value) elements.newItem.value = original || summary;
    showError(error);
    return false;
  } finally {
    addingProducts.delete(identity);
    if (entryId === listId && !elements.addForm.hidden) elements.newItem.focus();
  }
}

function productUsageForList(product, listId) {
  const stored = product.usage?.[listId];
  const weeks = new Map(Object.entries(stored?.weeks || {}));
  let added = stored?.added || 0;
  let lastAdded = stored?.last_added || 0;
  for (const operation of pendingOperations) {
    if (operation.type !== "add_item" || operation.entry_id !== listId ||
      (operation.metadata?.catalog_id || "supermarket") !== activeCatalogId ||
      canonicalProductKey(operation.summary) !== product.key) continue;
    added += 1;
    lastAdded = Math.max(lastAdded, operation.created_at);
    const date = new Date(operation.created_at);
    const day = date.getUTCDay() || 7;
    date.setUTCDate(date.getUTCDate() + 4 - day);
    const yearStart = Date.UTC(date.getUTCFullYear(), 0, 1);
    const week = Math.ceil(((date.getTime() - yearStart) / 86400000 + 1) / 7);
    const weekKey = `${date.getUTCFullYear()}-W${String(week).padStart(2, "0")}`;
    weeks.set(weekKey, (weeks.get(weekKey) || 0) + 1);
  }
  return { added, lastAdded, weeks };
}

function commonItemsForCurrentList() {
  const ranked = products
    .map(product => ({
      product,
      usage: productUsageForList(product, commonItemsListId),
      totalUsage: productUsageCount(product) + pendingOperations.filter(operation =>
        operation.type === "add_item" &&
        (operation.metadata?.catalog_id || "supermarket") === activeCatalogId &&
        canonicalProductKey(operation.summary) === product.key
      ).length,
    }))
    .filter(({ usage }) => commonItemsType !== "regular" || usage.weeks.size > 1);
  ranked.sort((a, b) => {
    if (commonItemsType === "recent") {
      return b.usage.lastAdded - a.usage.lastAdded ||
        b.usage.added - a.usage.added || nameOrder.compare(a.product.name, b.product.name);
    }
    if (commonItemsType === "regular") {
      const aWeeklyCount = [...a.usage.weeks.values()].reduce((sum, count) => sum + count, 0);
      const bWeeklyCount = [...b.usage.weeks.values()].reduce((sum, count) => sum + count, 0);
      return b.usage.weeks.size - a.usage.weeks.size ||
        bWeeklyCount - aWeeklyCount || b.usage.lastAdded - a.usage.lastAdded ||
        nameOrder.compare(a.product.name, b.product.name);
    }
    return b.totalUsage - a.totalUsage ||
      b.usage.lastAdded - a.usage.lastAdded || nameOrder.compare(a.product.name, b.product.name);
  });
  return ranked;
}

function renderCommonItems() {
  const titles = {
    frequent: "Häufigste Artikel",
    recent: "Kürzlich hinzugefügt",
    regular: "Regelmäßig hinzugefügt",
  };
  elements.commonItemsDialog.querySelectorAll("[data-common-items-type]").forEach(tab => {
    const selected = tab.dataset.commonItemsType === commonItemsType;
    tab.setAttribute("aria-selected", String(selected));
    tab.tabIndex = selected ? 0 : -1;
  });
  elements.commonItemsListTitle.textContent = titles[commonItemsType];
  const ranked = commonItemsForCurrentList();
  const open = openProductKeys();
  commonItemsSelection = new Set([...commonItemsSelection].filter(key => !open.has(key)));
  elements.commonItemsListCount.textContent = `${ranked.length} Artikel`;
  elements.commonItemsList.replaceChildren();
  for (const { product, usage, totalUsage } of ranked) {
    const present = open.has(product.key);
    const label = document.createElement("label");
    label.className = `common-item-option${present ? " already-on-list" : ""}`;
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = commonItemsSelection.has(product.key);
    checkbox.disabled = present;
    checkbox.hidden = present;
    checkbox.setAttribute("aria-label", present ? `${product.name}, bereits auf der Liste` : product.name);
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) commonItemsSelection.add(product.key);
      else commonItemsSelection.delete(product.key);
      updateCommonItemsSelection();
    });
    const name = document.createElement("span");
    name.className = "common-item-name";
    name.textContent = product.name;
    const frequency = document.createElement("span");
    frequency.className = "common-item-frequency";
    if (commonItemsType === "regular") frequency.textContent = `${usage.weeks.size} Wochen`;
    else if (commonItemsType === "frequent" && totalUsage) frequency.textContent = `${totalUsage}×`;
    label.append(checkbox);
    if (present) label.append(onListMark());
    label.append(name, frequency);
    if (present) label.append(onListBadge());
    elements.commonItemsList.append(label);
  }
  elements.commonItemsEmpty.hidden = ranked.length > 0;
  elements.commonItemsEmpty.textContent = commonItemsType === "regular"
    ? "Noch keine Artikel, die in mehreren Wochen hinzugefügt wurden."
    : "Noch keine bekannten Artikel für diese Liste.";
  updateCommonItemsSelection();
}

function updateCommonItemsSelection() {
  const selectedCount = commonItemsSelection.size;
  elements.commonItemsSelection.textContent = selectedCount ? `${selectedCount} ausgewählt` : "";
  elements.addCommonItems.disabled = !selectedCount || busy;
  elements.addCommonItems.textContent = selectedCount > 0 ? `Auf die Liste (${selectedCount})` : "Auf die Liste";
}

function openCommonItems() {
  if (busy || !entryId || elements.commonItemsDialog.open) return;
  closeProductSuggestions();
  commonItemsType = "frequent";
  commonItemsListId = entryId;
  commonItemsSelection = new Set();
  renderCommonItems();
  elements.commonItemsDialog.showModal();
  elements.commonItemsDialog.querySelector('[data-common-items-type="frequent"]').focus({ preventScroll: true });
}

function closeCommonItems() {
  if (elements.commonItemsDialog.open) elements.commonItemsDialog.close();
}

async function addSelectedCommonItems() {
  if (elements.addCommonItems.disabled || entryId !== commonItemsListId) return;
  const listId = commonItemsListId;
  const original = elements.newItem.value;
  const selectedNames = [...commonItemsSelection]
    .map(key => products.find(product => product.key === key)?.name)
    .filter(Boolean);
  closeCommonItems();
  for (const name of selectedNames) {
    if (!await addSuggestedProduct(name)) break;
  }
  if (entryId === listId) {
    elements.newItem.value = original;
    elements.newItem.focus();
    elements.newItem.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

elements.openCommonItems.addEventListener("click", openCommonItems);
elements.cancelCommonItems.addEventListener("click", closeCommonItems);
elements.closeCommonItems.addEventListener("click", closeCommonItems);
elements.addCommonItems.addEventListener("click", () => addSelectedCommonItems().catch(showError));
elements.commonItemsDialog.querySelectorAll("[data-common-items-type]").forEach(tab => {
  tab.addEventListener("click", () => {
    commonItemsType = tab.dataset.commonItemsType;
    renderCommonItems();
  });
  tab.addEventListener("keydown", event => {
    if (!["ArrowLeft", "ArrowRight"].includes(event.key)) return;
    event.preventDefault();
    const tabs = [...elements.commonItemsDialog.querySelectorAll("[data-common-items-type]")];
    const currentIndex = tabs.indexOf(tab);
    const delta = event.key === "ArrowRight" ? 1 : -1;
    tabs[(currentIndex + delta + tabs.length) % tabs.length].click();
    elements.commonItemsDialog.querySelector('[data-common-items-type="' + commonItemsType + '"]').focus();
  });
});
elements.commonItemsDialog.addEventListener("close", () => {
  commonItemsSelection = new Set();
  updateCommonItemsSelection();
});

elements.newItem.addEventListener("input", renderProductSuggestions);
elements.newItem.addEventListener("focus", renderProductSuggestions);
elements.newItem.addEventListener("blur", closeProductSuggestions);
elements.newItem.addEventListener("keydown", event => {
  if (event.isComposing) return;
  if (event.key === "Escape") {
    if (!elements.productSuggestions.hidden) event.stopPropagation();
    closeProductSuggestions();
    return;
  }
  if (["ArrowDown", "ArrowUp"].includes(event.key)) {
    if (elements.productSuggestions.hidden) renderProductSuggestions();
    if (!suggestionMatches.length || elements.productSuggestions.hidden) return;
    event.preventDefault();
    const options = [...elements.productSuggestions.children];
    const available = options.map((option, index) => option.disabled ? -1 : index).filter(index => index >= 0);
    if (!available.length) return;
    const current = available.indexOf(suggestionIndex);
    suggestionIndex = event.key === "ArrowDown"
      ? available[(current + 1) % available.length]
      : available[(current < 0 ? available.length - 1 : current - 1 + available.length) % available.length];
    options.forEach((option, index) => option.setAttribute("aria-selected", String(index === suggestionIndex)));
    elements.newItem.setAttribute("aria-activedescendant", options[suggestionIndex].id);
    options[suggestionIndex].scrollIntoView({ block: "nearest" });
  } else if (event.key === "Enter" && suggestionIndex >= 0 && !elements.productSuggestions.hidden) {
    event.preventDefault();
    addSuggestedProduct(suggestionMatches[suggestionIndex].name);
  }
});

elements.addForm.addEventListener("submit", event => {
  event.preventDefault();
  if (event.isComposing) return;
  addSuggestedProduct(elements.newItem.value);
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
  serviceWorkerRegistration?.update().catch(error => {
    console.warn("Die Web-App-Version konnte nicht geprüft werden.", error);
  });
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
  beginStartupConnection();
  initializeMode();
  elements.appVersion.textContent = `v${document.querySelector('meta[name="app-version"]').content}`;
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
      if (navigator.serviceWorker.controller) {
        let refreshing = false;
        navigator.serviceWorker.addEventListener("controllerchange", () => {
          if (refreshing) return;
          refreshing = true;
          location.reload();
        });
      }
      serviceWorkerRegistration = await navigator.serviceWorker.register("./service-worker.js", { scope: "./" });
      serviceWorkerRegistration.update().catch(error => {
        console.warn("Die Web-App-Version konnte nicht geprüft werden.", error);
      });
    }
    try {
      await completeAuthorization();
    } catch (error) {
      finishStartupConnection();
      showError(error);
    }
    setBusy(false);
    if (startAuthorization) {
      await connectHomeAssistant().catch(showError);
      return;
    }
    connect();
  } catch (error) {
    finishStartupConnection();
    showError(error);
    elements.connectionLabel.textContent = "Lokaler Speicher nicht verfügbar";
  }
}

initializeDesign();
start();
