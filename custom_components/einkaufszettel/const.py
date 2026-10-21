"""Constants for Einkaufszettel."""

DOMAIN = "einkaufszettel"
LEGACY_DOMAIN = "easy_shopping"
CONF_SOURCE = "source_entity_id"
STORAGE_VERSION = 1


def update_signal(entry_id: str) -> str:
    """Return the entry-specific local list update signal."""
    return f"{DOMAIN}_{entry_id}_updated"
