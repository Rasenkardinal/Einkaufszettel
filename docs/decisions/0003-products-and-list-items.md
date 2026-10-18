# ADR 0003: Produktkatalog und konkrete Listeneinträge trennen

- **Status:** Angenommen
- **Datum:** 2026-10-18

## Kontext

Ein Eintrag wie „Milch“ muss mit einem Produkt und einer Kategorie wie „Molkereiprodukte“ abgeglichen werden. Zusätzliche Angaben wie „3 Flaschen“ gelten typischerweise nur für den aktuellen Einkauf und dürfen nicht dauerhaft auf das Produkt übertragen werden. Mehrere Listeneinträge können dasselbe Produkt betreffen, aber unterschiedliche Mengen oder Notizen haben.

Das HA-To-do-Modell eignet sich zur Darstellung einfacher Einträge und ihres offenen/erledigten Status. Es definiert jedoch keine eigenen Produkt-IDs oder Kategorien.

## Entscheidung

1. Der Produktkatalog und konkrete Einkaufs-Listeneinträge sind getrennte Datensätze.
2. Ein Produkt beschreibt die wiederverwendbare Identität eines Artikels, z. B. `milk`, den Anzeigenamen „Milch“, Kategoriezuordnung und optional Suchbegriffe/Aliase. Produktkatalog und Kategorien werden integrationsverwaltet gespeichert.
3. Ein Einkaufs-Listeneintrag hat eine eigene stabile ID, einen Status und optional eine Produktreferenz. Ein Eintrag ohne passende Produktreferenz bleibt gültig und kann später zugeordnet werden.
4. Temporäre Angaben gehören zum Listeneintrag: Menge, Einheit und Notiz. Beispiel: Produkt „Milch“ in „Molkereiprodukte“ plus Einkaufsposition `quantity: 3`, `unit: Flasche`. Eine lesbare Notiz wie „3x in Flaschen“ kann angezeigt werden; strukturierte Menge/Einheit ist vorzuziehen, sobald sie separat bearbeitet oder verarbeitet werden soll.
5. Der `TodoItem`-Datensatz ist die HA-kompatible Projektion der Einkaufsposition (z. B. Zusammenfassung, Status und gegebenenfalls Beschreibung). Produkt-ID, Kategorie sowie strukturierte Menge/Einheit verbleiben in den integrationsverwalteten Daten und werden über die stabile Eintrags-ID zugeordnet. Kategorien werden nicht in das To-do-Textfeld hineinkodiert.
6. Die Sortierung nach Kategorie und individuelle Kategorie-/Produktverwaltung gehören zur Easy-Shopping-Fachlogik und nicht zur To-do-Grundschnittstelle.

## Folgen

- Eine einzelne Einkaufsposition kann in der eigenen Oberfläche mit Kategorie, Produkt, Menge, Einheit und Notiz angereichert werden, während sie in HA weiter als To-do erscheint und abgehakt werden kann.
- Produktname und Einkaufshinweis sind unterschiedliche Informationen; das Ändern einer Notiz ändert nicht das Produkt.
- Der Produktabgleich muss mehrdeutige Namen berücksichtigen. Automatisches Matching, Aliasregeln, manuelle Zuordnung und die Behandlung nicht zugeordneter Produkte sind noch nicht festgelegt.
- Beim Import einer einfachen Alexa-To-do-Position liegt zunächst nur der Quelltext vor. Menge, Einheit oder Produktkategorie werden nicht verlässlich vorausgesetzt, sofern sie nicht gesondert erkannt oder vom Nutzer ergänzt wurden.
- Eine Änderung der HA-To-do-Zusammenfassung muss mit der Zuordnung zum internen Datensatz konsistent behandelt werden; Details sind bei Implementierung zu definieren.

## Beispiel (konzeptionell)

```yaml
product:
  id: milk
  name: Milch
  category_id: dairy
  aliases: [Vollmilch]

list_item:
  id: 5f3b... # stabile interne ID
  product_id: milk
  status: needs_action
  quantity: 3
  unit: Flasche
  note: null
```
