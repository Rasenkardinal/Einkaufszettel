# Easy Shopping

Flexible, gemeinsam nutzbare Einkaufsliste für Home Assistant mit frei zuordenbaren Kategorien und Alexa-Anbindung.

> **Projektstatus:** Alpha `0.1.0-alpha.3`. Konfigurationsflow, initialer Import, manueller Kopieren-Knopf und eine dauerhaft gespeicherte HA-To-do-Liste zum Abhaken. Noch keine automatische Synchronisierung und keine eigene Smartphone-UI.

## Ziel

Eine lokale, zuverlässige Einkaufsliste für mehrere Haushaltsmitglieder. Artikel sollen Produkten und frei sortierbaren Kategorien zugeordnet werden können. Home Assistant (HA) ist die Plattform und soll mit der bereits eingebundenen Alexa-Einkaufsliste zusammenarbeiten. Die erste Ausbaustufe importiert Einträge und erlaubt lokales Abhaken; Synchronisierung ist später vorgesehen.

## Funktionsumfang der Alpha

- Eine vorhandene HA-To-do-Liste wird im Integrations-Konfigurationsflow ausgewählt. Voraussetzung ist, dass die Alexa-Liste in HA als `todo`-Entität mit lesbaren Einträgen verfügbar ist.
- Offene Quell-Einträge werden einmalig in eine eigene Easy-Shopping-Liste kopiert.
- Ein manueller Kopieren-Knopf ergänzt später neue offene Quell-Einträge anhand ihrer Quell-IDs. Bereits kopierte Einträge bleiben unverändert.
- Easy Shopping stellt eine eigene HA-To-do-Listen-Entität bereit, die in HA angezeigt und abgehakt werden kann.
- Die Kopie ist lokal und dauerhaft; Änderungen werden in dieser Version nicht zurück zur Quelle synchronisiert.
- Abhaken und Wiederöffnen, Bearbeiten des Namens sowie der Beschreibung und Fälligkeit erfolgen über die HA-To-do-Oberfläche.
- Gleichnamige Einträge bleiben getrennt. Jeder kopierte Eintrag erhält eine eigene stabile ID.
- Hinzufügen, Löschen, Kategorien, Produktkatalog und strukturierte Mengen sind noch nicht implementiert.

## Installation und Benutzung

### HACS

In HACS unter **Benutzerdefinierte Repositories** die URL `https://github.com/Rasenkardinal/Easy-Shopping` mit dem Typ **Integration** hinzufügen und herunterladen. Danach HA neu starten und Easy Shopping unter **Geräte & Dienste** hinzufügen.

Falls HACS meldet, dass Commit `f7858a4` nicht verwendet werden kann: Dieser ältere Stand enthält noch keine HACS-Metadaten. In HACS die Repository-Informationen aktualisieren (gegebenenfalls das Repository erneut öffnen oder HACS neu laden) und den aktuellen Stand von `main` herunterladen. Den alten Commit nicht erneut auswählen.

### Manuelle Installation

1. Voraussetzung: Home Assistant mit To-do-Unterstützung (API-Basis: HA 2025.10) und eine bereits verfügbare Quellliste als `todo`-Entität. Easy Shopping übernimmt weder die Alexa-Anmeldung noch die Anbindung von Amazon.
2. Den vollständigen Ordner [custom_components/easy_shopping](custom_components/easy_shopping) in den HA-Konfigurationsordner unter `custom_components/easy_shopping` kopieren. Eine eventuell vorhandene ältere Version dieses Integrationsordners vorher sichern.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Easy Shopping** öffnen.
5. Die Quell-To-do-Liste auswählen und einen Namen für die lokale Kopie vergeben. Im Flow wird die Lesbarkeit geprüft; beim anschließenden Einrichten wird der aktuelle Inhalt importiert.
6. In der HA-Seitenleiste **To-do-Listen** öffnen und die neue Liste auswählen. Der Standardname ist **Easy Shopping**; die Entitäts-ID wird von HA vergeben (normalerweise `todo.easy_shopping`).
7. Einträge abhaken oder wieder öffnen. Die Quellliste bleibt unverändert.

Easy Shopping ist als Service-Integration eingestuft und wird unter **Einstellungen → Geräte & Dienste → Integrationen** verwaltet. Version `0.1.0-alpha.1` war noch als Helper eingestuft und kann deshalb nur unter **Helfer** statt in der normalen Integrationsübersicht auftauchen. Nach dem Update auf `0.1.0-alpha.2` HA neu starten; eine bestehende Konfiguration und ihre kopierte Liste bleiben erhalten. Die Integration nicht löschen und neu hinzufügen.

Optional lässt sich die HA-Standardkarte auf einem Dashboard verwenden. Die tatsächliche Entitäts-ID gegebenenfalls anpassen:

```yaml
type: todo-list
entity: todo.easy_shopping
```

**Wichtig:** Nur offene Einträge werden kopiert. Neue Alexa-Einträge nach dem Import erscheinen nicht automatisch in Easy Shopping, sondern erst beim manuellen Kopieren. Der Neustart oder das Neuladen der Integration löst keinen erneuten Import aus, auch bei leerer lokaler Liste. Pro Quell-Entitäts-ID ist ein Konfigurationseintrag vorgesehen.

### Alexa-/Quellliste erneut kopieren

Nach dem Update auf Alpha `0.1.0-alpha.3` HA neu starten. Unter **Einstellungen → Geräte & Dienste → Easy Shopping → Entitäten** die Button-Entität **„Easy Shopping: Quellliste kopieren“** öffnen und **Drücken** wählen. Bei einem abweichenden Listennamen trägt der Knopf diesen Namen. Die Entität kann außerdem als Button auf ein Dashboard gelegt oder über `button.press` angesprochen werden.

- Nur bisher unbekannte, offene Quell-IDs werden ergänzt. Wiederholtes Drücken erzeugt keine Duplikate derselben Quell-ID.
- Bereits kopierte Artikel bleiben unverändert: lokale Namen, Notizen, Fälligkeit und Erledigt-Status werden nicht zurückgesetzt. Ein bereits abgehakter Artikel wird durch erneutes Kopieren nicht wieder geöffnet.
- Derselbe Artikelname mit einer neuen Quell-ID gilt als neuer Eintrag. Das Wiederöffnen einer alten Quell-ID gilt dagegen nicht als neuer Einkauf.
- Die Quelle wird weder abgehakt noch anderweitig verändert. Änderungen und Löschungen der Quelle werden nicht auf bestehende lokale Einträge übertragen.
- Sicheres wiederholtes Kopieren benötigt stabile, nichtleere Quell-IDs. Fehlen sie an aktuellen oder früher importierten Einträgen, meldet der Knopf einen Fehler und verändert die Liste nicht, statt anhand von Namen zu raten.
- Ist die Quelle nicht erreichbar oder schlägt das Speichern fehl, wird ein Fehler gemeldet und der lokale Bestand bleibt erhalten.

## Daten und Fehlerverhalten

- Die Config Entry enthält Quell-Entitäts-ID und Listenname, keine Amazon-Zugangsdaten.
- Der HA-`Store`-Helper speichert die lokale Liste als versionierte JSON-Daten unter `.storage/easy_shopping.<entry_id>` im HA-Konfigurationsordner. Die Einträge enthalten lokale ID, Quell-ID (falls geliefert), Text, Status sowie optionale Beschreibung und Fälligkeit.
- Erst nach erfolgreichem Speichern wird eine Änderung in HA veröffentlicht. Ein Speicherfehler wird gemeldet; die bisherige lokale Momentaufnahme bleibt erhalten.
- Ist die Quelle beim Erstimport nicht lesbar, wird die Einrichtung mit sichtbarem Fehler bzw. Wiederholungsversuch nicht als erfolgreicher leerer Import behandelt. Nach einem erfolgreichen Import wird die Quelle für lokale Änderungen und Neustarts nicht mehr benötigt.
- Beschädigte gespeicherte Daten werden nicht durch einen erneuten Import überschrieben.
- Entladen löscht keine Daten. In dieser Alpha gibt es bewusst auch beim Entfernen der Integration keine automatische Löschung der Speicherdatei. Erneutes Hinzufügen erzeugt eine neue Config Entry und eine neue Kopie; alte Daten werden nicht automatisch wieder zugeordnet.
- Die Speicherdateien nicht manuell bearbeiten. HA-Konfigurationsbackups einschließlich `.storage` verwenden; die Integration ist noch keine produktiv erprobte Datensicherung.
- Ohne erreichbares Home Assistant ist die Liste auch in der Companion App nicht verfügbar. Dies ist keine Offline-App.

## Entwicklung und Tests

Die portable Modellsuite benötigt Python 3.13 und die Entwicklungsabhängigkeiten:

```text
python -m pip install -r requirements-dev.txt
python -m pytest tests/unit
ruff check .
ruff format --check .
```

Die zusätzliche Integrationssuite prüft mit echtem Home Assistant den Konfigurationsflow, To-do-Services, Anzeigezustand, Abhaken/Wiederöffnen, parallele Änderungen, Speicherfehler, leere Kopien und Neuladen bei nicht erreichbarer Quelle. Die Linux-CI installiert über [requirements-test-ha.txt](requirements-test-ha.txt) eine festgelegte Testumgebung auf Basis HA 2025.10.0:

```text
python -m pip install -r requirements-test-ha.txt
python -m pytest
```

Die Integrationssuite benötigt eine von HA unterstützte Testumgebung; ein erfolgreicher Modelltest allein ersetzt keinen Test des Konfigurationsflows in HA. Die konkrete Alexa-Integration und die Anzeige auf dem Smartphone müssen zusätzlich in der Zielinstallation geprüft werden.

### Prüfstand dieser Alpha

Lokal unter Windows/Python 3.13 wurden 46 Tests erfolgreich ausgeführt: Modelltests, Paketmetadaten und Tests unserer Import-/Speicher-/Entitätslogik mit ausdrücklich simulierten HA-Schnittstellen, einschließlich des Kopieren-Knopfs. Ruff, Formatierung, Python-Syntax und JSON-Metadaten sind geprüft. Die Tests mit echtem HA konnten lokal nicht ausgeführt werden: Die Testabhängigkeit `lru-dict` ließ sich ohne Microsoft-C++-Build-Tools nicht installieren. Die Linux-CI ist vorbereitet, aber dieses Ergebnis ersetzt keinen erfolgreichen CI-Lauf oder Test in der Zielinstallation.

Vor produktiver Verwendung in HA prüfen:

1. Eine Test-Quellliste mit zwei offenen und einem erledigten Eintrag auswählen; nur die zwei offenen Positionen müssen in der Kopie erscheinen.
2. Abhaken und Wiederöffnen testen; die Quelle muss unverändert bleiben.
3. HA neu starten; lokale IDs und Erledigt-Status müssen erhalten bleiben.
4. Die Quelle vorübergehend nicht verfügbar machen und die bestehende Kopie weiter verwenden.
5. Eine leere Quellliste kopieren, anschließend neue Quelleinträge hinzufügen und neu laden: Die lokale Kopie muss leer bleiben.
6. Einen neuen Artikel in der Quelle ergänzen, den Kopieren-Knopf zweimal drücken: genau ein neuer lokaler Eintrag muss erscheinen; zuvor lokal abgehakte Artikel müssen erledigt bleiben.

## Dokumentation

- [Architekturentscheidungen (ADRs)](docs/decisions/README.md)
- [ADR 0001: Home Assistant als Plattform und To-do-Entität](docs/decisions/0001-home-assistant-todo-entity.md)
- [ADR 0002: Eigene Datenhaltung und initialer Import](docs/decisions/0002-owned-data-and-import.md)
- [ADR 0003: Produktdaten und Listeneinträge trennen](docs/decisions/0003-products-and-list-items.md)

## Geplante Architektur (Entwurf)

- **Quellliste:** vorhandene `todo`-Entität (beispielsweise die in HA synchronisierte Alexa-Liste).
- **Easy-Shopping-Liste:** eigene `TodoListEntity`-Entität für die HA-To-do-Schnittstelle.
- **Integration:** persistiert in der Alpha die Listeneinträge in integrationsverwaltetem HA-Speicher; die Config Entry hält die Quelllisten-Auswahl und Integrationskonfiguration. Produkt- und Kategoriedaten folgen später.
- **Oberfläche:** zunächst HA-To-do-Ansicht; eine eigene, einkaufsoptimierte UI ist ein späterer Schritt und noch nicht festgelegt.

## Wichtige Einschränkung

HA-To-do-Einträge bieten standardisierte Felder wie eindeutige ID, Zusammenfassung, Status und optionale Beschreibung. Kategorien, Produktzuordnungen und strukturierte Mengen/Einheiten gehören zum Easy-Shopping-Datenmodell und werden separat persistent gehalten. Die HA-To-do-Entität dient als kompatible Sicht und Bedienoberfläche, nicht als vollständiges Produktschema.
