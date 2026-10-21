# Einkaufszettel

Eine gemeinsam nutzbare Einkaufsliste für Home Assistant mit eigener Produkt- und Kategorienlogik sowie Alexa-Anbindung über eine vorhandene HA-To-do-Liste.

> **Projektstatus:** Alpha `0.2.0-alpha.1`. Enthält Konfigurationsflow, initialen Import, manuellen Kopieren-Knopf und eine dauerhaft gespeicherte HA-To-do-Liste. Noch keine automatische Synchronisierung, Produktverwaltung oder eigene Smartphone-UI.

## Funktionsumfang

- Eine externe HA-To-do-Liste – etwa die in HA verfügbare Alexa-Liste – wird im Konfigurationsflow ausgewählt.
- Offene Einträge werden bei der ersten Einrichtung in die lokale Liste kopiert.
- Ein Button ergänzt später neue, offene Quell-Einträge anhand ihrer Quell-IDs, ohne vorhandene lokale Änderungen zurückzusetzen.
- Die eigene To-do-Liste erscheint in HA und unterstützt Abhaken/Wiederöffnen, Umbenennen, Beschreibung und Fälligkeit.
- Die Quelle wird nicht verändert; es gibt keinen automatischen oder bidirektionalen Sync.
- Kategorien, Produktkatalog, strukturierte Mengen und eine eigene UI sind noch nicht implementiert.

## Installation mit HACS

1. In HACS das Repository `https://github.com/Rasenkardinal/Einkaufszettel` als **Integration** hinzufügen oder den bereits vorhandenen Repository-Eintrag aktualisieren.
2. Version `0.2.0-alpha.1` herunterladen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Einkaufszettel** öffnen.
5. Alexa-/Quell-To-do-Liste auswählen und eine lokale Listenbezeichnung festlegen.
6. Danach die Liste im HA-Bereich **To-do-Listen** öffnen. Der erwartete Entity-ID-Slug ist nun `todo.einkaufszettel`.

## Wichtige Umstellung von Easy Shopping (`easy_shopping`)

Diese Version ändert die technische HA-Domain von `easy_shopping` auf `einkaufszettel`. Home Assistant kann Config Entries nicht domainübergreifend migrieren. Deshalb wird eine neue Integrationseinrichtung benötigt. Der neue Konfigurationsflow kann jedoch vorhandene lokale Eintragsdaten aus einem passenden alten `easy_shopping`-Config-Entry übernehmen, wenn dieser noch in HA registriert ist und dieselbe Quell-Entity ausgewählt wird.

1. Vor dem Update ein Home-Assistant-Backup erstellen, einschließlich `.storage`.
2. HACS aktualisieren und **Einkaufszettel `0.2.0-alpha.1`** herunterladen. Home Assistant neu starten.
3. Den bisherigen Easy-Shopping-Eintrag **nicht vorher löschen**. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** die neue Integration **Einkaufszettel** hinzufügen.
4. Im neuen Konfigurationsflow dieselbe Alexa-/Quell-To-do-Entity wie zuvor wählen. Dadurch kann die Integration den alten lokalen Snapshot anhand der Quell-Entity übernehmen, ohne die Alexa-Liste erneut zu importieren. Die alte Integration darf bis zur erfolgreichen Prüfung registriert bleiben.
5. Prüfen, ob Einträge, Erledigt-Status, lokale Namen und Notizen in der neuen `todo.einkaufszettel`-Liste vorhanden sind. Dashboards, Automationen und Skripte mit `todo.easy_shopping` oder der alten Button-Entity anschließend auf die neuen Einkaufszettel-Entities umstellen.
6. Erst danach den alten **Easy Shopping**-Config-Entry löschen. Die alte `.storage/easy_shopping.<entry_id>`-Datei wird dadurch nicht automatisch gelöscht.

**Nicht** den alten Config-Entry entfernen, bevor die neue Liste geprüft ist. Falls er bereits gelöscht wurde, kann die Integration den zugehörigen alten Store nicht sicher anhand der Quellliste identifizieren; dann ist ein Restore aus Backup oder ein neuer Import aus der Quellliste erforderlich. Ein neuer Eintrag wird für den Store-Pfad `.storage/einkaufszettel.<entry_id>` angelegt.

## Manuelle Installation

Home Assistant mit To-do-Unterstützung und eine externe Quellliste als `todo`-Entity sind erforderlich. Den vollständigen Ordner [custom_components/einkaufszettel](custom_components/einkaufszettel) in den HA-Konfigurationsordner unter `custom_components/einkaufszettel` kopieren und Home Assistant neu starten. Die Integration verwaltet keine Alexa-Anmeldung und benötigt keine Amazon-Zugangsdaten.

## Quellliste erneut kopieren

Unter **Einstellungen → Geräte & Dienste → Einkaufszettel → Entitäten** den Button **„Einkaufszettel: Quellliste kopieren“** öffnen und **Drücken** wählen. Der Button kann auch in ein Dashboard gelegt oder mit `button.press` aufgerufen werden.

- Nur unbekannte, offene Quell-IDs werden hinzugefügt; wiederholtes Drücken erzeugt keine Duplikate.
- Vorhandene lokale Namen, Beschreibungen, Fälligkeiten und Erledigt-Status bleiben erhalten. Abgehakte Artikel werden nicht wieder geöffnet.
- Gleicher Name mit einer neuen Quell-ID gilt als neuer Eintrag. Fehlen stabile Quell-IDs, wird mit einer Fehlermeldung abgebrochen statt nach Namen zu raten.
- Quelländerungen und -löschungen werden nicht zurückgespiegelt. Bei nicht erreichbarer Quelle oder fehlgeschlagenem Speichern bleibt der lokale Bestand unverändert.

## Daten und Grenzen

- Die Config Entry speichert Quell-Entity-ID und Listenname, keine Zugangsdaten.
- Die lokale Liste und spätere Fachinformationen liegen dauerhaft im integrationsverwalteten HA-`Store` als versionierte Daten unter `.storage/einkaufszettel.<entry_id>`.
- HA `TodoItem` bildet die kompatible Listenansicht. Produktzuordnung, Kategorie, Menge und Einheit werden bei späterer Produktfunktion im eigenen Datenmodell geführt.
- Änderungen werden vor Anzeige dauerhaft gespeichert. Fehler werden nicht als Erfolg oder leere Liste verschleiert.
- Entfernen der neuen Integration löscht den neuen Store in dieser Alpha nicht automatisch. Backups verwenden und `.storage` nicht manuell bearbeiten.
- Die Liste wird von Home Assistant bereitgestellt und ist bei einem Ausfall von HA nicht offline verfügbar.

## Entwicklung und Tests

```text
python -m pip install -r requirements-dev.txt
python -m pytest tests/unit
ruff check .
ruff format --check .
```

Die HA-Integrationssuite ist für Linux/CI über [requirements-test-ha.txt](requirements-test-ha.txt) vorgesehen:

```text
python -m pip install -r requirements-test-ha.txt
python -m pytest
```

Windows/Python 3.13 hatte für den vorherigen Alpha-Stand 46 lokale Modell-, Paket- und Lifecycle-Tests bestanden. Die echten HA-Integrationstests konnten dort wegen einer nativen Test-Abhängigkeit ohne Microsoft-C++-Build-Tools nicht ausgeführt werden. Die neue Domain- und Legacy-Store-Übernahme benötigt zusätzlich einen Test in einer HA-Testumgebung und in der Zielinstallation.

## Architekturentscheidungen

- [ADR-Index und offene Fragen](docs/decisions/README.md)
- [ADR 0006: Marken- und technische Domain-Umbenennung](docs/decisions/0006-project-rename-and-domain.md)
