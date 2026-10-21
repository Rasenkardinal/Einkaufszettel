# ADR 0002: Eigene Datenhaltung und einmaliger Listenimport

- **Status:** Angenommen
- **Datum:** 2026-10-18

## Kontext

Die ausgewählte Alexa-Liste ist eine bestehende HA-To-do-Entität. Einkaufszettel muss unabhängig von Alexa weiter bedienbar bleiben und wird später zusätzliche Produkt- und Kategoriedaten verwalten. Ein HA-To-do-Eintrag allein enthält diese Domänendaten nicht.

## Entscheidung

1. Beim Einrichten wird die ausgewählte Quellliste als Teil der Config Entry konfiguriert. Die Konfiguration speichert Referenzen und Einstellungen, nicht den veränderlichen Einkaufsbestand.
2. Beim erstmaligen Einrichten kopiert Einkaufszettel die offenen Einträge der Quellliste in den eigenen Bestand. Abgeschlossene Einträge werden im ersten Entwurf nicht importiert. Die genaue Behandlung eines erneuten Imports ist noch offen.
3. Einkaufszettel ist für diesen Bestand die maßgebliche Datenquelle. Lokales Abhaken ändert nur den Einkaufszettel-Eintrag; im initialen Umfang wird die Quelle nicht verändert und es findet kein automatischer Einweg- oder Zweiweg-Sync statt.
4. Veränderliche Listen-, Produkt- und Kategoriedaten werden dauerhaft durch die Integration gespeichert. Vorgesehen ist der Home-Assistant-`Store`-Helper mit versioniertem JSON im integrationsverwalteten `.storage`-Bereich.
5. HA To-do-Entitäten und ihre `TodoItem`-Daten sind die standardisierte HA-Schnittstelle/Projektion. Sie ersetzen nicht den integrationsverwalteten Bestand mit Produktbeziehungen und Metadaten.

## Folgen

- Der eigene Bestand bleibt nach einem Home-Assistant-Neustart vorhanden und benötigt zum Abhaken keine erreichbare Alexa- oder Amazon-Cloud.
- Die Integration muss Änderungen der To-do-Entität in den eigenen persistenten Bestand übernehmen und danach HA-Entitätszustände aktualisieren.
- Speicherformate brauchen eine Versionsnummer und eine Migrationsstrategie, sobald das interne Schema sich ändert.
- Die Daten unter `.storage` sind integrationsverwaltet; Nutzer sollten sie nicht manuell bearbeiten. Backup und Wiederherstellung erfolgen über die üblichen HA-Konfigurationsbackups.
- Die Integration speichert eine interne stabile ID pro Listeneintrag. Eine Quell-UID kann, falls die konkrete Quellintegration sie liefert, als optionale Herkunftsreferenz abgelegt werden; sie ist nicht die Identität des kopierten Eintrags.

## Nicht Teil dieser Entscheidung

Automatischer Import neu hinzugefügter Quell-Einträge, Wiederholungs-/Merge-Verhalten, Zweiweg-Synchronisierung, Löschweitergabe und Konfliktlösung sind spätere Entscheidungen. Vor Implementierung ist zu verifizieren, welche Items und Fähigkeiten die tatsächlich installierte Alexa-Listenintegration über die HA-To-do-Schnittstelle bietet.
