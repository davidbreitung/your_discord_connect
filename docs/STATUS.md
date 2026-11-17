# Aktueller Entwicklungsstand

Stand: **17.11.2026**. Implementierte Version **1.0.2**, lokale DAVE-Korrektur
auf Basis des gepushten Diagnosecommits `ab9a086`. Commit/Push dieses
Fixes nach main wurde vom Benutzer beauftragt; der Hörtest bleibt offen.

Aktueller Befund: 105 von 105 Paketen bei unbereitem DAVE-Protokoll 1, keine
lokalen Sendefehler, nicht-stummes PCM. Quellcodevergleich belegt die
API-Unverträglichkeit davey 0.2.0 / discord.py 2.7.1. Korrektur: davey 0.1.7,
Bereitschaftswarten und Sendesperre bei fehlender DAVE-Bereitschaft. Details und
Quellen in [DECISIONS](DECISIONS.md). Historische Untersuchungsstände unten
sind durch diesen Befund ergänzt; die reale Hörbestätigung bleibt offen.

## Bestätigter Repository-Stand

Bei Beginn dieser Übergabe: sauberer Checkout, lokaler Branch `work` ohne Upstream;
HEAD und frisch abgerufenes `origin/main` identisch bei `f1e59cc`.
Remote: `https://github.com/davidbreitung/your_discord_connect.git`.
Gemeinsamer Entwicklungsbranch ist **main**, nicht ein veröffentlichter `work`-Branch.
Neue Dokumentationscommits können danach folgen; aktuellen Stand mit Git prüfen.

## Implementiert und automatisiert geprüft

- UI-Einrichtung/Reauth, Serverauswahl, zentraler Vollsync (30 Minuten, konfigurierbar),
  manueller Sync, dynamische Mitgliedsgeräte, Registry-Bereinigung und Wiederherstellung.
- Gateway-Push für Presence/Voice/Mute/AFK, Zähler und persistente Beobachtungszeiten.
- Zentrale/Benutzer-Gruppen, eigenes Bot-Gerät und sichere Bot-ID-Zuordnung.
- DM-Aktion/Python-API und pro Mitglied Textfeld/Sendebutton.
- Bot-Voice-Select, Kanalwechsel/Verlassen, HA-TTS, Queue/Abbruch, Status und Lautstärke.
- Discord-nahe Voice-Übersicht und Text-Feed mit visuellen Editoren, Auth-/Kanalprüfungen,
  begrenztem Cache und sicherer Textdarstellung.
- 1.0.1: Feed nach jedem Update und nachgeladenen Bildern bis ganz unten scrollen.
- Deutsche/englische Entitätstexte, Installation/API/Voice/Dashboard-Anleitungen und CI.

## Prüfstand und Grenzen der Aussage

| Prüfung / Quelle | Ergebnis |
| --- | --- |
| Vollständige Python-Suite vor Push von 1.0.0 (`78fa534`) | 96 Tests erfolgreich; Ruff/Format erfolgreich. |
| Browsertests nach Scroll-Korrektur 1.0.1 | 6 Tests erfolgreich mit System-Chromium auf Linux, einschließlich Scroll-/Bildlade-Regression. |
| Python-Codeänderung in 1.0.1 | Nur API-User-Agent-Version, keine neue Python-Laufzeitlogik; vollständige Python-Suite wurde für diesen Patch nicht erneut ausgeführt. |
| HA-Paketvorgaben | Korrigierte Abhängigkeiten gegen Constraints von 2026.10.4 und 2026.11.1 aufgelöst; CI prüft die installierte Testbasis. |
| GitHub-Actions-Ergebnis nach Push | In dieser Übergabe nicht separat über Actions abgefragt; lokale Prüfergebnisse sind kein behaupteter CI-Status. |
| Native Windows-Tests / zweiter Rechner | Noch nicht ausgeführt. WSL2-Anleitung basiert auf dem vorhandenen Linux-Testworkflow. |

Tests verwenden simulierte Discord-/HA-Frontend-Daten und native lokale Audio-/Krypto-
Komponenten. Sie ersetzen keine erfolgreiche Bot-Verbindung oder echten TTS-Hörtest.

## Bekannte Probleme / ausstehende Bestätigung

1. **Startfehler gemeldet und Ursache behoben:** PyNaCl-Konflikt des Discord-Voice-
   Extras. Korrektur in `78484d4`, Paketauflösung getestet. Keine explizite vollständige
   End-to-End-Abnahme der Installation durch den Benutzer dokumentiert.
2. **Feed-Scrollfehler gemeldet und korrigiert:** 1.0.1 ist gepusht, sechs Browsertests
   erfolgreich. Rückmeldung vom echten Dashboard nach Aktualisierung/Cache-Wechsel fehlt.
3. **Bekannte Deprecation-Warnungen:** discord.py verwendet
   `asyncio.iscoroutinefunction`; Tests bestehen, Warnung verweist auf Python 3.16.
   Kein Grund für einen ungeprüften Dependency-Wechsel.
4. **Reale Gesamtabnahme offen:** TTS-Hörtest, Discord-Voice/UDP/Stage, DMs,
   Reconnect, Änderungen von Rollen/Kanälen und HACS-Installation nicht vollständig
   als abgenommen belegt. Der Benutzer nutzt erkennbar HA/Feed; daraus folgt keine
   Abnahme jeder Funktion.
5. **Bewusste Grenzen:** neue Mitglieder erst beim Vollsync; HA sortiert Gruppen
   selbst; Text-Feed Polling statt Message-Push; keine vollständige Discord-Markdown-
   oder Spezialinhaltsdarstellung; ein Bot/Entry pro Server.
6. **Zugriffsmodell:** Feed verwendet Bot-Kanalrechte und HA-Zentralentitätsrecht,
   nicht die persönlichen Discord-Rechte des jeweiligen HA-Benutzers.

Vom Benutzer genannt: Home Assistant Core **2026.11.1**, Supervisor **2026.11.0**,
HA OS **18.4**, Frontend **20261028.5**. Das sind gemeldete Versionsangaben,
keine in dieser Cloud-Umgebung verifizierte Installation.

## Aktuelle Aufgabe

DAVE-Korrektur 1.0.2 prüfen und nach Freigabe bereitstellen; danach echter Hörtest. Der Benutzer
meldet allgemein, dass der übrige Funktionsumfang funktioniert; eine detaillierte
Einzelabnahme ist damit nicht dokumentiert. Prioritäten: [TODO.md](TODO.md).

## Dokumentationsprüfung dieser Übergabe

Am 17.11.2026 wurden die lokalen Markdown-Linkziele und der Git-Diff geprüft.
Eine Musterprüfung auf bekannte Token-/Schlüsseltypen und lange Zugangsdaten-
Zuweisungen ergab keine Treffer in den Projektdateien sowie 152 historischen
Blobs der zu diesem Zeitpunkt verfügbaren Git-Refs. Keine interne Codex- oder
HA-Konfiguration wurde dafür gelesen. Das ist eine begrenzte Musterprüfung,
kein vollständiger Beweis, dass jede denkbare Geheimnisform ausgeschlossen ist.
Die neuen Git-Ausschlüsse wurden für lokale `.env`-/HA-/Codex-Dateien geprüft;
geprüfte Beispiel-Env-Dateien bleiben versionierbar.

Da nur Dokumentation und Git-Ausschlüsse geändert wurden, wurden die bereits
belegten Funktionstests in dieser Aufgabe nicht erneut ausgeführt. Laufzeitcode,
Produktionsdienste, installierte HA-Konfiguration und Codex-Sitzungsdaten blieben unverändert.

## Neue Audiomeldung und lokale Untersuchung (17.11.2026)

Benutzer: „Es funktioniert alles“, aber bei TTS kein hörbarer Ton im Kanal trotz
Sprechring. Nachgereichte Benutzerangaben: **Home Assistant Cloud**, dessen Vorschau ist
hörbar, Lautstärke passt, normaler Sprachkanal (kein Stage). Weitere Benutzerbestätigung: Der Status kehrt auf **Bereit** zurück; auch nach
Verlassen/erneutem Beitritt bleibt die Ausgabe stumm. Konkrete Fehlertexte liegen
nicht vor (das ist keine Bestätigung, dass das Protokoll leer ist). Reale Ursache
weiterhin offen; als Nächstes lokale Audioframes/Peak in der Zielinstallation prüfen.

Lokaler synthetischer 440-Hz-Test: WAV/MP3 und das Cloud-Streaming-WAV-Format werden im vorhandenen Pfad zu nicht-stummen
PCM- und rückdekodierten Opus-Daten. Das reproduziert keine allgemeine Stummschaltung
im Audio-Encoder. Es belegt nicht die Ursache im realen System.

Separat bestätigte Lücke: PCMVolumeTransformer reicht FFmpegs `_current_error`
nicht an AudioPlayer weiter; bisherige native Tests verwendeten ausschließlich
Stille. Lokal ergänzt: geprüfter Wrapper mit Fehlererkennung und Frames/Peak als
Diagnoseattribute, Tests mit nicht-stummem Signal, 0/50/100 % Lautstärke und Opus-
Rückdekodierung. Die Ursache des Benutzerfalls bleibt offen, nicht als gelöst melden.

Prüfung der ersten lokalen Audio-Diagnose: **103 Python-Tests erfolgreich**, Ruff
und Formatprüfung erfolgreich. Nach Cloud-Format-Ergänzung: **24 gezielte Voice-Tests erfolgreich**, ebenfalls
Ruff/Format erfolgreich. Kein echter Discord-Hörtest durchgeführt.

## PCM-Nachweis aus der Benutzerinstallation (17.11.2026)

Nach Installation der ersten Diagnose (`4e2fb3b`) meldet der Benutzer
`last_audio_frames: 100`, `last_audio_peak: 8708`, Queue 0. Damit sind etwa zwei
Sekunden nicht-stummes PCM **nach** Lautstärkeregelung im realen System belegt.
Das bestätigt weder Opus-/DAVE-Erfolg noch Empfang beim Zuhörer; kein Decoderfix
als vollständige Lösung behaupten. Die Gegenprobe mit einem zweiten Discord-Client ist ebenfalls stumm, laut
Benutzerbestätigung. Ein Problem ausschließlich am bisherigen Endgerät ist damit
unwahrscheinlicher; die genaue Ursache im gemeinsamen Ausgabepfad bleibt offen.

Ergänzter kleiner `MeasuredVoiceClient`-/`MeasuredConnectionState`-Adapter
für Paket-Submits, von discord.py abgefangene lokale Sendefehler und DAVE-unbereite
Sendemomente. Gleicher Codec-/Verschlüsselungs-/Netzwerkpfad, keine Schlüssel-/Paket-
Logs. Neue Attribute brauchen diesen neueren Stand und eine neue Bot-Verbindung;
sie sind nicht Teil des bereits installierten ersten Diagnosecommits.

Prüfung der erweiterten Transportdiagnose: **111 Python-Tests erfolgreich**,
Ruff und Formatprüfung erfolgreich. Kein realer Discord-Hörtest in dieser Umgebung.


## Prüfung der DAVE-Korrektur 1.0.2

116 Python-Tests bestanden, einschließlich Bereitschaft/Timeout/Abbruch,
blockiertem UDP-Submit bei unbereitem DAVE und HA-Fehlerstatus. Native
FFmpeg-/Opus-/Kryptotests mit davey 0.1.7 erfolgreich. Ruff und Formatprüfung
bestanden; Paketauflösung gegen HA 2026.10.4 und 2026.11.1 erfolgreich.
Kein echter Discord-Hörtest. Frontend-Verhalten unverändert (nur Versionskopf);
Browsertests für diesen Audiofix nicht erneut ausgeführt.
