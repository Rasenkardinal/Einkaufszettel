# Einkaufszettel

Eine gemeinsam nutzbare Einkaufsliste für Home Assistant mit eigener Produkt- und Kategorienlogik sowie Alexa-Anbindung über eine vorhandene HA-To-do-Liste.

> **Projektstatus:** Alpha. Enthält HA-Quelllistenverwaltung, automatischen Quellabgleich, gemeinsame Produktkategorien und Supermärkte mit eigener Kategorienreihenfolge sowie eine installierbare Offline-PWA. Die Integration erzeugt keine zusätzlichen To-do-Listen. Produktnamen und Nutzungsstatistiken werden gemeinsam gespeichert und können unter **Artikel verwalten** bereinigt werden.

## Funktionsumfang

Alle angemeldeten HA-Nutzer können Listen, Kategorien, Supermärkte und den Artikelkatalog in der App verwalten; HA-Administratorrechte sind dafür nicht erforderlich. Änderungen einschließlich Löschungen gelten für alle Nutzer. Die Einrichtung der Integration und die technische HA-Konfiguration bleiben davon unberührt.

- Vorhandene externe HA-To-do-Listen werden unter **Einstellungen → Synchronisation → Listen verwalten** in der App angeboten. Dort werden Listen aktiviert und kurze App-Anzeigenamen vergeben.
- Offene Einträge werden beim ersten Aktivieren in einen internen HA-Speicher kopiert.
- Ein Button ergänzt später neue, offene Quell-Einträge anhand ihrer Quell-IDs, ohne vorhandene lokale Änderungen zurückzusetzen.
- Die PWA unterstützt Hinzufügen, Abhaken/Wiederöffnen, Umbenennen und Löschen. Es erscheint keine doppelte Einkaufszettel-Liste in der HA-To-do-Ansicht.
- Name und Status werden automatisch mit der Quelle abgeglichen; App-Änderungen werden zurückgeschrieben, soweit die Quelle die jeweilige Aktion unterstützt. Zusatzinformationen bleiben in unserem HA-Speicher.
- Produktkategorien werden gemeinsam gespeichert und alphabetisch A–Z verwaltet. Je Supermarkt lassen sich Kategorien auswählen und unabhängig sortieren; „Ohne Kategorie“ kann dort im Einkaufsmodus positioniert werden und bleibt im Planungsmodus oben. Die Hauptliste verwendet dezente Kategorieüberschriften mit Trennlinien.
- Zu jedem Supermarkt kann eine Bonuskarten- oder APP-Code-Grafik hinzugefügt werden. Unter **Supermarkt bearbeiten** steuern die Schalter **Pfandbon Hinweis** und **Anzeige Bonuskarte** unabhängig voneinander die Anzeige beim Kassiervorgang. Beide sind standardmäßig eingeschaltet, auch bei bestehenden Supermärkten. Ohne aktivierten Hinweis und ohne anzuzeigende Bonuskarte erscheint direkt die Bestätigung zum Beenden des Einkaufs. Die manuelle Bonuskartenanzeige bleibt verfügbar. Die Optionen werden beim Speichern gemeinsam für alle Nutzer in Home Assistant hinterlegt und offline zwischengespeichert.
- Artikel können eine Kategorie, eine Mengenangabe als Freitext und Zusatzinformationen erhalten. Diese Daten werden mit der vorhandenen Offline-Warteschlange gespeichert. Im Planungsmodus erscheinen zu Beginn passende Produktvorschläge aus bereits verwendeten Namen; über **＋** lassen sich außerdem häufige, kürzliche oder regelmäßige Artikel per Mehrfachauswahl ergänzen. Kategorie, Häufigkeit und letzter Verwendungszeitpunkt werden berücksichtigt. Strukturierte Mengeneinheiten sind noch nicht implementiert.
- Unter **Verwalten → Artikel verwalten** lassen sich Artikel suchen, hinzufügen und umbenennen. Ohne Ähnlichkeitshinweis stehen **Umbenennen ›** und **Zusammenführen ›** als gleichwertige Sekundärbuttons ohne Rand unter dem Namen; **Löschen** bleibt separat darunter. Bei ähnlich geschriebenen Namen werden beide Artikel zum Vergleich angezeigt und **Umbenennen** steht neben dem gespeicherten Namen; falsche Vorschläge können mit **Kein Fehler** dauerhaft ausgeblendet werden. **Zusammenführen** erscheint bei einem Vorschlag nur im Vergleich, ansonsten als manuelle Aktion. Verwendungen und Wochenstatistiken bleiben beim Zusammenführen erhalten; aktive App-Listen werden aktualisiert und Änderungen an verbundenen HA-Quelllisten beim nächsten Abgleich zurückgeschrieben. Auch verwendete Artikel können gelöscht werden. Der App-Dialog warnt: „Statistik für diesen Artikel wird ebenfalls gelöscht! Bisher X Verwendungen“ und nennt gegebenenfalls alle betroffenen App-Listen. **Abbrechen** ändert nichts; **Löschen** entfernt den Artikel, seine Nutzungs- und Wochenstatistik und alle Einträge auf den bestätigten Listen (auch abgehakte Einträge und deaktivierte App-Listen). Verbundene HA-/Alexa-Listen werden beim nächsten Quellabgleich aktualisiert, sofern die Quelle das Löschen unterstützt. Haben sich die betroffenen Listen zwischenzeitlich geändert, ist eine erneute Bestätigung erforderlich. Können nicht alle Listen geprüft werden, wird das Löschen mit einem Hinweis abgebrochen.
- In der Artikel-, Supermarkt- und Kategorieverwaltung bleiben **Artikel hinzufügen**, **Supermarkt hinzufügen** beziehungsweise **Kategorie hinzufügen** in einem festen Footer am unteren Bildschirmrand erreichbar, während die jeweilige Liste separat scrollt. Auch in den Kategorie- und Bonuskarten-Einstellungen bleiben Bestätigungsaktionen bei langen Inhalten unten erreichbar.
- Die Smartphone-Oberfläche wird als PWA von der Integration über Home Assistant ausgeliefert. App-Dateien und Listendaten werden lokal gespeichert; Hinzufügen, Abhaken und Löschen werden offline vorgemerkt und beim nächsten Verbinden synchronisiert.

## Installation mit HACS

1. In HACS das Repository `https://github.com/Rasenkardinal/Einkaufszettel` als **Integration** hinzufügen oder den bereits vorhandenen Repository-Eintrag aktualisieren.
2. Das aktuelle Release herunterladen.
3. Home Assistant neu starten.
4. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Einkaufszettel** öffnen.
5. Einrichtung bestätigen. Die Quelllisten werden anschließend in der App verwaltet.
6. In der Web-App **Einstellungen → Synchronisation → Listen verwalten** öffnen, gewünschte HA-Listen aktivieren und kurze Anzeigenamen vergeben. Alle angemeldeten HA-Nutzer können diese Einstellungen ändern; sie gelten für alle Haushaltsmitglieder.
7. Die neue Einkaufszettel-Seite erscheint in der Home-Assistant-Seitenleiste. Dort die Liste öffnen. Der Button **„Web-App öffnen / installieren“** unter den Integration-Entitäten erzeugt zusätzlich eine Benachrichtigung mit dem direkten App-Link.

Die Installation benötigt HTTPS, beispielsweise über Nabu Casa. Die PWA muss mindestens einmal online geladen und synchronisiert worden sein, bevor sie offline verwendet werden kann. Im installierten Modus kann sie ohne normale Browser-Adressleiste starten. Der Installationsdialog wird abhängig vom Browser angeboten; auf iOS kann stattdessen die Browserfunktion **Teilen → Zum Home-Bildschirm** nötig sein.

Die Web-App prüft bei jedem Öffnen und bei erneuter Verbindung aktiv auf eine neue Version. Nach dem Download der neuen App-Dateien übernimmt der Service Worker das Update, löscht den alten App-Shell-Cache und lädt die neue Oberfläche. Dieser Cache enthält nur App-Dateien; lokal gespeicherte Listen und noch nicht synchronisierte Änderungen bleiben erhalten. Die Versionsnummer steht unten im Menü.
