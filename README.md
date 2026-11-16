# Your Discord Connect

Eine eigenständige **Custom Integration für Home Assistant**, die Mitglieder eines
Discord-Servers als virtuelle Geräte abbildet. Kein separater Bot-Prozess und kein
Home-Assistant-Add-on erforderlich.

**Stand: 0.1.0 – erste Entwicklungsversion.** Unterstützte Testbasis: Home Assistant
**2026.10.4** mit Python **3.14.2 oder neuer**. Ältere Home-Assistant-Versionen sind
derzeit nicht unterstützt. Automatisierte Tests simulieren Discord-Antworten;
ein Test mit einem echten Discord-Server steht noch aus.

## Funktionen

- Einrichtung über die Home-Assistant-Oberfläche: Bot-Token eingeben, Server aus
  einer automatisch ermittelten Liste auswählen, Mitgliederzugriff prüfen lassen.
- Pro Mitglied ein virtuelles Gerät mit einem Sensor **Anzeigename**.
- Anzeigename: Server-Spitzname → globaler Discord-Anzeigename → Benutzername.
- Abgleich beim Start und alle **15 Minuten**; zentral pro Server auf ganze
  **1 bis 1440 Minuten** einstellbar.
- Neue Mitglieder werden angelegt, Namen aktualisiert, ausgetretene Mitglieder
  einschließlich ihrer Entitäten aus den Home-Assistant-Registern entfernt.
- Stabile Server- und Benutzer-IDs verhindern Duplikate bei Namensänderungen.
- Bots sind eingeschlossen. Mehrere Server sind als separate Einträge möglich;
  derselbe Server kann nur einmal eingerichtet werden.
- Deutsche und englische Oberfläche; erneute Anmeldung bei ungültigem Token.

Nachrichten, Rollen, Präsenzdaten und Sprachkanalzustände sind noch nicht enthalten.
Weitere Attribute können auf den bestehenden Geräte-IDs aufbauen.

## Installation

Die [vollständige Anleitung](docs/installation.md) erklärt Installation,
Bot-Erstellung, Berechtigungen, Einrichtung und Fehlerbehebung.

1. Integration manuell oder als benutzerdefiniertes HACS-Repository installieren.
2. Discord-Bot erstellen, **Server Members Intent** aktivieren und Bot einladen.
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

## Datenschutz

Die Integration liest Discord-Daten per HTTPS und sendet keine Nachrichten.
Benutzer-IDs und Anzeigenamen werden in Home Assistant verarbeitet; Sensorwerte
können durch den Recorder historisiert werden. Bei Bedarf die Entitäten in der
[Recorder-Konfiguration](https://www.home-assistant.io/integrations/recorder/) ausschließen.

Das Bot-Token wird in der lokalen Home-Assistant-Konfiguration gespeichert.
Backups schützen und Tokens niemals in Git, Screenshots, Issues oder Chats teilen.
Administratorrechte, Message Content Intent und Presence Intent sind nicht nötig.

## Hilfe und Entwicklung

- [Installation und Fehlerbehebung](docs/installation.md)
- [Entwicklung, Architektur und Tests](docs/development.md)
- [Änderungsverlauf](CHANGELOG.md)
- [Fehler melden](https://github.com/davidbreitung/your_discord_connect/issues)

Bei Fehlerberichten Versionsnummern und beobachtetes Verhalten angeben, jedoch
keine Tokens oder personenbezogenen Mitgliederdaten. Dokumentation und Tests
werden bei Funktionsänderungen mitgepflegt.
