# Einkaufszettel

Eine gemeinsam nutzbare Einkaufsliste für Home Assistant mit eigener Produkt- und Kategorienlogik sowie Alexa-Anbindung über eine vorhandene HA-To-do-Liste.

> **Projektstatus:** Alpha. Enthält HA-Quelllistenverwaltung mit gemeinsamen App-Anzeigenamen, Quelllisten-Kopierer und eine installierbare Offline-PWA. Die Integration erzeugt keine zusätzlichen To-do-Listen. Produktkatalog und Kategorien sind noch nicht implementiert.

## Funktionsumfang

- Vorhandene externe HA-To-do-Listen werden unter **Setup → Listen verwalten** in der App angeboten. Dort werden Listen aktiviert und kurze App-Anzeigenamen vergeben.
- Offene Einträge werden beim ersten Aktivieren in einen internen HA-Speicher kopiert.
- Ein Button ergänzt später neue, offene Quell-Einträge anhand ihrer Quell-IDs, ohne vorhandene lokale Änderungen zurückzusetzen.
- Die PWA unterstützt Hinzufügen, Abhaken/Wiederöffnen, Umbenennen und Löschen. Es erscheint keine doppelte Einkaufszettel-Liste in der HA-To-do-Ansicht.
- Die Quelle wird nicht verändert; es gibt keinen automatischen oder bidirektionalen Sync.
- Kategorien, Produktkatalog und strukturierte Mengen sind noch nicht implementiert.
- Die Smartphone-Oberfläche wird als PWA von der Integration über Home Assistant ausgeliefert. App-Dateien und Listendaten werden lokal gespeichert; Hinzufügen, Abhaken und Löschen werden offline vorgemerkt und beim nächsten Verbinden synchronisiert.

## Installation mit HACS

1. In HACS das Repository `https://github.com/Rasenkardinal/Einkaufszettel` als **Integration** hinzufügen oder den bereits vorhandenen Repository-Eintrag aktualisieren.
2. Die aktuelle Vorabversion herunterladen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Einkaufszettel** öffnen.
5. Einrichtung bestätigen. Die Quelllisten werden anschließend in der App verwaltet.
6. In der Web-App **Setup → Listen verwalten** öffnen, gewünschte HA-Listen aktivieren und kurze Anzeigenamen vergeben. Diese Einstellungen benötigen HA-Administratorrechte und gelten für alle Haushaltsmitglieder.
7. Die neue Einkaufszettel-Seite erscheint in der Home-Assistant-Seitenleiste. Dort die Liste öffnen. Der Button **„Web-App öffnen / installieren“** unter den Integration-Entitäten erzeugt zusätzlich eine Benachrichtigung mit dem direkten App-Link.

Die Installation benötigt HTTPS, beispielsweise über Nabu Casa. Die PWA muss mindestens einmal online geladen und synchronisiert worden sein, bevor sie offline verwendet werden kann. Im installierten Modus kann sie ohne normale Browser-Adressleiste starten. Der Installationsdialog wird abhängig vom Browser angeboten; auf iOS kann stattdessen die Browserfunktion **Teilen → Zum Home-Bildschirm** nötig sein.

## Wichtige Umstellung von Easy Shopping (`easy_shopping`)

Diese Version ändert die technische HA-Domain von `easy_shopping` auf `einkaufszettel`. Home Assistant kann Config Entries nicht domainübergreifend migrieren. Deshalb wird eine neue Integrationseinrichtung benötigt. Der neue Konfigurationsflow kann jedoch vorhandene lokale Eintragsdaten aus einem passenden alten `easy_shopping`-Config-Entry übernehmen, wenn dieser noch in HA registriert ist und dieselbe Quell-Entity ausgewählt wird.

1. Vor dem Update ein Home-Assistant-Backup erstellen, einschließlich `.storage`.
2. HACS aktualisieren und **Einkaufszettel `0.3.0-alpha.3`** herunterladen. Home Assistant neu starten.
3. Den bisherigen Easy-Shopping-Eintrag **nicht vorher löschen**. Unter **Einstellungen → Geräte & Dienste → Integration hinzufügen** die neue Integration **Einkaufszettel** hinzufügen.
4. In der neuen Web-App unter **Setup → Listen verwalten** dieselbe Alexa-/Quell-To-do-Entity aktivieren. Dadurch kann die Integration den alten lokalen Snapshot anhand der Quell-Entity übernehmen, ohne die Alexa-Liste erneut zu importieren. Die alte Integration darf bis zur erfolgreichen Prüfung registriert bleiben.
5. Einträge und Erledigt-Status in der Web-App prüfen. Eigene Einkaufszettel-To-do-Entitäten werden nicht mehr bereitgestellt; darauf basierende Dashboards und Automationen müssen angepasst werden.
6. Erst danach den alten **Easy Shopping**-Config-Entry löschen. Die alte `.storage/easy_shopping.<entry_id>`-Datei wird dadurch nicht automatisch gelöscht.

**Nicht** den alten Config-Entry entfernen, bevor die neue Liste geprüft ist. Falls er bereits gelöscht wurde, kann die Integration den zugehörigen alten Store nicht sicher anhand der Quellliste identifizieren; dann ist ein Restore aus Backup oder ein neuer Import aus der Quellliste erforderlich. Ein neuer Eintrag wird für den Store-Pfad `.storage/einkaufszettel.<entry_id>` angelegt.

## Manuelle Installation

Home Assistant mit To-do-Unterstützung und eine externe Quellliste als `todo`-Entity sind erforderlich. Den vollständigen Ordner [custom_components/einkaufszettel](custom_components/einkaufszettel) in den HA-Konfigurationsordner unter `custom_components/einkaufszettel` kopieren und Home Assistant neu starten. Die Integration verwaltet keine Alexa-Anmeldung und benötigt keine Amazon-Zugangsdaten.

Das Integrationslogo wird von Home Assistant ab Version 2026.3 direkt aus `custom_components/einkaufszettel/brand` geladen. Ältere HA-Versionen zeigen bei Custom Integrations weiterhin kein lokales Markenlogo an.

## Quellliste erneut kopieren

Unter **Einstellungen → Geräte & Dienste → Einkaufszettel → Entitäten** den Button **„Einkaufszettel: Quellliste kopieren“** öffnen und **Drücken** wählen. Der Button kann auch in ein Dashboard gelegt oder mit `button.press` aufgerufen werden.

- Nur unbekannte, offene Quell-IDs werden hinzugefügt; wiederholtes Drücken erzeugt keine Duplikate.
- Vorhandene lokale Namen, Beschreibungen, Fälligkeiten und Erledigt-Status bleiben erhalten. Abgehakte Artikel werden nicht wieder geöffnet.
- Gleicher Name mit einer neuen Quell-ID gilt als neuer Eintrag. Fehlen stabile Quell-IDs, wird mit einer Fehlermeldung abgebrochen statt nach Namen zu raten.
- Quelländerungen und -löschungen werden nicht zurückgespiegelt. Bei nicht erreichbarer Quelle oder fehlgeschlagenem Speichern bleibt der lokale Bestand unverändert.

## Offline-Web-App verwenden

1. In Home Assistant die neue **Einkaufszettel-Seite in der Seitenleiste** öffnen. Sie zeigt die Web-App direkt in Home Assistant; sie ist der normale Startweg.
2. Oben rechts das **Dreipunkte-Menü (Setup)** öffnen und **„App in eigenem Browserfenster öffnen / installieren“** wählen. Für Installation und Offline-Betrieb die HTTPS-Adresse verwenden, zum Beispiel über Nabu Casa. Im eigenen Browserfenster beim ersten Aufruf im Setup **Mit HA verbinden** wählen und Home Assistant den Zugriff erlauben; dann über **App installieren** oder das Browsermenü zum Startbildschirm hinzufügen.
3. Beim nächsten Einkauf das Homescreen-Symbol direkt starten; ohne Installation die Einkaufszettel-Seite in der HA-Seitenleiste öffnen.
4. Artikel hinzufügen, abhaken oder entfernen. Ohne Netz werden Änderungen in der lokalen Browser-Datenbank und einer dauerhaften Warteschlange gespeichert. Beim nächsten Start mit erreichbarem HA werden diese nacheinander übertragen.
5. Der Sync-Status zeigt ausstehende Änderungen. Bei abgelaufener Anmeldung im **Setup** **Mit HA verbinden** wählen und die Anmeldung erneut erlauben. Dort liegen auch **Alexa-Liste kopieren** und **Home Assistant öffnen**. Das Kopieren neuer Alexa-/Quelllistenartikel benötigt eine Verbindung.

Die PWA speichert ein Home-Assistant-Refresh-Token lokal im Browserprofil, damit sie unabhängig von der HA-Companion-App synchronisieren kann. Die Anmeldung wird über den offiziellen Home-Assistant-Autorisierungsdialog erteilt. Browserdaten nicht löschen, solange lokale Änderungen ausstehen; danach muss die App erneut verbunden werden. Der erste Offline-Sync verwendet stabile Aktions-IDs, damit ein nach Verbindungsabbruch wiederholter Artikel nicht doppelt angelegt wird. Bei gleichzeitigen Offline-Änderungen derselben Eigenschaft gilt die zuletzt synchronisierte Aktion; andere Eigenschaften desselben Eintrags bleiben davon unberührt.

### Mehrere Einkaufslisten

Die kleine Markenzeile bleibt **EINKAUFSZETTEL**; die große Überschrift zeigt den Namen der ausgewählten Liste. Direkt darunter lässt sich beispielsweise zwischen **Kaufland**, **Edeka** und **Baumarkt** wechseln.

- Neue Quelllisten weiterhin über Alexa anlegen und in HA bereitstellen. Die App erkennt externe HA-To-do-Listen automatisch unter **Setup → Listen verwalten**; eigene Einkaufszettel-Entitäten werden ausgeschlossen. Die Web-App legt keine Alexa- oder HA-Quelllisten an.
- Dort **In App anzeigen** über das Kontrollkästchen wählen, einen **App-Namen** vergeben und **Übernehmen** drücken. Der Alias wird zentral in HA gespeichert; Alexa- und HA-Quellnamen bleiben unverändert. Intern wird bei Bedarf automatisch ein quellgebundener Integrationseintrag mit eigenem Speicher angelegt; ein separater HA-Konfigurationsdurchlauf entfällt.
- Bestehende zusätzliche `todo`-Entitäten der Einkaufszettel-Integration werden beim Laden entfernt. Die externen Alexa-/HA-Quelllisten werden nicht entfernt oder umbenannt.
- Nach der Anmeldung werden alle geladenen Einkaufszettel-Listen angeboten und für den Offline-Zugriff zwischengespeichert. Bereits geladene Listen lassen sich auch ohne Netz wechseln.
- Artikel hinzufügen, abhaken und entfernen wie bisher; zum Bearbeiten des Namens den Artikelnamen antippen. Jede Liste hat ihre eigenen Artikel und ihre eigene Offline-Warteschlange.
- Beim Synchronisieren werden auch ausstehende Änderungen anderer verfügbarer Listen übertragen. Neue bzw. noch nicht zwischengespeicherte Listen benötigen zunächst eine Verbindung.
- **Alexa-Liste kopieren** im Setup bezieht sich immer auf die ausgewählte Liste und deren konfigurierte Quelle. Der bisherige Kopiermechanismus bleibt unverändert; es entsteht keine neue bidirektionale Alexa-Synchronisation.
- Ausgeblendete Listen verschwinden nach dem Online-Abgleich auch aus der Offline-Auswahl. Ihre internen Daten und ausstehenden Offline-Aktionen bleiben erhalten; ausstehende Aktionen werden nach erneutem Einblenden synchronisiert. Ohne Netz können Listen verwendet, aber keine gemeinsamen Einstellungen geändert werden.

## Daten und Grenzen

- Die Config Entry speichert Quell-Entity-ID und Listenname, keine Zugangsdaten.
- Die maßgebliche lokale Liste liegt dauerhaft im integrationsverwalteten HA-`Store` unter `.storage/einkaufszettel.<entry_id>`. Die PWA speichert den letzten Stand und ausstehende Aktionen zusätzlich gerätegebunden in IndexedDB.
- Die PWA greift direkt auf den integrationsverwalteten HA-Speicher zu. Eine zusätzliche `TodoListEntity` ist nicht erforderlich. Produktzuordnung, Kategorie, Menge und Einheit werden bei späterer Produktfunktion im eigenen Datenmodell geführt.
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
