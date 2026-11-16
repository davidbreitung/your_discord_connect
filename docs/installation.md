# Installation und Discord-Einrichtung

## Voraussetzungen

- Home Assistant ab **2026.10.4** (OS oder Container) und Zugriff auf dessen
  Konfigurationsverzeichnis, häufig `/config`.
- Discord-Konto mit **Server verwalten** beziehungsweise Berechtigung zum Einladen
  eines Bots auf den Zielserver.
- Ausgehender HTTPS-Zugriff auf `discord.com`, Port 443. Keine eingehenden Ports,
  Webhooks oder öffentliche Home-Assistant-Adresse erforderlich.

## 1. Integration installieren

### Manuell

1. Dieses Repository herunterladen.
2. `custom_components/your_discord_connect` vollständig einschließlich
   `translations` in das Home-Assistant-Konfigurationsverzeichnis kopieren.
3. Danach muss `/config/custom_components/your_discord_connect/manifest.json`
   existieren. Bei anderem Konfigurationspfad `/config` entsprechend ersetzen.
4. Home Assistant vollständig neu starten. YAML-Neuladen reicht bei der ersten
   Installation nicht aus. Keine YAML-Konfiguration für diese Integration nötig.

### HACS

Das Projekt ist nicht im standardmäßigen HACS-Katalog enthalten.

1. In HACS **Benutzerdefinierte Repositories** öffnen.
2. `https://github.com/davidbreitung/your_discord_connect` mit Kategorie
   **Integration** hinzufügen.
3. **Your Discord Connect** herunterladen und Home Assistant neu starten.

Hierfür müssen die Dateien bereits auf GitHub veröffentlicht sein. Lokale Änderungen
sind noch nicht über HACS verfügbar; die reale HACS-Installation ist separat zu prüfen.

## 2. Bot erstellen

1. [Discord Developer Portal](https://discord.com/developers/applications) öffnen.
2. Über **New Application** eine Anwendung erstellen, z. B. „Home Assistant“.
3. Unter **Bot** den zugehörigen Bot öffnen beziehungsweise anlegen, falls Discord
   ihn nicht automatisch erstellt hat.
4. Unter **Privileged Gateway Intents** den **Server Members Intent** aktivieren
   und speichern. Dieser ist auch für die REST-Mitgliederliste erforderlich,
   obwohl keine Gateway-Verbindung verwendet wird.
5. **Presence Intent** und **Message Content Intent** werden nicht benötigt.
6. Unter **Bot → Reset Token** ein Bot-Token erzeugen und sicher aufbewahren.
   Dieses später direkt in Home Assistant eingeben. Application ID, Public Key,
   OAuth Client Secret und persönliche Benutzer-Tokens sind nicht geeignet.

Bei größeren/verifizierten Bots können privilegierte Intents eine Genehmigung
von Discord erfordern. Die Integration umgeht diese Vorgaben nicht.

## 3. Bot einladen

1. Unter **OAuth2 → URL Generator** den Scope **bot** auswählen.
2. Keine zusätzlichen Bot-Berechtigungen auswählen; insbesondere keine
   **Administratorrechte** vergeben. Die Mitgliederliste benötigt nur den Members
   Intent und die Servermitgliedschaft, keine Nachrichten- oder Moderationsrechte.
3. Den erzeugten Link öffnen, Zielserver auswählen und zustimmen. Der Bot muss
   auf dem Server installiert werden, nicht nur für einen Benutzer.
4. Prüfen, dass der Bot in der Discord-Mitgliederliste erscheint.

Der Bot kann als **offline** erscheinen. Das ist normal: Die Integration verwendet
HTTPS-Abfragen, keine dauerhafte Gateway-Verbindung mit Online-Status.

## 4. Home Assistant verbinden

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
2. **Your Discord Connect** suchen und Bot-Token eingeben.
3. Server aus der automatisch geladenen Liste wählen. Bei gleichnamigen Servern
   hilft die zusätzlich angezeigte Server-ID.
4. Der gesamte Mitgliederzugriff wird geprüft. Nur bei Erfolg entsteht der Eintrag.
5. Die Mitglieder erscheinen als Geräte mit jeweils einem **Anzeigename**-Sensor.
   Auch der Bot selbst zählt als Mitglied.

Große Server werden in Seiten mit bis zu 1000 Mitgliedern geladen; der erste und
weitere Abgleiche können entsprechend länger dauern.

## 5. Intervall ändern

Am Integrationseintrag **Konfigurieren** wählen und eine ganze Zahl zwischen
**1 und 1440 Minuten** eingeben. Standard: **15 Minuten**. Speichern lädt den
Eintrag neu und synchronisiert sofort. Für große Server und mehrere Einträge
ein ausreichend langes Intervall wählen, um Ratenbegrenzungen zu vermeiden.

## Fehlerbehebung

| Verhalten | Abhilfe |
| --- | --- |
| Integration fehlt | Ordnerstruktur und HA-Version prüfen, vollständig neu starten und Protokoll auf Ladefehler prüfen. |
| Ungültiges Token | Bot-Token verwenden; nach Reset ist das bisherige Token ungültig. Neues Token in der erneuten Anmeldung eingeben. |
| Keine Server | Bot mit Scope `bot` einladen, dann Token-Formular erneut absenden. Token und eingeladener Bot müssen zur selben Anwendung gehören. |
| Zugriff verweigert | Members Intent aktivieren und speichern, Bot-Mitgliedschaft und gegebenenfalls Discord-Genehmigung prüfen. |
| Server nicht erreichbar | Prüfen, ob Bot entfernt wurde; wieder einladen oder nicht benötigten Integrationseintrag entfernen. |
| Verbindung fehlgeschlagen | DNS, Internet und HTTPS-Zugriff auf `discord.com` prüfen; Discord könnte vorübergehend ausgefallen sein. |
| Ratenbegrenzung | Warten; im Betrieb wird beim nächsten Intervall erneut versucht. Bei Bedarf Intervall erhöhen. |
| Sensoren nicht verfügbar | Letzter Abgleich fehlgeschlagen. Geräte bleiben erhalten. Eventuelle Aufforderung zur erneuten Anmeldung abschließen. |
| Mitglied fehlt noch | Nächstes Intervall abwarten oder Integrationseintrag neu laden. Kein Echtzeitabgleich. |
| Alter Gerätename | Eigene HA-Gerätenamen bleiben erhalten. Der Anzeigenamen-Sensor enthält den aktuellen Discord-Namen. |

## Aktualisieren und entfernen

Vor Updates ein Backup anlegen. Updates über HACS laden oder Integrationsordner
ersetzen, anschließend Home Assistant neu starten.

Zum Entfernen zuerst den Servereintrag in **Geräte & Dienste** löschen. Home
Assistant entfernt die zugehörigen Geräte und Entitäten. Danach gegebenenfalls
Integration über HACS entfernen oder Ordner löschen und neu starten. Einen nicht
mehr benötigten Bot optional aus Discord entfernen und dessen Token zurücksetzen.
