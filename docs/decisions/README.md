# Architekturentscheidungen

Diese Architecture Decision Records (ADRs) halten wichtige Architekturentscheidungen und ihre Begründung nachvollziehbar fest. Ein ADR beschreibt eine Entscheidung zum Zeitpunkt ihrer Annahme; neue Erkenntnisse führen zu einem neuen oder ersetzenden ADR, nicht zum stillen Umschreiben der Historie.

## Statuslegende

- **Vorgeschlagen:** noch nicht beschlossen.
- **Angenommen:** gilt als Projektentscheidung.
- **Ersetzt:** durch eine spätere Entscheidung abgelöst.

## Entscheidungen

| ADR | Titel | Status |
| --- | --- | --- |
| [0001](0001-home-assistant-todo-entity.md) | Home Assistant und To-do-Entität als Plattform | Angenommen |
| [0002](0002-owned-data-and-import.md) | Eigene Datenhaltung und einmaliger Listenimport | Angenommen |
| [0003](0003-products-and-list-items.md) | Produktkatalog von konkreten Listeneinträgen trennen | Angenommen |
| [0004](0004-alpha-scope.md) | Alpha-Umfang und Import-Lebenszyklus | Angenommen |
| [0005](0005-manual-append-button.md) | Manueller Kopieren-Knopf zum Ergänzen neuer Artikel | Angenommen |
| [0006](0006-project-rename-and-domain.md) | Marken- und technische Domain-Umbenennung | Angenommen |

## Noch offene Architekturfragen

Diese Punkte sind noch nicht entschieden und müssen vor der jeweiligen Implementierung konkretisiert werden:

- Wie werden Artikel aus der Quellliste mit dem Produktkatalog abgeglichen, und wie werden mehrdeutige bzw. unbekannte Namen behandelt?
- Welche Datenstruktur und Verwaltungsoberfläche verwenden wir für Produktkatalog und Kategorien?
- Erweiterte Import-/Merge-Regeln über das manuelle Ergänzen gemäß ADR 0005 hinaus.
- Welche Synchronisierungsregeln gelten später für Hinzufügen, Abhaken, Löschen und Konflikte zwischen Alexa und Einkaufszettel?
- Wird eine eigene Lovelace-Karte oder ein Custom Panel gebaut, und wann?
- Welche weiteren To-do-Funktionen sollen nach der Alpha ergänzt werden? Den Alpha-Umfang beschreibt ADR 0004.
- Welche Alexa-Listenintegration ist installiert, und stellt sie die Liste sowie Änderungen tatsächlich als HA-`todo`-Entität bereit?
