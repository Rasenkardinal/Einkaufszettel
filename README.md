# Easy Shopping

Flexible, gemeinsam nutzbare Einkaufsliste für Home Assistant mit frei zuordenbaren Kategorien und Alexa-Anbindung.

> **Projektstatus:** frühe Entwurfsphase. Dieses Repository dokumentiert bisherige Architekturentscheidungen und offene Fragen; eine lauffähige Integration ist noch nicht implementiert.

## Ziel

Eine lokale, zuverlässige Einkaufsliste für mehrere Haushaltsmitglieder. Artikel sollen Produkten und frei sortierbaren Kategorien zugeordnet werden können. Home Assistant (HA) ist die Plattform und soll mit der bereits eingebundenen Alexa-Einkaufsliste zusammenarbeiten. Die erste Ausbaustufe importiert Einträge und erlaubt lokales Abhaken; Synchronisierung ist später vorgesehen.

## Geplante erste Ausbaustufe

- Eine vorhandene HA-To-do-Liste wird im Integrations-Konfigurationsflow ausgewählt. Voraussetzung ist, dass die Alexa-Liste in HA als `todo`-Entität mit lesbaren Einträgen verfügbar ist.
- Offene Quell-Einträge werden einmalig in eine eigene Easy-Shopping-Liste kopiert.
- Easy Shopping stellt eine eigene HA-To-do-Listen-Entität bereit, die in HA angezeigt und abgehakt werden kann.
- Die Kopie ist lokal und dauerhaft; Änderungen werden in dieser Version nicht zurück zur Quelle synchronisiert.
- Eigene Produkt-, Kategorie- und Einkaufsdaten erweitern das standardisierte To-do-Datenmodell, ohne sie in unstrukturierte Textfelder zu zwängen.

## Dokumentation

- [Architekturentscheidungen (ADRs)](docs/decisions/README.md)
- [ADR 0001: Home Assistant als Plattform und To-do-Entität](docs/decisions/0001-home-assistant-todo-entity.md)
- [ADR 0002: Eigene Datenhaltung und initialer Import](docs/decisions/0002-owned-data-and-import.md)
- [ADR 0003: Produktdaten und Listeneinträge trennen](docs/decisions/0003-products-and-list-items.md)

## Geplante Architektur (Entwurf)

- **Quellliste:** vorhandene `todo`-Entität (beispielsweise die in HA synchronisierte Alexa-Liste).
- **Easy-Shopping-Liste:** eigene `TodoListEntity`-Entität für die HA-To-do-Schnittstelle.
- **Integration:** persistiert Listen-, Produkt- und Kategoriedaten in integrationsverwaltetem HA-Speicher; die Config Entry hält die Quelllisten-Auswahl und Integrationskonfiguration.
- **Oberfläche:** zunächst HA-To-do-Ansicht; eine eigene, einkaufsoptimierte UI ist ein späterer Schritt und noch nicht festgelegt.

## Wichtige Einschränkung

HA-To-do-Einträge bieten standardisierte Felder wie eindeutige ID, Zusammenfassung, Status und optionale Beschreibung. Kategorien, Produktzuordnungen und strukturierte Mengen/Einheiten gehören zum Easy-Shopping-Datenmodell und werden separat persistent gehalten. Die HA-To-do-Entität dient als kompatible Sicht und Bedienoberfläche, nicht als vollständiges Produktschema.
