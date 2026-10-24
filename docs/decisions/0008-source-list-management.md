# ADR 0008: HA-Quelllisten und gemeinsame App-Anzeigenamen

- **Status:** Angenommen
- **Datum:** 2026-10-21
- **Ersetzt:** ADR 0001 hinsichtlich eigener sichtbarer To-do-Entitaeten und Quellwahl im Benutzer-Konfigurationsflow.

## Entscheidung

Home Assistant bleibt zentrale Datenhaltung und Synchronisationszentrum. Neue Quelllisten werden weiterhin ueber Alexa angelegt und durch die vorhandene Alexa-Anbindung in HA bereitgestellt. Einkaufszettel erstellt keine externen Listen.

Die App bietet unter **Setup > Listen verwalten** vorhandene externe HA-To-do-Listen an. Alle angemeldeten HA-Nutzer koennen diese aktivieren, ausblenden und kurze Anzeigenamen vergeben. Diese Einstellungen liegen in HA und gelten fuer alle Benutzer. Alexa- und HA-Quellnamen bleiben unveraendert.

Der Benutzer richtet die Integration nur einmal ein. Fuer aktivierte Quellen werden interne quellgebundene Konfigurationseintraege automatisch ueber den Importflow angelegt. Diese halten Namen, Sichtbarkeit und interne Listendaten. Die bisherige Initialkopie und der manuelle Kopierer bleiben unveraendert; ein bidirektionaler Alexa-Sync ist nicht Teil dieser Entscheidung.

Es werden keine eigenen To-do-Listen-Entitaeten mehr erzeugt. Alte eigene To-do-Registry-Eintraege werden beim Laden entfernt; externe Quellen sind davon ausgeschlossen. Die PWA arbeitet direkt mit dem internen HA-Speicher und getrennten Offline-Warteschlangen.

## Folgen

- Keine doppelten Listen in der HA-To-do-Ansicht.
- Die Listenauswahl zeigt App-Anzeigenamen statt langer Alexa-Namen.
- Gemeinsame Listenverwaltung erfordert eine Verbindung und HA-Anmeldung, aber keine Administratorrechte. Bereits geladene Listen bleiben offline nutzbar.
- Ausblenden entfernt keine Alexa-Liste. Ausstehende Offline-Aktionen ausgeblendeter Listen werden erst nach erneutem Einblenden uebertragen.
- Dashboards und Automationen mit bisherigen Einkaufszettel-To-do-Entities muessen angepasst werden.
