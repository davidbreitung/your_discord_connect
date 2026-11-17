# Aktueller Entwicklungsstand

Stand: **17.11.2026**. Implementierte Version **1.0.1**. Letzter Funktionscommit:
[`f1e59cc`](https://github.com/davidbreitung/your_discord_connect/commit/f1e59cc).
Diese Dokumentationsänderung verändert keine Laufzeitfunktion und keine Version.

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

Projektwissen und sicheren A/B-Rechnerwechsel dokumentieren, ausschliesslich
Dokumentation/Git-Ausschlüsse ändern. Danach zuerst den zweiten Checkout einrichten
und 1.0.1 im echten Dashboard bestätigen. Prioritäten: [TODO.md](TODO.md).

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
