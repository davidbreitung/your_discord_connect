# Entwicklung

## Umgebung

Python **3.14.2+** und [uv](https://docs.astral.sh/uv/) verwenden:

```sh
cd your_discord_connect
uv sync --frozen
uv run python scripts/check_requirements.py
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Die Tests nutzen echtes Home Assistant **2026.10.4**, festgelegt durch
`pytest-homeassistant-custom-component==0.13.375`. `uv.lock` fixiert die
Entwicklungsabhängigkeiten. Discord-Antworten werden simuliert; Tokens, eine
externe Datenbank oder ein echter Server sind für die Tests nicht nötig.
REST nutzt Home Assistants `aiohttp`; das Gateway verwendet `discord.py==2.7.1` mit explizitem
`PyNaCl==1.6.2` und `davey==0.2.0`.
Die Bibliothek übernimmt Heartbeats, Reconnect, Session Resume und DAVE für Voice.
Für den nativen Audiotest FFmpeg mit Opus-Encoder installieren (unter Debian/Ubuntu
`sudo apt-get install ffmpeg libopus0`). CI installiert FFmpeg ausdrücklich.

In der Codex-Cloud liegt der Checkout unter `/workspace/your_discord_connect`.
Bei schreibgeschütztem Benutzer-Cache vor den Befehlen setzen:

```sh
export UV_CACHE_DIR=/workspace/.cache/uv
export UV_PYTHON_INSTALL_DIR=/workspace/.local/python
```

Den vorhandenen Checkout verwenden. Cloud-Aufgaben sind bereits isoliert; kein
zusätzliches Git-Worktree anlegen, außer es wird ausdrücklich gewünscht.

## Architektur

| Datei | Aufgabe |
| --- | --- |
| `api.py` | REST API v10, Authentifizierung, Paginierung, expliziter DM-Versand und Fehlerklassen. |
| `services.py`, `services.yaml` | Öffentliche DM-Aktion und Python-Funktion; Empfängervalidierung und Service-Antwort. |
| `config_flow.py` | Token, Serverauswahl, Zugriffsprüfung, Optionen, erneute Anmeldung. |
| `coordinator.py` | Ein zentraler Mitgliederabruf pro Server und Intervall. |
| `gateway.py` | Gateway-Lebenszyklus, Presence-Abfragen, Bot-Identität und expliziter Kanalabruf je Vollabgleich. |
| `voice.py` | Voice-Verbindung, HA-Standard-TTS, begrenzte Queue und FFmpeg-PCM-Verarbeitung und Opus-Wiedergabe. |
| `bot_entity.py`, `select.py`, `text.py` | Zentrales Bot-Gerät und Push-Aktualisierung seiner Bedienelemente. |
| `entity.py` | Gemeinsame Geräteidentität und Mitgliederentdeckung pro Plattform. |
| `sensor.py`, `binary_sensor.py` | Sieben Sensoren und vier Binärsensoren pro Mitglied sowie drei zentrale Zähler. |
| `groups.py` | Zwei feste Config Subentries, zentrale Geräteidentität und Migration bestehender Geräte. |
| `activity.py` | Beobachtungszustände und Zeitstempel in Home Assistants Store. |
| `button.py` | Manueller Abgleich über `button.press`, auch nach Fehlern bedienbar. |
| `__init__.py` | Einrichtung, Entladen, Neuladen nach Optionsänderungen. |
| `strings.json`, `translations/` | Basistexte und deutsche/englische Oberfläche. |

Ein Server entspricht einem Config Entry mit eindeutiger Server-ID. Geräte nutzen
`(your_discord_connect, <server_id>_<user_id>)`; Sensoren verwenden
`<server_id>_<user_id>_display_name` als Unique ID. Niemals IDs aus Namen ableiten.
Ein Mitglied mehrerer Server wird dadurch je Server unabhängig abgebildet.

Der Coordinator übernimmt einen Snapshot erst nach vollständig erfolgreichem
Abruf aller REST-Seiten und erfolgreichem Gateway-Snapshot. Teilfehler dürfen keine Löschung auslösen. HTTP 429 beendet
den Durchlauf ohne sofortige Wiederholungsschleife; der nächste geplante Abgleich
versucht es erneut. HTTP 401 löst eine erneute Anmeldung aus.

Private Textnachrichten werden nur über explizite Service-/API-Aufrufe gesendet. Ziele sind `https://discord.com/api/v10`
und die von Discord gelieferten Gateway-/Resume-Adressen unter `discord.gg` (WSS).
Gateway-Intents: guilds, members, presences und voice_states; keine Nachrichtenintents.

Pro Servereintrag läuft ein Gateway-Client als Home-Assistant-Hintergrundtask.
Fehlgeschlagene Einrichtung, Entladen und HA-Stopp schließen ihn. Mehrere Server
bedeuten mehrere Verbindungen; Discord-Sessionlimits bei großen Installationen beachten.

Normale Member-Chunks enthalten nicht zuverlässig Presence-Daten. Jeder Abgleich
verwendet daher `query_members(user_ids=..., presences=True, cache=True)` in Gruppen
von höchstens 100 IDs. Sprachzustände kommen aus dem laufend gepflegten Guild-Cache.
Ergebnisse werden in unveränderliche Member-Snapshots kopiert. Presence- und
Voice-State-Ereignisse aktualisieren bekannte Mitglieder und die zentralen Zähler
sofort. Fehlende Mitglieder bleiben unbekannt.
Ein Gateway-Abbruch während einer Abfrage verwirft den Snapshot.

Neue Unique-ID-Suffixe: `username`, `presence`, `in_voice_channel`, `voice_channel`.
Die bisherigen IDs und Geräte bleiben erhalten. Der Button hat `<server_id>_sync`
und wird dem Gerät `<server_id>_central` in der Untergruppe `central` zugeordnet.
Mitgliedsgeräte gehören zur Untergruppe `users` und verwenden `via_device_id` zur Zentrale.
Registry-Bereinigung erfolgt zentral für beide Mitgliederplattformen und lässt
 den Button und zentrale Zähler bestehen.

## Ereignisverarbeitung und Beobachtungszeitpunkte

Standardintervall des vollständigen Abgleichs: 30 Minuten, eigene Optionen bleiben
bestehen. Gateway-Pushes aktualisieren `coordinator.data` und rufen die Listener auf,
ohne den Polling-Timer neu zu starten. Ereignisse während eines Vollabgleichs werden
zusätzlich gepuffert und über dessen Snapshot gelegt, damit ältere Abfragewerte
nicht gerade empfangene Änderungen zurücksetzen.

Anwesenheit = Presence online/idle/dnd oder bestehender Sprachzustand. Abwesenheit =
offline und kein Sprachzustand. Fehlende Daten und Verbindungsabbrüche erzeugen keine
Abwesenheitsbeobachtung. Erste bekannte Zustände erhalten den Beobachtungszeitpunkt;
spätere Zustandswechsel aktualisieren den jeweiligen Zeitstempel. Kein Login-Zeitpunkt
wird rückwirkend erfunden. `last_gateway_event` wird nur von benutzerbezogenen Presence-
und Voice-State-Ereignissen gesetzt, nicht durch Abfragen oder Heartbeats.

`ActivityTracker` persistiert Bool-Zustand und UTC-Zeitstempel mit Home Assistants
`Store` unter `your_discord_connect.<guild_id>.activity`. Saves werden fünf Sekunden
gebündelt; Entladen/Stoppen schreibt abschließend. Austritte bereinigen die Daten;
Entfernen des Config Entry löscht die Datei. Bei hartem Abbruch können die jüngsten
noch nicht gespeicherten Ereignisse verloren gehen.

Mikrofon-Mute = self_mute OR mute; Lautsprecher-Mute = self_deaf OR deaf. Stage-Suppress
wird nicht als Mikrofon-Mute interpretiert. AFK wird anhand der konfigurierten
`guild.afk_channel`-ID festgestellt. Bei vorhandener Sprachverbindung mit unbekanntem
Kanalnamen bleibt der AFK-Zustand unbekannt, sofern ein AFK-Kanal konfiguriert ist.

## Bot-Steuerung und Audio

Der eigene Bot wird ausschließlich über `client.user.id` erkannt und nur bei sicherer
Identität aus den Benutzergeräten ausgefiltert; die Coordinator-Mitgliederliste und
Zähler bleiben vollständig. Das neue Gerätekennzeichen ist `<guild_id>_bot`, dessen
Entitäten heißen `<guild_id>_bot_channel`, `<guild_id>_tts_message` und
`<guild_id>_tts_execute`. Beim Upgrade werden frühere Mitgliederentitäten des eigenen
Bots bereinigt. Alle drei Steuerelemente gehören zur Untergruppe `central`.

`guild.fetch_channels()` läuft bei jedem vollständigen Mitgliederabgleich. Die Liste
enthält Voice- und Stage-Kanäle, keine Textkanäle. Gateway-Kanalereignisse aktualisieren
sie zusätzlich. Eine Revisionsnummer verhindert, dass eine ältere HTTP-Antwort ein
zwischenzeitlich empfangenes Kanalereignis überschreibt. Die Auswahl wird anhand der
Kanal-ID ausgewertet, nicht aus einem möglicherweise doppelt vergebenen Namen.

`BotVoice` serialisiert Verbindungsänderungen und Durchsagen separat. Maximal fünf
TTS-Aufträge einschließlich laufender Wiedergabe werden akzeptiert. Jeder erfasst Text
und Kanal beim Knopfdruck. Kanalwechsel, Disconnect und Unload brechen Aufträge ab.
`tts.async_default_engine`/`generate_media_source_id`/`async_get_media_source_audio`
verwenden den vorhandenen HA-TTS-Unterbau; keine zweite TTS-Anmeldung und keine
öffentliche Media-URL sind nötig. Der konfigurierte HA-FFmpeg-Pfad wird verwendet.

FFmpeg liest ausschließlich generierte Audiodaten aus einer Pipe; die Protokolle
sind auf `pipe,fd` eingeschränkt. Prozessstart läuft im Executor. Discords Audio-Thread
liest Opus-Pakete und übernimmt nach `play` die Source-Bereinigung. Der Completion-
Callback wechselt threadsicher zurück in den HA-Event-Loop. Abbruch während des
Prozessstarts bereinigt die Source nach Abschluss des Executor-Jobs. Text maximal
255 Zeichen, Generierung maximal 60 Sekunden, Audiodaten maximal 10 MiB, Wiedergabe
maximal 120 Sekunden. Keine automatische Wiederholung nach Fehlern.

Text und Kanalauswahl werden nicht über Neustarts wiederhergestellt. Die bestehende
DM-Schnittstelle bleibt unabhängig von der Voice-Verbindung nutzbar. Details und
Bedienungsbeispiele stehen in [voice.md](voice.md).

## Tests und reale Abnahme

Tests prüfen HTTP-Fehler, Paginierung, Einrichtung, Optionen, Geräteanlage,
Umbenennung, Ein-/Austritt, Neustart, Fehlererholung und regelmäßige Abfragen.
GitHub Actions führt Tests und Ruff-Prüfungen aus.

Für eine reale Abnahme auf einer separaten HA-Instanz die
[Installation](installation.md) durchführen:

1. Testbot und Testserver einrichten; echten Mitgliederabruf bestätigen.
2. Server-Spitzname ändern; nach Synchronisation Sensorwert prüfen.
3. Testmitglied einladen und entfernen; Geräteanlage und Entfernung prüfen.
4. Intervall ändern und HA neu starten; Optionen und Geräte prüfen.
5. Presence wechseln; sofortige Aktualisierung ohne manuellen Abgleich prüfen.
6. Sprachkanal betreten, wechseln und verlassen; sofortige Aktualisierung prüfen.
   Selbst-/Server-Mute, Deafen und den konfigurierten AFK-Kanal testen.
7. Gateway-Verbindung unterbrechen; Geräteerhalt, Nichtverfügbarkeit und Erholung prüfen.
8. Bot-Token zurücksetzen; erneute Anmeldung abschließen.
9. Bot-Gerät prüfen: nur eigene Bot-ID aus Benutzergruppe ausgeblendet.
10. Sprachkanal wählen/wechseln/verlassen; echten TTS-Hörtest mit konfiguriertem Anbieter durchführen.
11. Kanal anlegen/umbenennen/löschen: sofortige und periodische Dropdown-Aktualisierung prüfen.
12. Laufende/wartende Durchsagen durch Kanalwechsel abbrechen; Stage-Freigaben und Voice-UDP testen.

Die reale Discord-Abnahme und HACS-Installation aus einem veröffentlichten
Repository stehen noch aus.

## Änderungen pflegen

Bei Funktionsänderungen Tests, README, Installationsanleitung und Changelog
mitpflegen. Neue UI-Texte in `strings.json` und beiden Übersetzungen ergänzen.
Keine echten Tokens oder Mitgliederdaten in Tests oder Issues übernehmen.
Weitere Attribute sollen bestehende Unique IDs unverändert lassen.

Die öffentliche Versand-Schnittstelle und Beispiele für andere Integrationen stehen
in [api.md](api.md). Versandtests simulieren alle HTTP-Aufrufe; keine echten DMs
werden in Tests verschickt. Die reale DM-Abnahme mit einem eigenen Testempfänger
steht noch aus.

## Installationsabhängigkeiten prüfen

`python scripts/check_requirements.py` löst die Manifest-Abhängigkeiten mit
Home Assistants `package_constraints.txt` auf, wie es auch der HA-Installer tut.
CI führt diese Prüfung zusätzlich zu den Funktionstests aus. Ein optionaler
Dateipfad als Argument erlaubt die Prüfung gegen die Vorgaben einer weiteren
HA-Version. Die korrigierte Paketkombination wurde gegen 2026.10.4 und 2026.11.1
aufgelöst. Die Funktionstests laufen weiterhin auf 2026.10.4.

Das Discord-Voice-Extra setzt eine mit HA unvereinbare PyNaCl-Obergrenze. Deshalb
werden die benötigten Voice-Pakete separat deklariert und die tatsächlich von
discord.py genutzte AEAD-Verschlüsselung mit dieser Kombination getestet.
Die Entwicklungsumgebung verwendet außerdem HA-kompatibles CFFI 2.0.0.

## Dashboard-Frontend testen

Die Karten bestehen aus einem lokalen JavaScript-Modul ohne Laufzeitabhängigkeiten
oder Build-Schritt. `frontend/discord-cards.js` muss im Integrationsordner enthalten
sein. `dashboard.py` registriert die statische Ressource und die authentifizierten
WebSocket-Kommandos für Serverliste, Voice-Abonnement und Text-Feed.

```sh
npm ci
npx playwright install chromium
npm test
```

Bei vorhandenem Chromium alternativ `CHROMIUM_PATH=/usr/bin/chromium npm test`.
Die Browsertests verwenden simulierte HA-/Discord-Daten, prüfen DOM-Darstellung,
Live-Updates, Editor, Zugriff auf unsichere Links, mobiles Layout und Aufräumen
der Abonnements. Ein Demo-Screenshot entsteht unter `test-results/discord-cards.png`.
Die Python-Tests prüfen zusätzlich echte HA-WebSocket-Kommandos, Berechtigungen,
Kanalisolierung, Feed-Cache sowie Direktnachrichten über die HA-Entitäten.
