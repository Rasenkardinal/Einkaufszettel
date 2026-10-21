# ADR 0007: Offline-First-PWA und Hosting über Home Assistant

- **Status:** Angenommen
- **Datum:** 2026-10-21

## Kontext

Die Home Assistant Companion App benötigt eine Netzwerkverbindung zu Home Assistant, um dessen Oberflächen aufzurufen. Beim Einkaufen ist diese Verbindung nicht immer verfügbar. Eine reine HA-To-do-Entität oder Lovelace-Oberfläche kann deshalb nicht die alleinige Smartphone-Lösung sein.

Home Assistant bleibt die lokale Datenhaltung und gemeinsame Synchronisationszentrale des Haushalts. Der Nutzer hat zudem einen Nabu Casa Cloudzugang mit HTTPS. Eine zusätzliche dauerhaft betriebene Webserver-Infrastruktur soll vermieden werden.

## Entscheidung

1. Die Smartphone-Oberfläche wird als installierbare Progressive Web App (PWA) konzipiert und offline-first umgesetzt.
2. Die statischen App-Dateien werden durch die Einkaufszettel-Integration über Home Assistant bereitgestellt. Für Betrieb und Hosting wird kein separater Webserver vorausgesetzt. Der konfigurierte HTTPS-Zugang, etwa über Nabu Casa, dient dem initialen Laden, der Installation und späterer Verbindung zur HA-Synchronisation.
3. Die PWA speichert die für den Offline-Betrieb benötigten App-Dateien lokal im Service-Worker-Cache und den zuletzt synchronisierten Einkaufslistenstand sowie noch nicht synchronisierte Änderungen lokal auf dem jeweiligen Gerät. Die lokale Liste ist ein gerätegebundener Cache/Arbeitsstand; Home Assistant bleibt die gemeinsame maßgebliche Datenhaltung.
4. Beim ersten Öffnen beziehungsweise vor der ersten Offline-Nutzung muss das Gerät die App und die Liste online geladen haben. Ohne Verbindung zu HA oder bereits gespeicherte lokale Daten kann die App keine aktuelle Liste bereitstellen.
5. Bearbeitungen im Offlinebetrieb werden lokal vorgemerkt und bei wiederhergestellter Verbindung mit HA synchronisiert. Öffnen beziehungsweise manuelles Anstoßen der Synchronisation sind für den ersten Umfang ausreichend; zuverlässige Hintergrundsynchronisierung wird nicht vorausgesetzt.
6. Die erste Synchronisationsversion überträgt einzelne Aktionen und niemals einen vollständigen Offline-Snapshot über die HA-Liste. Neue Artikel bekommen clientseitig stabile IDs und werden idempotent angelegt; Abhaken/Wiederöffnen aktualisiert nur den Status des betroffenen Eintrags; Löschen erfolgt anhand seiner ID. Bei gleichzeitigen Änderungen derselben Eigenschaft gilt die zuletzt beim Server eintreffende Aktion. Andere Eigenschaften des Eintrags werden nicht überschrieben.
7. Alexa-Spracheingabe und Änderungen anderer Nutzer können ohne jeweilige Netzwerkverbindung nicht live übernommen werden. Sie werden erst nach späterer Verbindung und Synchronisation sichtbar.
8. Die PWA soll im installierten Modus ohne normale Browser-Adressleiste starten. Das Layout wird für eine immersive, möglichst vollflächige Darstellung ausgelegt; die genaue Vollbilddarstellung (z. B. Statusleiste, Systemleisten und iOS-Verhalten) hängt von Browser und Betriebssystem ab und wird auf den Zielgeräten geprüft.
9. Die erste Verbindung der PWA zu HA erfolgt über den Home-Assistant-Autorisierungsdialog. Die PWA speichert das ausgegebene Refresh-Token lokal im Browserprofil, damit die eigenständige App ohne Zugriff auf den HA-Frontend-Speicher synchronisieren kann; sie fordert bei Bedarf ein neues Zugriffstoken an. PKCE wird verwendet, wenn der HA-Autorisierungsserver es anbietet.

## Folgen

- HA-Hosting und Nabu Casa HTTPS vermeiden einen zusätzlichen Webserver, erfordern aber eine erreichbare HA-Instanz für Erstinstallation und Synchronisation.
- Offlinebetrieb ist auf bereits geladene App-Dateien und Daten beschränkt. Ein unvorbereiteter Browser oder ein Gerät mit gelöschtem Webspeicher kann offline nicht nachträglich initialisiert werden.
- Browser- und Betriebssystemdaten können gelöscht oder bereinigt werden. Deshalb muss die App ausstehende Änderungen sichtbar machen und nach Wiederverbindung zuverlässig synchronisieren; die lokale Kopie ersetzt kein Backup.
- Die Companion App kann zum erstmaligen Öffnen/Installieren dienen. Bei fehlendem HA-Zugang wird die zuvor installierte PWA direkt über ihr Homescreen-/App-Symbol gestartet, nicht durch erneutes Navigieren innerhalb der Companion App.
- Die Alpha `0.3.0-alpha.1` liefert die PWA-Shell, eine gerätegebundene IndexedDB-Warteschlange und authentifizierte HA-WebSocket-Befehle für Listenlesen, Hinzufügen, Statusänderung, Löschen und Quelllisten-Kopie. Produkt-/Kategorie-Konflikte sind noch nicht relevant, da diese Felder noch nicht implementiert sind.
- Das gerätegebundene Refresh-Token wird im lokalen Browserprofil gespeichert und mit dem Löschen der Browserdaten entfernt. Die erneute Anmeldung erfordert eine Verbindung und Freigabe durch einen HA-Benutzer. Token-Erneuerung, Vollbilddarstellung und Offlinewiederherstellung sind in Zielbrowsern zu testen.
- Vollbild bedeutet zunächst „standalone/immersive App-Darstellung“ und keine Zusage, dass auf jedem Gerät auch Status- und Systemleisten vollständig verborgen werden können.
