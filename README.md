# Einkaufszettel

Eine gemeinsam nutzbare Einkaufsliste für Home Assistant mit eigener Produkt- und Kategorienlogik sowie Alexa-Anbindung über eine vorhandene HA-To-do-Liste.

> **Projektstatus:** Alpha. Enthält HA-Quelllistenverwaltung, automatischen Quellabgleich, gemeinsame Produktkategorien und Supermärkte mit eigener Kategorienreihenfolge sowie eine installierbare Offline-PWA. Die Integration erzeugt keine zusätzlichen To-do-Listen. Produktnamen und Nutzungsstatistiken werden für lokale Vorschläge gespeichert; eine Oberfläche zur eigenständigen Produktkatalogverwaltung gibt es noch nicht.

## Funktionsumfang

- Vorhandene externe HA-To-do-Listen werden unter **Setup → Listen verwalten** in der App angeboten. Dort werden Listen aktiviert und kurze App-Anzeigenamen vergeben.
- Offene Einträge werden beim ersten Aktivieren in einen internen HA-Speicher kopiert.
- Ein Button ergänzt später neue, offene Quell-Einträge anhand ihrer Quell-IDs, ohne vorhandene lokale Änderungen zurückzusetzen.
- Die PWA unterstützt Hinzufügen, Abhaken/Wiederöffnen, Umbenennen und Löschen. Es erscheint keine doppelte Einkaufszettel-Liste in der HA-To-do-Ansicht.
- Name und Status werden automatisch mit der Quelle abgeglichen; App-Änderungen werden zurückgeschrieben, soweit die Quelle die jeweilige Aktion unterstützt. Zusatzinformationen bleiben in unserem HA-Speicher.
- Produktkategorien werden gemeinsam gespeichert und alphabetisch A–Z verwaltet. Je Supermarkt lassen sich Kategorien auswählen und unabhängig sortieren; „Ohne Kategorie“ kann dort im Einkaufsmodus positioniert werden und bleibt im Planungsmodus oben. Die Hauptliste verwendet dezente Kategorieüberschriften mit Trennlinien.
- Zu jedem Supermarkt kann eine Bonuskarten- oder APP-Code-Grafik hinzugefügt werden. Das Bild wird gemeinsam in Home Assistant gespeichert und beim Start des Kassiervorgangs zusammen mit der Pfandbon-Erinnerung angezeigt.
- Artikel können eine Kategorie, eine Mengenangabe als Freitext und Zusatzinformationen erhalten. Diese Daten werden mit der vorhandenen Offline-Warteschlange gespeichert. Im Planungsmodus erscheinen zu Beginn passende Produktvorschläge aus bereits verwendeten Namen; über **＋** lassen sich außerdem häufige, kürzliche oder regelmäßige Artikel per Mehrfachauswahl ergänzen. Kategorie, Häufigkeit und letzter Verwendungszeitpunkt werden berücksichtigt. Eine Oberfläche zur eigenständigen Produktverwaltung und strukturierte Mengeneinheiten sind noch nicht implementiert.
- In den Kategorie- und Bonuskarten-Einstellungen bleiben Bestätigungsaktionen auch bei langen Inhalten am unteren Bildschirmrand erreichbar.
- Die Smartphone-Oberfläche wird als PWA von der Integration über Home Assistant ausgeliefert. App-Dateien und Listendaten werden lokal gespeichert; Hinzufügen, Abhaken und Löschen werden offline vorgemerkt und beim nächsten Verbinden synchronisiert.

## Installation mit HACS

1. In HACS das Repository `https://github.com/Rasenkardinal/Einkaufszettel` als **Integration** hinzufügen oder den bereits vorhandenen Repository-Eintrag aktualisieren.
2. Das aktuelle Release herunterladen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Einkaufszettel** öffnen.
5. Einrichtung bestätigen. Die Quelllisten werden anschließend in der App verwaltet.
6. In der Web-App **Setup → Listen verwalten** öffnen, gewünschte HA-Listen aktivieren und kurze Anzeigenamen vergeben. Diese Einstellungen benötigen HA-Administratorrechte und gelten für alle Haushaltsmitglieder.
7. Die neue Einkaufszettel-Seite erscheint in der Home-Assistant-Seitenleiste. Dort die Liste öffnen. Der Button **„Web-App öffnen / installieren“** unter den Integration-Entitäten erzeugt zusätzlich eine Benachrichtigung mit dem direkten App-Link.

Die Installation benötigt HTTPS, beispielsweise über Nabu Casa. Die PWA muss mindestens einmal online geladen und synchronisiert worden sein, bevor sie offline verwendet werden kann. Im installierten Modus kann sie ohne normale Browser-Adressleiste starten. Der Installationsdialog wird abhängig vom Browser angeboten; auf iOS kann stattdessen die Browserfunktion **Teilen → Zum Home-Bildschirm** nötig sein.

Nach einem Update die Web-App online neu laden. JavaScript und CSS tragen eine gemeinsame Versionskennung, damit eine neue HTML-Seite keine alten Dateien aus dem Offline-Cache verwendet. Nach dem Laden des aktualisierten Offline-Caches ist die neue Oberfläche auch ohne Netz verfügbar. Browserdaten müssen dafür nicht gelöscht werden.
