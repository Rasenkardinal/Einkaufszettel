# Einkaufszettel

Eine gemeinsam nutzbare Einkaufsliste für Home Assistant mit eigener Produkt- und Kategorienlogik sowie Alexa-Anbindung über eine vorhandene HA-To-do-Liste.

> **Projektstatus:** Alpha `0.3.0-alpha.2`. Enthält Konfigurationsflow, initialen Import, Quelllisten-Kopierer, lokale HA-To-do-Liste und eine installierbare Offline-PWA. Produktkatalog und Kategorien sind noch nicht implementiert.

## Funktionsumfang

- Eine externe HA-To-do-Liste – etwa die in HA verfügbare Alexa-Liste – wird im Konfigurationsflow ausgewählt.
- Offene Einträge werden bei der ersten Einrichtung in die lokale Liste kopiert.
- Ein Button ergänzt später neue, offene Quell-Einträge anhand ihrer Quell-IDs, ohne vorhandene lokale Änderungen zurückzusetzen.
- Die eigene To-do-Liste erscheint in HA und unterstützt Abhaken/Wiederöffnen, Umbenennen, Beschreibung und Fälligkeit.
- Die Quelle wird nicht verändert; es gibt keinen automatischen oder bidirektionalen Sync.
- Kategorien, Produktkatalog, strukturierte Mengen und eine eigene UI sind noch nicht implementiert.
- Die Smartphone-Oberfläche wird als PWA von der Integration über Home Assistant ausgeliefert. App-Dateien und Listendaten werden lokal gespeichert; Hinzufügen, Abhaken und Löschen werden offline vorgemerkt und beim nächsten Verbinden synchronisiert.

## Installation mit HACS

1. In HACS das Repository `https://github.com/Rasenkardinal/Einkaufszettel` als **Integration** hinzufügen oder den bereits vorhandenen Repository-Eintrag aktualisieren.
2. Version `0.3.0-alpha.2` herunterladen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Einkaufszettel** öffnen.
5. Alexa-/Quell-To-do-Liste auswählen und eine lokale Listenbezeichnung festlegen.
6. Danach die Liste im HA-Bereich **To-do-Listen** öffnen. Der erwartete Entity-ID-Slug ist nun `todo.einkaufszettel`.
7. Unter den Integration-Entitäten den Button **„Web-App öffnen / installieren“** drücken, die verlinkte Seite online im Smartphone-Browser öffnen und **Installieren** beziehungsweise **Zum Startbildschirm hinzufügen** wählen.

Die Installation benötigt HTTPS, beispielsweise über Nabu Casa. Die PWA muss mindestens einmal online geladen und synchronisiert worden sein, bevor sie offline verwendet werden kann. Im installierten Modus kann sie ohne normale Browser-Adressleiste starten. Der Installationsdialog wird abhängig vom Browser angeboten; auf iOS kann stattdessen die Browserfunktion **Teilen → Zum Home-Bildschirm** nötig sein.

## Wichtige Umstellung von Easy Shopping (`easy_shopping`)

Diese Version ändert die technische HA-Domain von `easy_shopping` auf `einkaufszettel`. Home Assistant kann Config Entries nicht domainübergreifend migrieren. Deshalb wird eine neue Integrationseinrichtung benötigt. Der neue Konfigurationsflow kann jedoch vorhandene lokale Eintragsdaten aus einem passenden alten `easy_shopping`-Config-Entry übernehmen, wenn dieser noch in HA registriert ist und dieselbe Quell-Entity ausgewählt wird.

1. Vor dem Update ein Home-Assistant-Backup erstellen, einschließlich `.storage`.
2. HACS aktualisieren und **Einkaufszettel `0.3.0-alpha.2`** herunterladen. Home Assistant neu starten.
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

## Offline-Web-App verwenden

1. In Home Assistant **Einstellungen → Geräte & Dienste → Einkaufszettel → Entitäten** den Button **„Web-App öffnen / installieren“** drücken.
2. Die Benachrichtigung öffnen und den Web-App-Link im Smartphone-Browser laden. Beim ersten Aufruf **Mit HA verbinden** wählen und Home Assistant den Zugriff erlauben. Die App-Shell und Anmeldung werden initialisiert.
3. Die App über den Browser installieren oder zum Startbildschirm hinzufügen. Beim nächsten Einkauf direkt dieses Symbol öffnen; nicht erst in der Companion App zu einer nicht erreichbaren HA-Seite navigieren.
4. Artikel hinzufügen, abhaken oder entfernen. Ohne Netz werden Änderungen in der lokalen Browser-Datenbank und einer dauerhaften Warteschlange gespeichert. Beim nächsten Start mit erreichbarem HA werden diese nacheinander übertragen.
5. Der Sync-Status zeigt ausstehende Änderungen. Bei abgelaufener Anmeldung **Mit HA verbinden** wählen und die Anmeldung erneut erlauben. Das Kopieren neuer Alexa-/Quelllistenartikel benötigt eine Verbindung.

Die PWA speichert ein Home-Assistant-Refresh-Token lokal im Browserprofil, damit sie unabhängig von der HA-Companion-App synchronisieren kann. Die Anmeldung wird über den offiziellen Home-Assistant-Autorisierungsdialog erteilt. Browserdaten nicht löschen, solange lokale Änderungen ausstehen; danach muss die App erneut verbunden werden. Der erste Offline-Sync verwendet stabile Aktions-IDs, damit ein nach Verbindungsabbruch wiederholter Artikel nicht doppelt angelegt wird. Bei gleichzeitigen Offline-Änderungen derselben Eigenschaft gilt die zuletzt synchronisierte Aktion; andere Eigenschaften desselben Eintrags bleiben davon unberührt.

## Daten und Grenzen

- Die Config Entry speichert Quell-Entity-ID und Listenname, keine Zugangsdaten.
- Die maßgebliche lokale Liste liegt dauerhaft im integrationsverwalteten HA-`Store` unter `.storage/einkaufszettel.<entry_id>`. Die PWA speichert den letzten Stand und ausstehende Aktionen zusätzlich gerätegebunden in IndexedDB.
- HA `TodoItem` bildet die kompatible Listenansicht. Produktzuordnung, Kategorie, Menge und Einheit werden bei späterer Produktfunktion im eigenen Datenmodell geführt.
- Änderungen werden vor Anzeige dauerhaft gespeichert. Fehler werden nicht als Erfolg oder leere Liste verschleiert.
- Entfernen der Integration löscht weder den HA-Store noch Browserdaten automatisch. Backups verwenden und `.storage` nicht manuell bearbeiten.
- Der HA-WebSocket-Zugang und damit die erste Anmeldung sowie Synchronisation benötigen eine Verbindung zu Home Assistant. Bereits installierte App-Shell und zwischengespeicherte Liste sind offline verfügbar.

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

Die lokalen Modell-, Paket- und Lifecycle-Tests laufen unter Windows/Python 3.13. Die echte HA-Integrationssuite benötigt eine native Test-Abhängigkeit, die auf Windows Microsoft-C++-Build-Tools voraussetzt; daher wurde sie hier nicht ausgeführt. Die PWA muss außerdem auf den konkreten Android-/iOS-Geräten und mit dem Nabu-Casa-Zugang getestet werden.

## Architekturentscheidungen

- [ADR-Index und offene Fragen](docs/decisions/README.md)
- [ADR 0006: Marken- und technische Domain-Umbenennung](docs/decisions/0006-project-rename-and-domain.md)
- [ADR 0007: Offline-First-PWA und Hosting über Home Assistant](docs/decisions/0007-offline-first-pwa.md)
