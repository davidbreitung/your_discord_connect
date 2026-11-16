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
Im Betrieb nutzt die Integration Home Assistants `aiohttp` ohne Zusatzbibliothek.

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
| `sensor.py` | Geräte und Anzeigenamen-Sensoren anlegen, aktualisieren, entfernen. |
| `__init__.py` | Einrichtung, Entladen, Neuladen nach Optionsänderungen. |
| `strings.json`, `translations/` | Basistexte und deutsche/englische Oberfläche. |

Ein Server entspricht einem Config Entry mit eindeutiger Server-ID. Geräte nutzen
`(your_discord_connect, <server_id>_<user_id>)`; Sensoren verwenden
`<server_id>_<user_id>_display_name` als Unique ID. Niemals IDs aus Namen ableiten.
Ein Mitglied mehrerer Server wird dadurch je Server unabhängig abgebildet.

Der Coordinator übernimmt einen Snapshot erst nach vollständig erfolgreichem
Abruf aller Seiten. Teilfehler dürfen keine Löschung auslösen. HTTP 429 beendet
den Durchlauf ohne sofortige Wiederholungsschleife; der nächste geplante Abgleich
versucht es erneut. HTTP 401 löst eine erneute Anmeldung aus.

Die Integration schreibt nicht nach Discord und nutzt kein Gateway. Das externe
Ziel im Betrieb ist `https://discord.com/api/v10`.

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
5. Bot-Token zurücksetzen; erneute Anmeldung abschließen.

Die reale Discord-Abnahme und HACS-Installation aus einem veröffentlichten
Repository stehen noch aus.

## Änderungen pflegen

Bei Funktionsänderungen Tests, README, Installationsanleitung und Changelog
mitpflegen. Neue UI-Texte in `strings.json` und beiden Übersetzungen ergänzen.
Keine echten Tokens oder Mitgliederdaten in Tests oder Issues übernehmen.
Weitere Attribute sollen bestehende Unique IDs unverändert lassen.
