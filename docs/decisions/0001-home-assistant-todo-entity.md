# ADR 0001: Home Assistant und eine native To-do-Entität

- **Status:** Angenommen
- **Datum:** 2026-10-18

## Kontext

Die Liste soll für mehrere Haushaltsmitglieder in deren vorhandener Home-Assistant-Umgebung verfügbar sein. Die Alexa-Einkaufsliste ist bereits mit HA verbunden. HA bietet ein standardisiertes To-do-Modell und eine native Listenverwaltung, deren Einträge auch von Automationen und weiteren Integrationen verwendet werden können.

Eine eigene Smartphone-Oberfläche ist erwünscht, aber der erste Schritt soll die Daten- und Listenintegration klären, ohne sofort eine weitere App zu betreiben.

## Entscheidung

1. Einkaufszettel wird als Home-Assistant-Integration umgesetzt.
2. Beim Einrichten wählt der Nutzer eine vorhandene `todo`-Entität als Quellliste aus. Erwartet wird die in HA verfügbare Alexa-Einkaufsliste.
3. Einkaufszettel stellt eine eigene To-do-Listen-Entität über HA's `TodoListEntity`-Schnittstelle bereit. Sie ist damit in der HA-To-do-Listenverwaltung sichtbar und kann dort grundsätzlich über standardisierte To-do-Funktionen angesprochen werden.
4. Der erste Funktionsumfang ist eine lokale Kopie der offenen Quelllisteneinträge, die in Einkaufszettel abgehakt werden können. Es gibt in dieser Version keinen Rückkanal zur Quellliste und keine laufende Synchronisierung.
5. Die eigene mobile UI bleibt eine spätere, separate Entscheidung. Zunächst verwenden wir die native HA-Listenansicht als Basis; Lovelace-Karte oder Custom Panel sind noch nicht festgelegt.

## Folgen

- Nutzer, Gerätezugriff und HA-Betrieb werden wiederverwendet; eine separate native App und eigene Authentifizierung sind für den Anfang nicht erforderlich.
- HA-To-do-Kompatibilität bietet eine einfache Standardansicht, bildet aber weder Produktkatalog noch Kategorien vollständig ab.
- Die Integration muss prüfen, ob die ausgewählte Quell-Entität tatsächlich verfügbar ist und Einträge über die To-do-Schnittstelle lesen lässt. Die konkrete Alexa-Integration und ihre Fähigkeiten sind vor Implementierung zu verifizieren.
- Ist HA selbst nicht erreichbar, ist die dort gehostete Liste nicht verfügbar. Der Ausfall von Alexa/der Amazon-Cloud soll dagegen die lokal gespeicherte Kopie nicht blockieren.

## Verworfen / nicht gewählt

- Eine separate native App als erster Schritt: zusätzlicher Entwicklungs- und Wartungsaufwand, bevor die fachlichen Daten geklärt sind.
- Die Alexa-Liste als alleinige Datenquelle: sie enthält nicht die benötigten eigenen Produkt- und Kategorieinformationen und wäre bei Cloud-/Integrationsausfall keine lokale Arbeitskopie.
