# Your Discord Connect

Eine eigenständige **Custom Integration für Home Assistant**, die Mitglieder eines
Discord-Servers als virtuelle Geräte abbildet. Kein separater Bot-Prozess und kein
Home-Assistant-Add-on erforderlich.

**Stand: 1.0.0.** Unterstützte Testbasis: Home Assistant
**2026.10.4** mit Python **3.14.2 oder neuer**. Ältere Home-Assistant-Versionen sind
derzeit nicht unterstützt. Automatisierte Tests simulieren Discord-Antworten;
ein Test mit einem echten Discord-Server steht noch aus.

## Funktionen

- Einrichtung über die Home-Assistant-Oberfläche: Bot-Token eingeben, Server aus
  einer automatisch ermittelten Liste auswählen, Mitgliederzugriff prüfen lassen.
- Zentrale Konfiguration mit Synchronisationsknopf und drei Serverzählern.
- Mitgliedergeräte in der Gruppe **Benutzer**, mit dreizehn Entitäten pro Mitglied.
- Anzeigename: Server-Spitzname → globaler Discord-Anzeigename → Benutzername.
- Abgleich beim Start und alle **30 Minuten**; zentral pro Server auf ganze
  **1 bis 1440 Minuten** einstellbar.
- Neue Mitglieder werden angelegt, Namen aktualisiert, ausgetretene Mitglieder
  einschließlich ihrer Entitäten aus den Home-Assistant-Registern entfernt.
- Stabile Server- und Benutzer-IDs verhindern Duplikate bei Namensänderungen.
- Der eigene Bot hat ein zentrales Gerät mit Kanalauswahl und TTS-Durchsagen;
  andere Bots bleiben als Benutzer sichtbar. Mehrere Server sind als separate Einträge möglich;
  derselbe Server kann nur einmal eingerichtet werden.
- Deutsche und englische Oberfläche; erneute Anmeldung bei ungültigem Token.

Die Karten **Discord-Channel-Overview** und **Discord-Text-Channel-Feed** zeigen
Sprachkanalbelegung und Textkanal-Nachrichten in Discord-naher Optik.
[Einrichtung und Bedienung der Karten](docs/dashboard.md).

Private Textnachrichten können am Benutzergerät, über eine Aktion oder aus anderen Integrationen
gesendet werden. TTS-Durchsagen sind über das Bot-Gerät möglich. Rollen, beliebige
Audiostreams und Video sind noch nicht enthalten.
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

## Gerätegruppen und zentrale Konfiguration

Jeder Server hat zwei Home-Assistant-Untergruppen (Config Subentries):

- **zentrale Konfiguration:** ein gleichnamiges Gerät mit **Benutzer jetzt synchronisieren**,
  **Alle Mitglieder**, **Online-Benutzer** und **Benutzer in Channels** sowie ein
  zusätzliches **Bot-Gerät** mit Sprachkanal-Dropdown, **TTS-Nachricht**, **TTS ausführen**, **Wiedergabestatus** und **Lautstärke**.
- **Benutzer:** alle Mitgliedsgeräte außer dem eindeutig erkannten eigenen Bot, mit Modell/Typ **Benutzer**. Jedes Mitgliedsgerät
  ist über `via_device_id` mit dem zentralen Gerät verknüpft.

Die zentrale Gruppe wird zuerst angelegt. Die Integration kann die Sortierung der
Home-Assistant-Oberfläche jedoch nicht erzwingen; dort kann „Benutzer“ alphabetisch
zuerst erscheinen. Die Gruppen sind keine zusätzlichen Discord-Server.

Alle Zähler schließen Bots ein. Online bedeutet hier **Presence online/idle/dnd ODER
Sprachkanalverbindung**. Der Presence-Sensor selbst bleibt unverändert: Unsichtbar
wird weiterhin als offline angezeigt. Der Channel-Zähler zählt Mitglieder in Sprach-
und Stage-Kanälen, nicht Textkanalzugriffe. Wenn fehlende Zustände einen exakten Zähler
verhindern, zeigt dieser unbekannt statt einer irreführenden Teilanzahl.

## Entitäten pro Benutzer

| Entität | Bedeutung |
| --- | --- |
| Anzeigename | Server-Spitzname, globaler Anzeigename oder Benutzername. |
| Benutzername | Eigentlicher Discord-Benutzername (`user.username`), unabhängig vom Spitznamen. |
| Presence-Status | `online`, `idle`, `dnd` oder `offline`; in der Oberfläche übersetzt. Unsichtbar erscheint als offline. |
| Im Sprachkanal | Binärsensor: an bei Verbindung mit einem Sprach- oder Stage-Kanal, sonst aus. |
| Sprachkanal | Name des aktuellen Kanals; ohne Kanal ist der Sensor unbekannt. |
| Lautsprecher stumm | Discord-Deafen: selbst deaktiviert oder serverseitig deaktiviert; kein Hardwarezustand. |
| Mikrofon stumm | Selbst-Mute oder serverseitiges Mute. Stage-Unterdrückung ist kein Mute-Schalter. |
| Im AFK-Kanal | Mitglied befindet sich im konfigurierten AFK-Sprachkanal des Servers; nicht bloß in einem Kanal namens „AFK“. |
| Zuletzt anwesend erkannt | Letzte beobachtete erste Anwesenheit oder Wechsel zu anwesend (Presence sichtbar oder Sprachverbindung). |
| Zuletzt nicht anwesend erkannt | Letzte beobachtete erste Abwesenheit oder Wechsel zu offline ohne Sprachverbindung. |
| Letztes Gateway-Ereignis | Lokaler Empfangszeitpunkt des letzten Presence-/Sprachstatusereignisses für dieses Mitglied. |

## Sofortige Aktualisierung und manueller Abgleich

Presence, Sprachkanal, Mute und AFK werden direkt aus Gateway-Ereignissen übernommen.
Auch die Zähler und Beobachtungszeitpunkte aktualisieren sich dabei sofort. Für
Automationen die normalen Home-Assistant-Zustandstrigger auf diesen Entitäten nutzen.
Discord garantiert keine maximale Übertragungszeit; kein Intervall muss abgewartet werden.

Unter **Einstellungen → Geräte & Dienste → Your Discord Connect → zentrale Konfiguration**
den Knopf **Benutzer jetzt synchronisieren** drücken. Er ist auch über `button.press`
in Automationen nutzbar und bleibt nach Fehlern bedienbar. Bestehende Button-Entitäts-IDs
bleiben erhalten, auch wenn ihr bisheriger Name noch den Servernamen enthält.

Der vollständige Abgleich entdeckt/entfernt Mitglieder und prüft alle Zustände: beim
Start, manuell und standardmäßig alle **30 Minuten**. Eigene gespeicherte Intervalle
bleiben erhalten. Häufige Gateway-Ereignisse verschieben diesen Abgleich nicht.
Neue Mitgliedsgeräte erscheinen mit dem nächsten vollständigen Abgleich.

Ohne Sprachverbindung sind Sprach-, Mute- und AFK-Binärsensoren aus; der Kanalname ist
unbekannt. Fehlende Gateway-Mitglieder ergeben unbekannte Statuswerte. Beim
Gateway-Ausfall sind Mitgliederentitäten und Zähler nicht verfügbar; Geräte bleiben
erhalten. Nach Wiederverbindung wird ein vollständiger Abgleich angefordert.

### Bedeutung der Zeitstempel

Es werden **Beobachtungen**, keine tatsächlichen Discord-An- oder Abmeldezeiten
festgehalten. Erste bekannte Zustände erhalten den Zeitpunkt ihrer Beobachtung;
wiederholte gleiche Zustände überschreiben die An-/Abwesenheitszeitpunkte nicht.
Ein unsichtbares Mitglied im Sprachkanal gilt als anwesend. Erst offline **und** ohne
Sprachverbindung gilt als nicht anwesend. Bot-Verbindungsabbrüche zählen nie als Abwesenheit.

„Letztes Gateway-Ereignis“ wird weder durch Polling noch durch Heartbeats verändert.
Ein alter Wert kann schlicht bedeuten, dass sich beim Benutzer nichts geändert hat.
Vor dem ersten empfangenen Benutzerereignis ist er unbekannt. Zeitstempel werden in
UTC gespeichert und von Home Assistant in der lokalen Zeitzone angezeigt.

Die Zeitstempel bleiben über Neustarts erhalten. Während Ausfällen verpasste Übergänge
können nicht nachträglich rekonstruiert werden. Speicherung erfolgt gebündelt nach fünf
Sekunden und beim geordneten Stoppen; ein harter Prozessabbruch kann die letzten noch
nicht gespeicherten Ereignisse verlieren. Bei bestätigtem Serveraustritt oder Entfernen
der Integration werden die zugehörigen gespeicherten Beobachtungen entfernt.

**Update von 0.1.0:** Im Developer Portal zusätzlich **Presence Intent** aktivieren,
Integration aktualisieren und Home Assistant neu starten. Bestehende Geräte und
Anzeigenamen-Sensoren behalten ihre IDs; die neuen Entitäten werden automatisch ergänzt.
Der Bot benötigt Zugriff auf die gewünschten Sprachkanäle. Ein Beitritt erfolgt
erst nach Kanalauswahl; TTS-Audio erst nach Drücken des Ausführungsbuttons.

## Bot-Kanalauswahl und TTS

Im zentralen **Bot-Gerät** einen Sprach- oder Stage-Kanal auswählen, das Feld
**TTS-Nachricht** befüllen und **TTS ausführen** drücken. Die Spracherzeugung nutzt
Home Assistants Standard-TTS-Anbieter. **alle verlassen** ist der erste Dropdown-
Eintrag und beendet die Sprachverbindung. Die Liste aktualisiert sich bei jedem
Vollabgleich und zusätzlich bei Kanaländerungen per Gateway.

Benötigt werden ein HA-TTS-Anbieter, FFmpeg mit Opus-Unterstützung sowie Discords
Rechte **Verbinden** und **Sprechen**. Für Voice ist außerdem ausgehendes UDP nötig.
Die [vollständige Voice-/TTS-Anleitung](docs/voice.md) beschreibt Stage-Freigaben,
Queue, Abbruch, Namensänderungen, Automationsbeispiele und Grenzen.

## Private Nachrichten aus anderen Integrationen

Mit `your_discord_connect.send_direct_message` eine private Textnachricht an ein
vorhandenes Benutzergerät senden. Andere Integrationen können dieselbe Aktion oder
`async_send_direct_message(hass, device_id, content)` nutzen; sie benötigen kein Bot-Token.
Das zentrale Gerät ist kein Empfänger. Bis zu 2000 Zeichen pro Nachricht sind möglich.
Discord kann DMs aufgrund der Empfängereinstellungen ablehnen. Nachrichten werden nur
auf ausdrücklichen Aufruf gesendet, niemals automatisch bei der Synchronisation.

Die [Schnittstellendokumentation](docs/api.md) enthält YAML-/Python-Beispiele,
Rückgabewerte, Empfängerauswahl und Fehlerbehandlung.

## Datenschutz

Die Integration liest Discord-Daten per HTTPS und Gateway-WebSocket. Private
Textnachrichten werden ausschließlich nach Aufruf der Versandaktion gesendet. Benutzer-IDs, Namen, Presence und Sprachkanalbelegung werden in Home
Assistant verarbeitet. Beobachtungszeitpunkte werden zusätzlich lokal gespeichert; Sensorwerte
können durch den Recorder historisiert werden. Bei Bedarf die Entitäten in der
[Recorder-Konfiguration](https://www.home-assistant.io/integrations/recorder/) ausschließen.

Das Bot-Token wird in der lokalen Home-Assistant-Konfiguration gespeichert.
Backups schützen und Tokens niemals in Git, Screenshots, Issues oder Chats teilen.
Administratorrechte und Message Content Intent sind nicht nötig.

## Hilfe und Entwicklung

- [Installation und Fehlerbehebung](docs/installation.md)
- [Entwicklung, Architektur und Tests](docs/development.md)
- [Schnittstelle für private Nachrichten](docs/api.md)
- [Bot-Kanalauswahl und TTS-Durchsagen](docs/voice.md)
- [Änderungsverlauf](CHANGELOG.md)
- [Fehler melden](https://github.com/davidbreitung/your_discord_connect/issues)

Bei Fehlerberichten Versionsnummern und beobachtetes Verhalten angeben, jedoch
keine Tokens oder personenbezogenen Mitgliederdaten. Dokumentation und Tests
werden bei Funktionsänderungen mitgepflegt.
