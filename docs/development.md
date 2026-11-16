# Entwicklung

## Umgebung

Python **3.14.2+** und [uv](https://docs.astral.sh/uv/) verwenden:

```sh
cd your_discord_connect
uv sync --frozen
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

Die Tests nutzen echtes Home Assistant **2026.10.4**, festgelegt durch
`pytest-homeassistant-custom-component==0.13.375`. `uv.lock` fixiert die
Entwicklungsabhängigkeiten. Discord-Antworten werden simuliert; Tokens, eine
externe Datenbank oder ein echter Server sind für die Tests nicht nötig.
REST nutzt Home Assistants `aiohttp`; das Gateway verwendet `discord.py==2.6.4`.
Die Bibliothek übernimmt Heartbeats, Reconnect und Session Resume.

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
| `api.py` | REST API v10, Authentifizierung, Paginierung, Fehlerklassen. |
| `config_flow.py` | Token, Serverauswahl, Zugriffsprüfung, Optionen, erneute Anmeldung. |
| `coordinator.py` | Ein zentraler Mitgliederabruf pro Server und Intervall. |
| `gateway.py` | Gateway-Lebenszyklus, Presence-Abfragen, Sprachkanal-Snapshots. |
| `entity.py` | Gemeinsame Geräteidentität und Mitgliederentdeckung pro Plattform. |
| `sensor.py`, `binary_sensor.py` | Vier Sensoren und ein Sprachverbindungs-Binärsensor pro Mitglied. |
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

Die Integration sendet keine Nachrichten. Ziele sind `https://discord.com/api/v10`
und die von Discord gelieferten Gateway-/Resume-Adressen unter `discord.gg` (WSS).
Gateway-Intents: guilds, members, presences und voice_states; keine Nachrichtenintents.

Pro Servereintrag läuft ein Gateway-Client als Home-Assistant-Hintergrundtask.
Fehlgeschlagene Einrichtung, Entladen und HA-Stopp schließen ihn. Mehrere Server
bedeuten mehrere Verbindungen; Discord-Sessionlimits bei großen Installationen beachten.

Normale Member-Chunks enthalten nicht zuverlässig Presence-Daten. Jeder Abgleich
verwendet daher `query_members(user_ids=..., presences=True, cache=True)` in Gruppen
von höchstens 100 IDs. Sprachzustände kommen aus dem laufend gepflegten Guild-Cache.
Ergebnisse werden in unveränderliche Member-Snapshots kopiert; Gateway-Ereignisse
allein veröffentlichen keine HA-Zustände. Fehlende Mitglieder bleiben unbekannt.
Ein Gateway-Abbruch während einer Abfrage verwirft den Snapshot.

Neue Unique-ID-Suffixe: `username`, `presence`, `in_voice_channel`, `voice_channel`.
Die bisherigen IDs und Geräte bleiben erhalten. Der Button hat `<server_id>_sync`
und ist dem Config Entry zugeordnet, ohne ein weiteres Mitgliedsgerät anzulegen.
Registry-Bereinigung erfolgt zentral für beide Mitgliederplattformen und lässt
 den Button bestehen.

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
5. Presence zwischen online, abwesend und nicht stören wechseln; manuell synchronisieren.
6. Sprachkanal betreten, wechseln und verlassen; Status und Kanalname nach Abgleich prüfen.
7. Gateway-Verbindung unterbrechen; Geräteerhalt, Nichtverfügbarkeit und Erholung prüfen.
8. Bot-Token zurücksetzen; erneute Anmeldung abschließen.

Die reale Discord-Abnahme und HACS-Installation aus einem veröffentlichten
Repository stehen noch aus.

## Änderungen pflegen

Bei Funktionsänderungen Tests, README, Installationsanleitung und Changelog
mitpflegen. Neue UI-Texte in `strings.json` und beiden Übersetzungen ergänzen.
Keine echten Tokens oder Mitgliederdaten in Tests oder Issues übernehmen.
Weitere Attribute sollen bestehende Unique IDs unverändert lassen.
