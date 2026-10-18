# ADR 0004: Alpha-Umfang und Import-Lebenszyklus

- **Status:** Angenommen
- **Datum:** 2026-10-18

## Kontext

Die erste Implementierung soll Konfigurationsflow, Kopie der Quellliste und Anzeige mit Abhaken bereitstellen. Produktkatalog, Kategorien und eigene UI bleiben spätere Schritte. Ein Neustart darf weder erledigte Einträge zurücksetzen noch lokale Daten durch die Quelle ersetzen.

## Entscheidung

- Die Quellliste wird mit einem auf die HA-Domäne `todo` beschränkten Entity-Selector ausgewählt. Eigene Easy-Shopping-Listen sind ausgeschlossen. Der Flow prüft die Lesbarkeit und verhindert eine zweite Konfiguration derselben Quell-Entitäts-ID.
- Beim erstmaligen Setup ohne vorhandenen Store werden offene Einträge übernommen. Die Prüfung im Flow ist kein dauerhaft gespeicherter Import; für das Setup wird die Quelle nochmals gelesen.
- Nur das Fehlen des Stores löst den Erstimport aus. Eine erfolgreich gespeicherte leere Liste ist gültig und wird nicht erneut importiert.
- Einträge erhalten neue lokale UUIDs. Quell-UIDs werden nur als Herkunftsreferenz gespeichert. Gleichnamige Einträge bleiben getrennt; es wird nicht automatisch addiert oder zusammengeführt.
- Die HA-To-do-Liste unterstützt in der Alpha Aktualisierungen: Abhaken/Wiederöffnen, Name, Beschreibung und Fälligkeit. Hinzufügen, Löschen und manuelles Umsortieren sind nicht freigeschaltet.
- Jede Änderung wird vor Veröffentlichung gespeichert. Ein Lock serialisiert Schreiboperationen, damit paralleles Abhaken verschiedener Positionen nicht die gesamte Liste mit einem veralteten Snapshot überschreibt.
- Eine beschädigte Speicherdatei führt zu einem sichtbaren Setup-Fehler und nicht zu einem neuen Import oder einer leeren Ersatzliste.
- Neuladen und Entfernen löschen den Store in dieser Alpha nicht automatisch. Ein erneut hinzugefügter Konfigurationseintrag erhält einen neuen Store; eine Oberfläche für Wiederherstellung/Bereinigung gehört noch nicht zum Umfang.

## Folgen

Die Alpha ist als unabhängige lokale Kopie nutzbar, aber nicht als laufende Alexa-Synchronisierung. Standard-To-do-Oberfläche und Dashboard-Karte reichen für die erste Anzeige. Die spätere Synchronisierung benötigt eigene Regeln für Identitäten, Löschungen, Konflikte und Wiederholungen. Der spätere Produktkatalog wird nicht vorweg als bereits implementiert dargestellt.
