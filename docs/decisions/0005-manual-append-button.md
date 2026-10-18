# ADR 0005: Manueller Kopieren-Knopf zum Ergänzen neuer Artikel

- **Status:** Angenommen
- **Datum:** 2026-10-18
- **Ergänzt:** ADR 0002 und ADR 0004

## Kontext

Nach dem Erstimport sollen neue Artikel aus der konfigurierten Alexa-/To-do-Quelle manuell übernommen werden können. Der Nutzer hat ausdrücklich Ergänzen statt Ersetzen gewählt. Lokale Notizen und Erledigt-Status dürfen nicht verloren gehen.

## Entscheidung

Eine HA-Button-Entität pro Konfiguration liest beim Drücken die offenen Quell-Einträge und ergänzt ausschließlich bisher unbekannte Quell-IDs. Alle vorhandenen lokalen Einträge, auch erledigte, zählen beim Abgleich als bereits importiert. Verschiedene Quell-IDs mit demselben Namen bleiben eigenständige Einkaufspositionen. Innerhalb derselben Antwort mehrfach vorkommende IDs werden nur einmal ergänzt.

Fehlende Quell-IDs führen bei manueller Ergänzung zu einem expliziten Fehler statt zu einem Namensabgleich. Das gilt auch für bereits lokal gespeicherte Einträge ohne Herkunfts-ID. Der ursprüngliche Erstimport bleibt unverändert.

Lesen, Zusammenführen und Speichern erfolgen unter demselben Eintrags-Lock wie lokale Änderungen. Erst nach erfolgreicher Persistierung wird die lokale Momentaufnahme ersetzt und die To-do-Entität über ein konfigurationsspezifisches Signal aktualisiert. Doppelte Klicks ergänzen denselben Artikel nicht zweimal.

## Folgen

Dies ist weiterhin kein automatischer Sync. Umbenennen, Abhaken und Löschen in der Quelle ändern vorhandene lokale Positionen nicht. Wiederöffnen derselben Quell-ID aktiviert keinen bereits erledigten lokalen Artikel. Ein neuer Einkauf desselben Produkts wird nur bei neuer Quell-ID als neuer Artikel erkannt. Die stabile Vergabe der Quell-IDs hängt von der Quellintegration ab.
