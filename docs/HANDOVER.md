# Kompakte Übergabe für die nächste Codex-Sitzung

Stand **17.11.2026**. Lies zuerst `AGENTS.md`, dann [STATUS](STATUS.md) und
[TODO](TODO.md); für Änderungen [ARCHITECTURE](ARCHITECTURE.md) und
[DECISIONS](DECISIONS.md). Rechnerwechsel: [WINDOWS](WINDOWS.md).

## Projekt und gesicherter Ausgangspunkt

- Repository: `davidbreitung/your_discord_connect`, Domain `your_discord_connect`.
- Ziel: eigenständige Home-Assistant-Integration für Discord, von Dritten nutzbar,
  fortlaufend dokumentiert. Sprache mit Benutzer: Deutsch.
- Implementierte Version **1.0.1**, letzter Funktionscommit **`f1e59cc`**, nach
  `origin/main` gepusht. Zu Beginn dieser Dokumentationsaufgabe HEAD = origin/main,
  sauberer Checkout. Der Dokumentationscommit selbst folgt darauf; aktuellen
  Hash mit `git log -1` prüfen, nicht den alten Funktionshash blind auschecken.
- Lokaler Cloud-Branch heißt `work` ohne Upstream; tatsächlicher gemeinsamer
  Entwicklungsbranch ist `main`. Windows-Clone normalerweise auf `main`.
- Bisher Cloud-Linux; Benutzer möchte künftig zwischen Windows-Rechnern mit
  Codex Desktop wechseln. Native Windows-Tests sind nicht nachgewiesen; WSL2 für
  HA-Testumgebung vorgesehen. Keine produktiven Dienste in dieser Aufgabe ändern.

## Was umgesetzt wurde

1. Bot-Token/Server über HA-Configflow, regelmäßiger Mitgliederabgleich und stabile
   virtuelle Geräte. Anzeigename und Benutzername getrennt.
2. Presence, Voice-Mitgliedschaft/Kanal, Mikrofon-/Lautsprecher-Mute, AFK,
   Beobachtungszeitpunkte und letztes Mitglieds-Gateway-Ereignis. Gateway-Push
   zusätzlich zum Vollsync, Standard nach Benutzerentscheidung **30 statt 15 Minuten**.
3. Gruppen `central`/`users`: Sync-Button und drei Zähler zentral, Benutzergeräte
   verknüpft. Eigener Bot nur bei eindeutiger ID aus Benutzergruppe ausgeblendet.
4. Gemeinsame DM-Aktion/Python-Funktion für andere Integrationen, später je Mitglied
   Textfeld „Private Nachricht“ und Button „Private Nachricht senden“.
5. Bot-Gerät mit Kanal-Select (`alle verlassen` zuerst), HA-Standard-TTS,
   Ausführungsbutton, Wiedergabestatus und persistenter Lautstärke (Standard 50 %).
6. Voice-Karte mit Kategorien/Kanälen/Mitgliedern/Avataren/Mute, Text-Feed mit
   auswählbarem Kanal, visuellen Editoren und Dokumentation. Ressource manuell
   als `/your_discord_connect/discord-cards.js?v=1.0.1` registrieren.
7. Zuletzt Scroll-Fix: Feed soll nach **jedem** Update und nachgeladenen Bildern
   ganz unten stehen; kein Erhalt einer früheren hochgescrollten Position.

## Relevante Probleme und Lösungen

- **Installation startete nicht:** `discord.py[voice]==2.7.1` verlangt PyNaCl <1.6,
  HA 2026.10.4/2026.11.1 pinnt 1.6.2. Auf separate Abhängigkeiten umgestellt:
  `discord.py==2.7.1`, `PyNaCl==1.6.2`, `davey==0.2.0`; Entwicklungs-CFFI 2.0.0.
  HA-Constraints nicht aufweichen. `scripts/check_requirements.py` und CI prüfen
  Paketauflösung; native Audio-/Kryptotests prüfen verwendete APIs.
- **Feed sprang nach oben:** Implementierung ersetzte den DOM-Inhalt und versuchte
  alte Positionen zu erhalten. 1.0.1 scrollt sofort und nach dem Renderframe nach
  unten, außerdem bei Bild-Load. Regressionstest mit langem Feed, vorherigem
  Hochscrollen und späterem Bild-Layout; sechs Browsertests bestanden.
- **Audio-Details aus früherer Arbeit:** discord.py braucht ein Dateiobjekt für
  FFmpeg-stderr; `os.devnull` geöffnet übergeben. Neue FFmpeg-Versionen verwenden
  für stdin teils `fd` statt `pipe`, beide lokalen Protokolle erlaubt. Native
  Audiotests beibehalten. PCMVolumeTransformer/libopus ermöglicht laufende Lautstärkeänderungen.
- **Cloud-Tooling:** Standard-Cachepfade waren teilweise nicht schreibbar; lokale
  `UV_CACHE_DIR`/`npm_config_cache` halfen. Playwright-Browserdownload wurde blockiert;
  vorhandenes `/usr/bin/chromium` via `CHROMIUM_PATH` funktionierte. Keine allgemeine
  Aussage über Netzwerk oder Windows daraus ableiten.

## Benutzerentscheidungen, die erhalten bleiben müssen

- Dokumentation laufend mitpflegen, keine reine Einzelplatzlösung.
- Echtzeit für Presence/Voice; Vollsync bleibt für vollständige Mitglieder-/Kanalliste.
- Anwesenheit kann aus sichtbarer Sprachverbindung folgen, auch wenn Presence
  unsichtbar/offline ist. Das ist **keine** echte Login-Zeit und keine Umdeutung
  des Presence-Sensors. Bei Ausfall keine erfundene Abwesenheit.
- Gleiche Bot-Verbindung für angebotene DM-/TTS-Funktionen; Kanaländerungen müssen
  Dropdown und Übersicht aktualisieren.
- MusikAssistant ausdrücklich **später, nicht implementieren**. Zweiter Musik-Bot
  nur als Möglichkeit besprochen; eine App hat einen Bot, zweiter Bot braucht
  eigene App/Token und eine spätere Änderung der Entry-Identität.
- Kein beauftragter Kamera-/Video- oder allgemeiner Stream-Player.
- Versionierung ab 1.0.0, aktueller Patch 1.0.1. Ein Git-Push veröffentlicht nicht
  automatisch eine Cloud-Umgebung, ein GitHub-Release oder die HA-Installation.
- Wiederholte Chat-Hinweise „Umgebung veröffentlicht, warten, nichts erneut
  anwenden“ bezogen sich auf Cloud-Entwürfe. Bereits enthaltene Änderungen niemals
  aus alten Nachrichten nochmals anwenden; neuer konkreter Auftrag hat Vorrang.

## Letzte Commits und Evidenz

| Commit | Inhalt |
| --- | --- |
| `94de543` | Echtzeit, Gruppen, Beobachtungen und DM-API. |
| `5229494` | Zentrales Bot-Gerät, Voice-Steuerung und HA-TTS. |
| `78484d4` | HA-Dependency-Fix sowie vorhandener Volume-/Playback-Stand. |
| `78fa534` | Karten, DM-Bedienung und Version 1.0.0. |
| `f1e59cc` | Feed-Scroll-Fix und Version 1.0.1. |

Vor 1.0.0-Push: **96 Python-Tests und fünf Browsertests** bestanden. Nach Scroll-Fix:
**sechs Browsertests** bestanden; komplette Python-Suite nicht für den JS-Patch
erneut gelaufen. Keine Behauptung, dass alle Funktionen real in Discord abgenommen
wurden. Benutzer meldete HA Core 2026.11.1 / Supervisor 2026.11.0 / OS 18.4 /
Frontend 20261028.5; automatisierte Testbasis ist weiterhin HA 2026.10.4.

## Was als Nächstes ansteht

Die unmittelbar letzte Aufgabe war **Kontextbewahrung und geräteübergreifende
Weiterarbeit**, keine neue Funktion. Dokumentationsdateien und Git-Ausschlüsse
wurden dafür ergänzt. Den abschließenden Commit/Push anhand Git/Antwort prüfen;
keine ungeprüfte Annahme über eine noch laufende Übertragung machen.

Nächste sinnvolle Schritte: zweiter Rechner nach WINDOWS-Anleitung, neue Sitzung
mit diesen Dateien starten, echte Bestätigung des Scroll-Fixes einholen und die
offene Gesamtabnahme planen. Keine zurückgestellten Features eigenständig beginnen.
Prüfbefehle stehen in AGENTS/development; nach reinen Docs keine unnötige Vollsuite.

## Herkunft, Unsicherheiten und nicht gesicherte Informationen

**Bestätigt:** versionierter Code/History und Tool-Ergebnisse der zugänglichen
Unterhaltung; ausdrücklich sichtbare Benutzerwünsche. Einige ältere Arbeitsschritte
sind nur aus der im Gespräch verfügbaren Zusammenfassung rekonstruierbar.

**Nicht vollständig verfügbar/übernommen:** wortgetreuer Gesamtchat, frühere nicht
sichtbare Assistentenantworten/Anhänge, sämtliche Roh-Toolausgaben, interne
Gedankengänge, lokale Codex-Thread-/DB-Daten, andere Chats/Computer, lokale
App-Einstellungen, Account-Plugins/Skills und Cloud-Provider-Konfiguration.
Es wurden keine solchen internen Dateien gelesen oder migriert. Keine Tokens,
Mitgliederdaten oder Zugangsdaten in die Zusammenfassung aufnehmen.

**Offen statt angenommen:** echte Installations-/Hör-/DM-Abnahme, eingesetzte
Windows-/Codex-App-Versionen, vollständige automatische Synchronisierung lokaler
Desktop-Unterhaltungen. Die Produkt-Webdokumentation war aus der Umgebung gesperrt;
offizielle CLI-Quellen belegen `resume`, aber keine universelle Desktop-A/B-Synchronisierung.
Details/Quellen in WINDOWS. Neue Threads sollen sich auf Git-Projektwissen stützen.

## Pflege bei der nächsten Übergabe

Datum, letzten relevanten Funktionscommit, konkrete Änderungen, ausgeführte Tests,
Benutzerentscheidungen und nächsten Schritt aktualisieren. STATUS/TODO dazu
konsistent halten. Keine erfundenen Ergebnisse und keinen vollständigen privaten
Chatdump committen. `git status`, Fetch und Fast-Forward-Prüfung vor autorisiertem
Push; niemals fremde Änderungen durch Force-Push ersetzen.
