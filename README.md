# Your Discord Connect

Eine eigenständige **Custom Integration für Home Assistant**, die Mitglieder eines
Discord-Servers als virtuelle Geräte abbildet. Kein separater Bot-Prozess und kein
Home-Assistant-Add-on erforderlich.

**Stand: 0.2.0 – Entwicklungsversion.** Unterstützte Testbasis: Home Assistant
**2026.10.4** mit Python **3.14.2 oder neuer**. Ältere Home-Assistant-Versionen sind
derzeit nicht unterstützt. Automatisierte Tests simulieren Discord-Antworten;
ein Test mit einem echten Discord-Server steht noch aus.

## Funktionen

- Einrichtung über die Home-Assistant-Oberfläche: Bot-Token eingeben, Server aus
  einer automatisch ermittelten Liste auswählen, Mitgliederzugriff prüfen lassen.
- Pro Mitglied ein virtuelles Gerät mit fünf Entitäten: **Anzeigename**,
  **Benutzername**, **Presence-Status**, **Im Sprachkanal** und **Sprachkanal**.
- Anzeigename: Server-Spitzname → globaler Discord-Anzeigename → Benutzername.
- Abgleich beim Start und alle **15 Minuten**; zentral pro Server auf ganze
  **1 bis 1440 Minuten** einstellbar.
- Neue Mitglieder werden angelegt, Namen aktualisiert, ausgetretene Mitglieder
  einschließlich ihrer Entitäten aus den Home-Assistant-Registern entfernt.
- Stabile Server- und Benutzer-IDs verhindern Duplikate bei Namensänderungen.
- Bots sind eingeschlossen. Mehrere Server sind als separate Einträge möglich;
  derselbe Server kann nur einmal eingerichtet werden.
- Deutsche und englische Oberfläche; erneute Anmeldung bei ungültigem Token.

Nachrichten und Rollen sind noch nicht enthalten.
Weitere Attribute können auf den bestehenden Geräte-IDs aufbauen.

## Installation

Die [vollständige Anleitung](docs/installation.md) erklärt Installation,
Bot-Erstellung, Berechtigungen, Einrichtung und Fehlerbehebung.

1. Integration manuell oder als benutzerdefiniertes HACS-Repository installieren.
2. Discord-Bot erstellen, **Server Members Intent** und **Presence Intent** aktivieren und Bot einladen.
3. Home Assistant neu starten und **Your Discord Connect** hinzufügen.
4. Bot-Token eingeben und Server wählen. Der erste Abgleich erfolgt automatisch.

Discord verlangt Bot-Erstellung und Zustimmung zum Serverbeitritt durch einen
berechtigten Benutzer. Diese Schritte kann die Integration nicht übernehmen.
Danach sind keine manuell gepflegten Mitgliederlisten oder Server-IDs nötig.

## Bedienung

Unter **Einstellungen → Geräte & Dienste → Your Discord Connect → Konfigurieren**
das Intervall ändern. Dies lädt den Servereintrag neu und synchronisiert sofort.
Eigene Home-Assistant-Gerätenamen bleiben erhalten; der Anzeigenamen-Sensor zeigt
weiterhin den aktuellen Discord-Namen.

Bei API-Fehlern bleiben Geräte erhalten; ihre Sensoren sind bis zum nächsten
erfolgreichen Abgleich nicht verfügbar. Nur eine vollständig abgerufene Liste
darf Löschungen auslösen. Der nächste Versuch erfolgt zum nächsten Intervall.
Ein ungültiges Token löst eine Aufforderung zur erneuten Anmeldung aus.

Nach einem Austritt müssen Automationen, die auf entfernte Entitäten verweisen,
gegebenenfalls angepasst werden. Ein Wiedereintritt verwendet dieselbe eindeutige
Discord-ID. Eigene Einstellungen und betroffene Automationen danach prüfen.

## Neue Entitäten und manuelle Synchronisation

| Entität | Bedeutung |
| --- | --- |
| Anzeigename | Server-Spitzname, globaler Anzeigename oder Benutzername. |
| Benutzername | Eigentlicher Discord-Benutzername (`user.username`), unabhängig vom Spitznamen. |
| Presence-Status | `online`, `idle`, `dnd` oder `offline`; in der Oberfläche übersetzt. Unsichtbar erscheint als offline. |
| Im Sprachkanal | Binärsensor: an bei Verbindung mit einem Sprach- oder Stage-Kanal, sonst aus. |
| Sprachkanal | Name des aktuellen Kanals; ohne Kanal ist der Sensor unbekannt. |

Am Integrationseintrag gibt es den Knopf **<Servername> synchronisieren**. Er
aktualisiert alle Mitglieder und ihre fünf Entitäten gemeinsam. Er kann auch mit
Home Assistants Aktion `button.press` in Automationen oder Dashboards genutzt werden.
Der Knopf bleibt nach einem fehlgeschlagenen Abgleich bedienbar.

Die Gateway-Verbindung läuft dauerhaft und hält Sprachkanalzustände aktuell vor.
Die Entitäten werden dennoch nur bei der geplanten oder manuellen Synchronisation
aktualisiert. Presence wird dabei über das Gateway explizit abgefragt. Fehlende
Gateway-Mitglieder ergeben unbekannte Statuswerte, keine erfundenen Offline-Werte.
Scheitert der Abgleich, bleiben Geräte erhalten und Mitgliederentitäten werden
nicht verfügbar. Ohne Sprachverbindung: Binärsensor aus, Kanalname unbekannt.

**Update von 0.1.0:** Im Developer Portal zusätzlich **Presence Intent** aktivieren,
Integration aktualisieren und Home Assistant neu starten. Bestehende Geräte und
Anzeigenamen-Sensoren behalten ihre IDs; die neuen Entitäten werden automatisch ergänzt.
Der Bot benötigt Zugriff auf die gewünschten Sprachkanäle. Es wird weder einem
Sprachkanal beigetreten noch Audio übertragen.

## Datenschutz

Die Integration liest Discord-Daten per HTTPS und Gateway-WebSocket und sendet keine
Nachrichten. Benutzer-IDs, Namen, Presence und Sprachkanalbelegung werden in Home
Assistant verarbeitet; Sensorwerte
können durch den Recorder historisiert werden. Bei Bedarf die Entitäten in der
[Recorder-Konfiguration](https://www.home-assistant.io/integrations/recorder/) ausschließen.

Das Bot-Token wird in der lokalen Home-Assistant-Konfiguration gespeichert.
Backups schützen und Tokens niemals in Git, Screenshots, Issues oder Chats teilen.
Administratorrechte und Message Content Intent sind nicht nötig.

## Hilfe und Entwicklung

- [Installation und Fehlerbehebung](docs/installation.md)
- [Entwicklung, Architektur und Tests](docs/development.md)
- [Änderungsverlauf](CHANGELOG.md)
- [Fehler melden](https://github.com/davidbreitung/your_discord_connect/issues)

Bei Fehlerberichten Versionsnummern und beobachtetes Verhalten angeben, jedoch
keine Tokens oder personenbezogenen Mitgliederdaten. Dokumentation und Tests
werden bei Funktionsänderungen mitgepflegt.
