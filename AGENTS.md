# Your Discord Connect – dauerhafte Arbeitsanweisungen

## Einstieg und Quellen

- Mit dem Benutzer auf Deutsch kommunizieren; Code-Bezeichner und bestehende
  technische Kommentare bleiben Englisch. Bestehenden Code und lokale Änderungen
  vor jeder Bearbeitung prüfen und erhalten.
- Zuerst `docs/HANDOVER.md`, `docs/STATUS.md` und `docs/TODO.md` lesen; bei technischen
  Änderungen zusätzlich `docs/ARCHITECTURE.md` und `docs/DECISIONS.md`.
- Git/Code sind die Quelle für den tatsächlichen Stand. Übergaben enthalten
  datierte Beobachtungen, keine Garantie über spätere Änderungen. Unbekanntes als
  unbekannt kennzeichnen; Chat-Zusammenfassungen sind kein vollständiger Chat-Export.
- Ziel ist eine eigenständige, für Dritte installierbare Home-Assistant-Integration.
  Keine grundlegende Umstrukturierung oder zusätzliche Plattform ohne Auftrag.
- Music Assistant, ein zweiter Bot auf demselben Server und allgemeines
  Musik-/Video-Streaming sind zurückgestellt, nicht freigegebenes Restprogramm.

## Architekturregeln

- Domain: `your_discord_connect`; HA Custom Integration, kein Add-on und kein
  separater Bot-Dienst. Ein Config Entry pro Discord-Server, ein Coordinator und
  Gateway-Client je Entry. Versionsbasis und Abhängigkeiten aus Manifest/Lockfiles.
- Identität immer über Server-, Mitglieds- und Kanal-IDs, niemals Namen.
  Bestehende Geräte-/Entitäts-IDs erhalten; Migrationen bewusst dokumentieren.
- Vollabgleich standardmäßig 30 Minuten, Benutzeroptionen erhalten. Geräte nur
  nach vollständig erfolgreichem Abgleich entfernen. Fehler sind keine leere Liste.
- Gateway-Pushes dürfen den Polling-Timer nicht verschieben. Ereignisse während
  laufender Abfragen müssen Vorrang vor älteren Snapshot-Daten behalten.
- Presence bleibt Discord-Presence. Beobachtete Anwesenheit darf zusätzlich eine
  Sprachverbindung berücksichtigen; unsichtbar wird nicht zu sichtbarer Presence.
  Zeitstempel sind Beobachtungen, keine tatsächlichen Login-/Logout-Zeitpunkte.
  Fehlende Daten und Bot-Ausfälle erzeugen keine künstliche Abwesenheit.
- Eigener Bot: nur über sichere Bot-ID aus Benutzergeräten ausblenden, weiterhin
  in Daten/Zählern enthalten. Zentrale und Benutzer-Config-Subentries erhalten.
- Nachrichten und Audio nur auf explizite Bedienung/Aktionsaufrufe senden.
  Keine automatischen DM-Wiederholungen bei unklarer Zustellung. Tests senden
  niemals echte Nachrichten und benötigen keine echten Zugangsdaten.
- TTS nutzt den HA-Unterbau. Blocking Audio-/Subprozessarbeit im Executor;
  Queue-/Verbindungs-/Lifecycle-Bereinigung erhalten. Kein Shell-Aufruf für Texte.
- Dashboard-Daten nur über authentifizierte HA-WebSockets; vorhandene HA- und
  Bot-Kanalberechtigungsprüfungen erhalten. Kein Token ins Frontend. Externe
  Nachrichtentexte niemals ungeprüft als HTML rendern.
- Voice-Übersicht per Push; Text-Feed bewusst REST-Polling mit begrenztem Cache.
  Feed scrollt nach jeder Aktualisierung und nach geladenen Bildern ganz nach unten.

## Abhängigkeiten und Tests

- Python >= 3.14.2, für reproduzierbare Arbeit Python 3.14 verwenden; `uv` 0.13.6,
  Node.js 22 für Browsertests. Vollständige HA-Tests unter Linux/WSL2, nicht als
  zugesicherter nativer Windows-Workflow. Anleitung: `docs/WINDOWS.md`.
- `discord.py[voice]==2.7.1` **nicht wieder einführen**: PyNaCl < 1.6 kollidiert mit
  HA. Aktuell separate Anforderungen Discord 2.7.1, PyNaCl 1.6.2 und davey 0.2.0;
  Entwicklungs-CFFI 2.0.0 entspricht HA. Änderungen gegen HA-Constraints prüfen.
- `uv.lock` und `package-lock.json` pflegen; keine unkontrollierten Upgrades.
- Python: `uv sync --frozen`, `uv run ruff check .`, `uv run ruff format --check .`,
  `uv run pytest`. Bei Dependency-/Manifeständerungen zusätzlich
  `uv run python scripts/check_requirements.py`.
- Frontend: `npm ci`, `npx playwright install chromium`, `npm test`;
  alternativ vorhandenes Chromium über `CHROMIUM_PATH` auswählen.
- Sinnvolle, betroffene Tests zuerst. Keine redundanten Testläufe für reine
  Dokumentationsänderungen; stattdessen Links, Befehle und Git-Diff prüfen.
- Simulierte HA-/Discord- und isolierte Browsertests klar von echter
  Discord-/TTS-/HACS-Abnahme unterscheiden. Keine unbelegten Erfolgsbehauptungen.

## Dokumentation und Übergabe

- Funktionen mit Anleitung/README, Übersetzungen (`strings.json`, `de.json`,
  `en.json`), passender Prüfung und Changelog pflegen.
- Architekturänderungen mit Begründung in `docs/DECISIONS.md` dokumentieren.
  Aufgabenstatus in `docs/TODO.md`, aktuellen Stand in `docs/STATUS.md` und die
  nächste Übergabe in `docs/HANDOVER.md` aktualisieren, wenn sich diese ändern.
- Bei Releases Versionsangaben in Manifest, Python-/npm-Metadaten/Lockfiles,
  API-User-Agent, Frontend-Dateikopf und Anleitungen konsistent halten.
  Kartenressourcen-URL zur Cache-Aktualisierung beachten. Reine Docs brauchen
  keine neue Integrationsversion.

## Git, Geheimnisse und Rechnerwechsel

- Vorher `git status --short --branch`, `git branch -vv`, Remote und History prüfen.
  Bestehender gemeinsamer Entwicklungsbranch ist derzeit `origin/main`. In der
  Cloud heißt der lokale Branch `work` ohne Upstream; daraus keinen neuen
  Remote-Branch ableiten. Ziel bei diesem bestätigten Zustand: `HEAD:main`.
- Vor autorisiertem Push `git fetch origin` und Abweichungen prüfen. Kein Force-Push,
  keine fremden Änderungen verwerfen. Bei Divergenz Änderungen erhalten und erst
  regulär integrieren; bei unklaren Konflikten gezielt nachfragen.
- Commit/Push nach aktuellem Auftrag; nicht aus alten Einzelaufträgen eine
  unbegrenzte Erlaubnis für zukünftige Veröffentlichungen ableiten.
- Ein Windows-Rechner arbeitet aktiv, dann Commit/Push, dann anderer Rechner
  Fetch/Pull. Keine Synchronisierung aktiver Checkouts per OneDrive/Dropbox.
- Keine Tokens, HA-Konfigurationsspeicher, privaten Mitgliederdaten, Logs oder
  Codex-Authentifizierungs-/Sitzungsdaten in Git. Nur geprüfte, anonymisierte
  Erkenntnisse in der Übergabe. `.gitignore` ersetzt keine Geheimnisprüfung.
- Interne Codex-Dateien/-Datenbanken nicht kopieren, zusammenführen oder verändern
  ohne ausdrückliche Freigabe. Keine eigene Synchronisation von `CODEX_HOME`.
- Cloud-Umgebungsveröffentlichung, Git-Push, Release und HA-Deployment sind
  verschiedene Aktionen. Produktive Systeme nicht ohne entsprechenden Auftrag ändern.
