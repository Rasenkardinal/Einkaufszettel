# ADR 0006: Marken- und technische Domain-Umbenennung

- **Status:** Angenommen
- **Datum:** 2026-10-21

## Kontext

Das Projekt und das öffentliche GitHub-Repository sollen „Einkaufszettel“ heißen. Zusätzlich wurde die technische HA-Integrationsdomain von `easy_shopping` auf `einkaufszettel` geändert.

Home Assistant identifiziert und lädt Integrationen über ihre Domain und den gleichnamigen Ordner unter `custom_components`. Config-Entry-Versionierung migriert Daten innerhalb einer Integration, nicht den Domain-Namespace selbst. Die bisher veröffentlichte Integration und ihre lokale Liste verwenden `easy_shopping`; Entity-IDs und Store-Schlüssel enthalten ebenfalls diesen Namen.

## Entscheidung

1. Neue Installationen verwenden den sichtbaren Namen „Einkaufszettel“, die Domain `einkaufszettel`, die HACS-Integration im Ordner `custom_components/einkaufszettel` und den Store-Namensraum `.storage/einkaufszettel.<entry_id>`.
2. Bestehende `easy_shopping`-Config-Entries werden nicht als HA-Config-Entries umgeschrieben. Nutzer richten die neue Integration separat mit derselben Quell-Entity ein.
3. Beim Einrichten einer neuen Liste sucht Einkaufszettel in HA nach genau einem alten `easy_shopping`-Config-Entry mit derselben Quell-Entity-ID. Falls dessen Store vorhanden und valide ist, werden diese lokalen Listendaten in den neuen Store kopiert, bevor die neue To-do-Entität bereitgestellt wird.
4. Der alte Store wird nicht gelöscht oder verändert. Mehrere passende Legacy-Entries beziehungsweise beschädigte Daten führen zu einem expliziten Setup-Fehler, nicht zu einer stillen Ersatzliste.
5. Der alte Config-Entry muss bestehen bleiben, bis die neue Liste erfolgreich eingerichtet und geprüft wurde. Nach Verifikation wird er vom Nutzer entfernt; Dashboards und Automationen mit alten Entity-IDs werden manuell angepasst.

## Folgen

- Der Projektname und die Integration sind einheitlich „Einkaufszettel“; `easy_shopping` bleibt ausschließlich ein technischer Legacy-Schlüssel zum Auffinden vorhandener Daten.
- Eine neue HA-Config-Entry-ID erzeugt neue Entities, typischerweise `todo.einkaufszettel` und einen neuen Button. Bestehende Entity-IDs werden nicht automatisch übernommen.
- Wenn ein Nutzer den alten Config-Entry vor der Neueinrichtung löscht, steht dessen Entry-ID der Integration nicht mehr zur Zuordnung der alten Store-Datei zur Verfügung. Ein vollständiges HA-Backup oder erneuter Import ist dann erforderlich.
- Die neue Installation darf nicht als nahtloses Domain-Upgrade beworben werden. Die Konfiguration wird neu angelegt und abhängige Dashboard-/Automation-Referenzen sind zu kontrollieren.
