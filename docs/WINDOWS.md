# Auf mehreren Windows-Rechnern mit Codex weiterarbeiten

Stand: 17.11.2026. GitHub ist die Quelle für **Code und dokumentiertes Projektwissen**.
Jeder Rechner erhält einen eigenen Checkout. Keine Freigabe, OneDrive-/Dropbox-
Synchronisierung oder Kopie eines aktiven `.git`-/Codex-Datenverzeichnisses verwenden.

## 1. Voraussetzungen pro Rechner

- Eine für den Rechner unterstützte **Codex-Desktop-App**, separat angemeldet.
  Konto-/Organisationseinstellungen und verfügbare App-Funktionen lokal prüfen.
- **Git for Windows** einschließlich Git Credential Manager; GitHub-Anmeldung
  per Browser/Anmeldedialog. Keine Tokens in Clone-URLs oder Dateien schreiben.
- **WSL2 mit Ubuntu** für die vollständige Linux-/Home-Assistant-Testumgebung.
  Home Assistant Core wird hier nicht als native Windows-Laufzeit vorausgesetzt.
- In WSL: Git, curl, CA-Zertifikate, **uv 0.13.6**, **Python 3.14 >=3.14.2**,
  FFmpeg, libopus, **Node.js 22** und npm. Playwright wird über `npm ci` installiert.
- Netzwerk für GitHub, Python-/npm-Pakete und ggf. Playwright-Browserdownload.
  Für automatisierte Tests sind **kein Discord-Token, kein HA-Zugang und kein
  OpenAI-API-Key im Projekt** erforderlich.

Der Weg wurde aus der vorhandenen Linux-/CI-Konfiguration abgeleitet, nicht auf
Deinen Windows-Rechnern ausgeführt. Menütexte und WSL-Integration der Desktop-App
können versionsabhängig sein. Kein bestimmtes Desktop-WSL-Feature ist Voraussetzung:
Die App öffnet den Windows-Ordner; Tests können explizit im Ubuntu-Terminal laufen.

## 2. Klonen und in der Desktop-App öffnen

In PowerShell, Pfad bei Bedarf anpassen:

```powershell
New-Item -ItemType Directory -Force C:\dev | Out-Null
Set-Location C:\dev
git -c core.autocrlf=false clone https://github.com/davidbreitung/your_discord_connect.git
Set-Location C:\dev\your_discord_connect
git config --local core.autocrlf false
git switch main
git pull --ff-only origin main
git status --short --branch
git log -1 --oneline
```

`core.autocrlf=false` ist eine lokale Einstellung für diesen Checkout und verhindert
unnötige Zeilenende-Änderungen zwischen Windows und WSL. Eigene Git-Identität auf
jedem Rechner korrekt einrichten (`git config user.name` / `user.email` prüfen),
bevor Commits erstellt werden. Anmeldungen werden nicht durch Klonen übertragen.

In Codex Desktop den Ordner **`C:\dev\your_discord_connect`** als Projekt öffnen.
Eine neue Unterhaltung mit folgendem Einstieg beginnen:

> Lies AGENTS.md, docs/HANDOVER.md, docs/STATUS.md und docs/TODO.md. Prüfe zuerst
> den aktuellen Git-Stand und die vorhandenen lokalen Änderungen. Setze danach
> folgende Aufgabe fort: [konkrete Aufgabe]. Erfinde keinen fehlenden Chat-Kontext
> und wende bereits abgeschlossene Änderungen nicht erneut an. Die vollständigen
> HA-Tests laufen in WSL2, siehe docs/WINDOWS.md.

Damit erhält Codex die entscheidungsrelevanten Informationen aus dem Repo, ohne
Zugriff auf die ursprüngliche Unterhaltung vorauszusetzen. Alte persönliche Codex-
Anweisungen/Plugins werden dadurch nicht automatisch auf dem zweiten PC eingerichtet.

## 3. Linux-Testumgebung über WSL2

Falls noch nicht vorhanden: WSL/Ubuntu über die Microsoft-Anleitung installieren
(z. B. `wsl --install -d Ubuntu` in einer entsprechend berechtigten PowerShell),
bei Aufforderung Windows neu starten und Ubuntu-Benutzer einrichten.

Im **Ubuntu-Terminal**, nicht in PowerShell:

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates ffmpeg libopus0
cd /mnt/c/dev/your_discord_connect
```

`uv` 0.13.6 nach der [offiziellen Installation](https://docs.astral.sh/uv/getting-started/installation/)
installieren. Der versionierte Installer kann so aufgerufen werden:

```bash
curl -LsSf https://astral.sh/uv/0.13.6/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
uv python install 3.14
uv sync --python 3.14 --frozen
```

**Node.js 22 in WSL** installieren, z. B. über ein separat nach dessen
[offizieller Anleitung](https://github.com/nvm-sh/nvm#installing-and-updating)
eingerichtetes nvm. Danach in einer Shell mit geladenem nvm:

```bash
nvm install 22
nvm use 22
node --version
npm --version
npm ci
npx playwright install --with-deps chromium
```

`--with-deps` kann Ubuntu-Systempakete und entsprechende Berechtigungen benötigen.
Falls ein verwalteter Rechner Downloads untersagt, lokale IT-/Netzwerkvorgaben beachten.
Ein vorhandenes Linux-Chromium lässt sich alternativ über `CHROMIUM_PATH` auswählen.
Keinen heruntergeladenen Windows-Browser mit Linux-Playwright mischen.

Prüfungen:

```bash
uv run ruff check .
uv run ruff format --check .
uv run python scripts/check_requirements.py
uv run pytest
npm test
```

Die `.venv` und `node_modules` in diesem Checkout werden **nur in WSL** aufgebaut
und genutzt. Nicht zwischen Windows-Python/-Node und WSL wechseln. In PowerShell
bei Bedarf `wsl -d Ubuntu` öffnen und dann die obigen Befehle ausführen.
Gleichzeitige Mutationen desselben Checkouts durch zwei Tools vermeiden.

Auf `/mnt/c` kann Dateizugriff langsamer sein als im WSL-Dateisystem. Die einfache
Windows-Ordner-Lösung ist hier bewusst die Ausgangsbasis. Eine spätere Verlagerung
in WSL nur bewusst vornehmen und vorher prüfen, wie die installierte Desktop-App
WSL-Projekte unterstützt; nicht unbemerkt zwei auseinanderlaufende Kopien anlegen.

## 4. Alltag: Rechner A → B → A

**Vor jeder Arbeit**, aus dem Projektordner:

```powershell
git status --short --branch
git branch -vv
git fetch origin
git switch main
git pull --ff-only origin main
```

Nur bei sauberem Arbeitsverzeichnis wechseln/pullen. Bei lokalen Änderungen diese
zuerst prüfen und sinnvoll committen oder separat sichern; kein `reset --hard`,
kein erzwungenes Checkout und kein blindes `clean`. Bei einem bereits begonnenen
Feature-Branch stattdessen genau diesen Branch auf beiden Rechnern verwenden.

**Vor dem Wechsel von A nach B:**

1. Arbeit beenden; STATUS/TODO/HANDOVER bei relevanten Änderungen mitpflegen.
2. Betroffene Prüfungen ausführen und Ergebnisse/Restaufgaben notieren.
3. Änderungen prüfen, gezielt stagen und committen. Für bewusst unfertige Arbeit
   einen klar benannten Branch mit Übergabenotiz statt stillschweigender Fertigmeldung nutzen.

```powershell
git diff --check
git diff
# Nur geprüfte Dateien hinzufügen; Platzhalter durch tatsächliche Pfade ersetzen:
git add <Dateipfade>
git diff --cached --stat
git diff --cached
git commit -m "Beschreibe die konkrete Änderung"
git fetch origin
git push origin HEAD:main
git status --short --branch
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

Den `git add <Dateipfade>`-Platzhalter nicht wörtlich ausführen. Vor dem Push auch
neue/unversionierte Dateien prüfen; normale `git diff`-Ausgabe zeigt deren Inhalt
noch nicht. Der Push ist ohne Force: neuere fremde Commits werden nicht überschrieben.
Bei Ablehnung zuerst `git fetch origin` und `git log --oneline --left-right
HEAD...origin/main` prüfen. Änderungen regulär zusammenführen; unklare fachliche
Konflikte mit Codex und Benutzer klären. Nicht einfach Force-Push verwenden.

**Auf B:** dieselben Fetch/Pull-Befehle, identischen Commit prüfen, Projekt öffnen,
Übergabedateien lesen lassen. Bei geänderten Lockfiles in WSL erneut `uv sync --frozen`
bzw. `npm ci`; bei geänderter Playwright-Version ggf. Browser nachinstallieren.
Rückweg B → A ist identisch. Ein Stash, uncommittete Dateien und lokale Branches
werden durch Push/Pull nicht automatisch übertragen.

**Sonderfall dieser Cloud-Umgebung:** lokaler Branch `work`, kein Upstream,
Remote-Entwicklungsbranch `main`. Dort wurde bewusst `git push origin HEAD:main`
verwendet. Ein normaler neuer Windows-Clone verwendet dagegen `main` mit
`origin/main` als Upstream. Keinen Remote-Branch `work` allein wegen des Cloud-Namens anlegen.

## 5. Was Git synchronisiert – und was nicht

| Kategorie | Übertragung / Wiederherstellung |
| --- | --- |
| Python-/JS-Code, Übersetzungen, Tests, CI, Dokumentation | Versioniert, per Clone/Pull. |
| AGENTS/ARCHITECTURE/DECISIONS/STATUS/TODO/HANDOVER | Versioniertes Projektwissen; bei der Weiterarbeit aktiv pflegen. |
| `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`, Manifest | Versioniert; lokale Pakete mit `uv sync --frozen` / `npm ci` rekonstruieren. |
| `.venv/`, `node_modules/` | Ignoriert, pro Rechner/OS neu erzeugen. |
| Python-/Ruff-/pytest-Caches, Coverage, `test-results/` | Ignoriert, reproduzierbare Ergebnisse; Screenshots bei Bedarf neu erstellen. |
| FFmpeg, libopus, Python, uv, Node, Browser-Binaries | System-/Benutzerinstallation, nicht Git; pro Rechner einrichten. |
| `.ha-dev/`, `.storage/`, `secrets.yaml`, `.env*` | Lokale Konfiguration/Geheimnisse, nicht Git; für Mock-Tests nicht erforderlich. Geprüfte `.env.example`/`.env.sample` dürfen nur Platzhalter enthalten. |
| HA-Bot-Token, reale Geräte, Recorder, TTS-Anbieter, Dashboard-Ressource | Laufende HA-Installation, nicht Entwicklungs-Checkout. Nicht von A/B automatisch deployen. |
| GitHub-/Codex-Login, Credential Manager, SSH-Schlüssel | Pro Gerät separat, nicht über Repo verteilen. |
| `.git`-Konfiguration, Stashes, Hooks, lokale nicht gepushte Branches | Lokaler Git-Zustand, kein synchronisierter Projektinhalt. |
| Codex-Sitzungen, interne DBs, UI-Einstellungen, Benutzerskills/Plugins | Nicht Git. Projektwissen stattdessen über diese Dokumente. Keine internen Verzeichnisse kopieren. |
| Cloud-Setup-Skripte/Netzwerkregeln außerhalb des Repos | Nicht Teil des Clones. Relevante Voraussetzungen stehen hier; kein vollständiger Export der Cloud-Umgebung. |

Zum Kontrollieren: `git ls-files`, `git status --short`, `git status --ignored --short`.
Die aktuelle `.gitignore` schützt zusätzliche lokale Geheimnis-/Codex-Dateien,
aber bereits getrackte Dateien würden davon nicht automatisch entfernt.

## 6. Umgebungsvariablen

Keine projektspezifische Token-Umgebungsvariable erforderlich. Discord-Token gehört
zur HA-Einrichtung, nicht in eine Entwicklungs-`.env`.

| Variable | Wann / Beispiel |
| --- | --- |
| `CHROMIUM_PATH` | Optionaler vorhandener Linux-Browser, z. B. `/usr/bin/chromium`; sonst Playwright-Download verwenden. |
| `UV_CACHE_DIR` | Optional bei beschränktem Cachezugriff; Cloud-Beispiel `/workspace/.cache/uv`, auf Windows/WSL eigener lokaler Pfad. |
| `UV_PYTHON_INSTALL_DIR` | Optional für lokal verwaltete Python-Installationen; Cloud-Beispiel `/workspace/.local/python`. |
| `npm_config_cache` | Optional bei npm-Cacheproblemen, lokaler schreibbarer Pfad. |
| `PLAYWRIGHT_BROWSERS_PATH` | Optionaler Browsercache; für Installation **und** Test denselben Wert verwenden. |
| `PATH` | uv/Node/FFmpeg müssen in der ausführenden WSL-Shell gefunden werden. |

Beispiel nur für eine bestehende WSL-Chromium-Installation:
`CHROMIUM_PATH=/usr/bin/chromium npm test`.
`HOME`/`CODEX_HOME` nicht umbiegen, um Projekt- oder Chat-Synchronisierung zu erzwingen.
Die in älteren Cloud-Aufgaben genannten `/workspace/...`-Pfade sind keine
Windows-Voraussetzung und sollen nicht unverändert übernommen werden.

## 7. Eigentliche Codex-Unterhaltungen

**Sicher vorbereitet ist die Synchronisierung des Projektwissens, nicht eine
vollständige Replikation der lokalen Codex-Unterhaltungen.** GitHub speichert nur
bewusst eingecheckte Dateien. Gleicher Codex-Login allein wird hier nicht als
Garantie für verfügbare lokale Threads, Arbeitsverzeichnisse oder Tool-Historie gewertet.

Recherche am 17.11.2026:

- Die [offizielle Codex-README](https://github.com/openai/codex/blob/main/README.md)
  unterscheidet CLI, Desktop-App und Codex Web. Sie dokumentiert keinen allgemeinen
  A/B-Dateisynchronisationsweg für lokale Desktop-Threads.
- Der [offizielle CLI-Quelltext](https://github.com/openai/codex/blob/main/codex-rs/cli/src/main.rs)
  enthält `resume`/`fork` zum Fortsetzen vorheriger Sitzungen. Das belegt eine
  Fortsetzungsfunktion für dort zugängliche Sitzungen, aber keine automatische
  Desktop-Gerätesynchronisierung. Eine Session-ID ist kein exportiertes Projektwissen.
- Die aktuellen Produktseiten [App-Funktionen](https://developers.openai.com/codex/app/features),
  [Windows](https://developers.openai.com/codex/app/windows) und
  [CLI-Referenz](https://developers.openai.com/codex/cli/reference) waren aus dieser
  Ausführungsumgebung mit HTTP 403 nicht abrufbar. Die konkret auf Deinen Rechnern
  installierte App-Version und deren verfügbare Export-/Cloud-Funktionen wurden
  nicht geprüft. **Ob sie inzwischen einen unterstützten Thread-Transfer anbietet,
  bleibt deshalb offen; es wird weder zugesichert noch pauschal ausgeschlossen.**

Falls die installierte App eine offizielle Export-/Import- oder Cloud-Funktion
anbietet, nur nach deren Dokumentation und mit geprüftem Datenumfang verwenden.
Ein Text-Export kann als Lesereferenz nützlich sein, ist aber nicht automatisch
als aktive Sitzung importierbar. In diesem Auftrag wurde kein Export erstellt.

Keine SQLite-/Session-Dateien, Auth-Dateien oder gesamten Codex-Benutzerordner per
Git, OneDrive oder selbstgebautem Merge synchronisieren. Solche Kopien können
Zugangsdaten, private Inhalte, rechnerabhängige Pfade und inkonsistente Datenbanken
enthalten. Es wurden keine internen Codex-Dateien/-DBs gelesen oder verändert.

Der verlässliche Weg heute: neuer Thread auf B, gleiches Repository, `AGENTS.md`
und `HANDOVER.md` lesen lassen, konkrete nächste Aufgabe nennen. Fehlende Details
bei Bedarf aus der Originalunterhaltung manuell und ohne Geheimnisse ergänzen.
