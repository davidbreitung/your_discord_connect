# Installation und Discord-Einrichtung

## Voraussetzungen

- Home Assistant ab **2026.10.4** (OS oder Container) und Zugriff auf dessen
  Konfigurationsverzeichnis, häufig `/config`.
- Discord-Konto mit **Server verwalten** beziehungsweise Berechtigung zum Einladen
  eines Bots auf den Zielserver.
- Ausgehender HTTPS-Zugriff auf `discord.com` und WSS-Zugriff auf
  `gateway.discord.gg` sowie die von Discord gelieferten Gateway-/Resume-Adressen
  (gegebenenfalls `*.discord.gg`), jeweils Port 443. Keine eingehenden Ports,
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
4. Unter **Privileged Gateway Intents** den **Server Members Intent** und
   **Presence Intent** aktivieren und speichern. Beide werden benötigt.
5. **Message Content Intent** wird nur für die optionale Text-Feed-Karte benötigt
   (siehe [Dashboard-Anleitung](dashboard.md)); für Mitglieder und TTS nicht.
6. Unter **Bot → Reset Token** ein Bot-Token erzeugen und sicher aufbewahren.
   Dieses später direkt in Home Assistant eingeben. Application ID, Public Key,
   OAuth Client Secret und persönliche Benutzer-Tokens sind nicht geeignet.

Bei größeren/verifizierten Bots können privilegierte Intents eine Genehmigung
von Discord erfordern. Die Integration umgeht diese Vorgaben nicht.

## 3. Bot einladen

1. Unter **OAuth2 → URL Generator** den Scope **bot** auswählen.
2. **View Channels / Kanäle ansehen** für die gewünschten Sprachkanäle erlauben
   (auch kanalbezogene Überschreibungen prüfen). Keine **Administratorrechte**,
   Nachrichten- oder Moderationsrechte vergeben. Für Bot-Kanalauswahl und TTS
   zusätzlich **Connect / Verbinden** und **Speak / Sprechen** erlauben. Für die
   reine Mitgliederanzeige werden diese beiden Rechte nicht benötigt.
3. Den erzeugten Link öffnen, Zielserver auswählen und zustimmen. Der Bot muss
   auf dem Server installiert werden, nicht nur für einen Benutzer.
4. Prüfen, dass der Bot in der Discord-Mitgliederliste erscheint.

Ab Version 0.2.0 hält die Integration eine Gateway-Verbindung. Der Bot kann dadurch
als online erscheinen. Sein Online-Status allein belegt keinen erfolgreichen Abgleich.

## 4. Home Assistant verbinden

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen** öffnen.
2. **Your Discord Connect** suchen und Bot-Token eingeben.
3. Server aus der automatisch geladenen Liste wählen. Bei gleichnamigen Servern
   hilft die zusätzlich angezeigte Server-ID.
4. Der REST-Mitgliederzugriff wird geprüft. Beim Laden des Eintrags wird zusätzlich
   die Gateway-Verbindung aufgebaut. Fehlende Intents dort aktivieren und den
   Integrationseintrag anschließend neu laden.
5. Unter **zentrale Konfiguration** erscheinen Sync-Knopf und Zähler. In der Gruppe
   **Benutzer** erhält jedes Mitglied dreizehn Entitäten für Namen, Presence, Sprachkanal,
   Mute, AFK und Beobachtungszeitpunkte (siehe README).
   Auch der Bot selbst zählt als Mitglied.

Große Server werden in Seiten mit bis zu 1000 Mitgliedern geladen; der erste und
weitere Abgleiche können entsprechend länger dauern. Presence-Abfragen erfolgen
in Gruppen von höchstens 100 Benutzer-IDs über das Gateway.

## 5. Intervall ändern

Am Integrationseintrag **Konfigurieren** wählen und eine ganze Zahl zwischen
**1 und 1440 Minuten** eingeben. Standard: **30 Minuten**. Speichern lädt den
Eintrag neu und synchronisiert sofort. Für große Server und mehrere Einträge
ein ausreichend langes Intervall wählen, um Ratenbegrenzungen zu vermeiden.

## 6. Manuell synchronisieren

Im Gerät **zentrale Konfiguration** den Knopf **Benutzer jetzt synchronisieren** drücken.
Er aktualisiert Mitglieder, Namen, Status und Zähler gemeinsam. Presence-, Sprach-,
Mute- und AFK-Änderungen erscheinen zusätzlich sofort per Gateway-Ereignis.
Alternativ `button.press` mit dieser Entität in einer Automation verwenden. Schnelle
Mehrfachaufrufe werden durch Home Assistants Coordinator zusammengefasst.

Discord unterscheidet für Bots unsichtbare Benutzer nicht von Offline-Benutzern.
Ohne Sprachkanal zeigt der Binärsensor aus und der Kanalsensor unbekannt. Bei einem
fehlenden Gateway-Mitglied sind Presence und Sprachdaten unbekannt. Bei einem
Verbindungsfehler werden Mitgliederentitäten nicht verfügbar; keine Geräte werden gelöscht.

## Fehlerbehebung

| Verhalten | Abhilfe |
| --- | --- |
| Integration fehlt | Ordnerstruktur und HA-Version prüfen, vollständig neu starten und Protokoll auf Ladefehler prüfen. |
| Ungültiges Token | Bot-Token verwenden; nach Reset ist das bisherige Token ungültig. Neues Token in der erneuten Anmeldung eingeben. |
| Keine Server | Bot mit Scope `bot` einladen, dann Token-Formular erneut absenden. Token und eingeladener Bot müssen zur selben Anwendung gehören. |
| Zugriff verweigert | Members Intent und Presence Intent aktivieren und speichern; anschließend Integration neu laden, Bot-Mitgliedschaft und gegebenenfalls Discord-Genehmigung prüfen. |
| Server nicht erreichbar | Prüfen, ob Bot entfernt wurde; wieder einladen oder nicht benötigten Integrationseintrag entfernen. |
| Verbindung fehlgeschlagen | DNS, Internet und HTTPS-Zugriff auf `discord.com` und WSS auf Discord-Gateway-Adressen prüfen; Discord könnte vorübergehend ausgefallen sein. |
| Ratenbegrenzung | Warten; im Betrieb wird beim nächsten Intervall erneut versucht. Bei Bedarf Intervall erhöhen. |
| Sensoren nicht verfügbar | Letzter Abgleich fehlgeschlagen. Geräte bleiben erhalten. Eventuelle Aufforderung zur erneuten Anmeldung abschließen. |
| Mitglied fehlt noch | Nächstes Intervall abwarten oder Integrationseintrag neu laden. Neue Mitglieder werden beim vollständigen Abgleich entdeckt; bestehende Statusentitäten aktualisieren sich sofort per Gateway. |
| Alter Gerätename | Eigene HA-Gerätenamen bleiben erhalten. Der Anzeigenamen-Sensor enthält den aktuellen Discord-Namen. |

## Bot-Kanalauswahl und TTS ab 0.4.0

Das Gerät **Bot: <Name>** wird automatisch in **zentrale Konfiguration** angelegt.
Der eigene Bot wird bei eindeutiger ID aus **Benutzer** entfernt. Andere Bots und
Serverzähler bleiben enthalten. Das Dropdown führt „alle verlassen“ zuerst auf;
anschließend Sprach-/Stage-Kanäle mit IDs. Kanaländerungen werden per Gateway und
bei jedem Vollabgleich synchronisiert.

Für TTS einen HA-TTS-Anbieter konfigurieren, FFmpeg bereitstellen und dem Bot
Verbinden/Sprechen erlauben. Discord-Voice benötigt ausgehendes UDP; die bisherige
HTTPS/WSS-Freigabe alleine genügt nicht. Siehe [Voice-/TTS-Anleitung](voice.md).
Nach dem Update Home Assistant neu starten. Es wird nicht automatisch einem Kanal
beigetreten. Die bisherigen eigenen Bot-Mitgliederentitäten werden durch das neue
Bot-Gerät ersetzt; darauf verweisende Automationen gegebenenfalls anpassen.

## Update von älteren Versionen auf mindestens 0.3.0

Integration aktualisieren und Home Assistant neu starten. Die Gruppen, das zentrale
Gerät, Zähler und zusätzlichen Mitgliederentitäten werden automatisch angelegt.
Bestehende Geräte- und Entitäts-IDs sowie eigene Gerätenamen bleiben erhalten.
Den Integrationseintrag nicht löschen. Ohne eigene Intervalloption gilt jetzt ein
Standard von **30 Minuten**; ein explizit gespeichertes Intervall wird nicht verändert.
Die Reihenfolge der beiden Gruppen bestimmt die Home-Assistant-Oberfläche.

## Zusätzliche Voraussetzung beim Update von 0.1.0

Vor dem Update **Presence Intent** im Developer Portal aktivieren und die Sichtbarkeit
relevanter Sprachkanäle für den Bot prüfen. Danach aktualisieren und Home Assistant
neu starten. Geräte und Anzeigenamen-Sensoren behalten ihre IDs; weitere Entitäten
und der Synchronisationsknopf werden automatisch hinzugefügt. Den Servereintrag
nicht löschen und neu anlegen.

## Aktualisieren und entfernen

Vor Updates ein Backup anlegen. Updates über HACS laden oder Integrationsordner
ersetzen, anschließend Home Assistant neu starten.

Zum Entfernen zuerst den Servereintrag in **Geräte & Dienste** löschen. Home
Assistant entfernt die zugehörigen Geräte und Entitäten. Danach gegebenenfalls
Integration über HACS entfernen oder Ordner löschen und neu starten. Einen nicht
mehr benötigten Bot optional aus Discord entfernen und dessen Token zurücksetzen.

### Startfehler: `Requirements ... not found`

Bei der bisherigen Anforderung `discord.py[voice]==2.7.1` besteht ein
Versionskonflikt: Das Voice-Extra fordert PyNaCl < 1.6, Home Assistant
2026.10.4 und 2026.11.1 schreiben jedoch PyNaCl 1.6.2 vor. Die korrigierte
`manifest.json` deklariert Discord, PyNaCl und DAVE getrennt.

Die korrigierten Integrationsdateien installieren und Home Assistant vollständig
neu starten. Der vorhandene Integrationseintrag und das Bot-Token können bleiben.
Keine Home-Assistant-Systempakete manuell herabstufen oder Paketvorgaben entfernen.

Falls die Installation weiterhin fehlschlägt, in **Einstellungen → System →
Protokolle** den vorherigen Eintrag von `homeassistant.util.package` mit
`Unable to install package` prüfen. Er enthält den konkreten Paket-, Download-
oder Plattformfehler; die Meldung von `homeassistant.setup` allein genügt nicht.

## Dashboard-Karten und Direktnachrichten ab 1.0.0

Nach dem Update Home Assistant neu starten. Die beiden DM-Bedienelemente werden
auf vorhandenen Benutzergeräten automatisch angelegt; Geräte-IDs bleiben bestehen.
Für die Karten einmalig die JavaScript-Ressource registrieren und anschließend
die Karten über den visuellen Editor hinzufügen. Siehe [Dashboard-Anleitung](dashboard.md).
