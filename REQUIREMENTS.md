# Anforderungen – Your Discord Connect

> Bestandsaufnahme anhand der bestehenden Projektunterlagen (17.11.2026). Detaillierte Entscheidungen: `docs/DECISIONS.md`; offene Aufgaben: `docs/TODO.md`.

## Zweck
Home-Assistant-Custom-Integration mit Domain `your_discord_connect` zur Abbildung von Discord-Servern und Mitgliedern als Geräte und Entitäten. Bot und Gateway laufen innerhalb der Integration, ohne separaten Bot-Dienst.

## Dokumentierter Funktionsumfang
- [x] UI-Einrichtung mit Bot-Token, Serverauswahl, Berechtigungsprüfung und Reauthentifizierung.
- [x] Zentrale Konfiguration und Benutzergeräte mit stabilen Discord-IDs.
- [x] Synchronisierung beim Start, manuell und im einstellbaren Intervall (Standard 30 Minuten).
- [x] Gateway-Updates für Presence, Voice, Mute, AFK und Beobachtungszeitpunkte.
- [x] Direktnachrichten per Benutzergerät, HA-Aktion und Python-Schnittstelle.
- [x] Bot-Sprachkanalauswahl und HA-TTS mit Status und Lautstärke.
- [x] Dashboard-Karten für Sprachkanäle und Textkanal-Feed.
- [x] Deutsche und englische Oberflächentexte sowie Installations-/API-/Dashboard-Anleitungen.

## Sicherheits- und Betriebsanforderungen
- Nachrichten und Audio nur nach ausdrücklicher Bedienung senden; keine automatischen DM-Wiederholungen.
- Bot-Tokens niemals im Frontend, in Git oder in Diagnosen veröffentlichen.
- Mitgliedsgeräte nur nach vollständig erfolgreichem Abgleich entfernen.
- Identitäten über Discord-IDs, nicht über veränderliche Namen.
- Fehler und unbekannte Zustände nicht als Offline- oder Nullwerte erfinden.

## Akzeptanzkriterien / noch offene Abnahme
- [x] Automatisierte Python- und Browsertests laut bestehendem Projektstatus ausgeführt (historische Ergebnisse; bei dieser Dokumentationsänderung nicht erneut ausgeführt).
- [ ] Echter Discord-/Home-Assistant-End-to-End-Test für Voice und TTS, einschließlich hörbarer Ausgabe und DAVE-Aushandlung.
- [ ] Vollständige Live-Abnahme von DMs, Reconnect, HACS und Berechtigungen.
- [ ] Benutzer- und Administrationshandbuch an einer realen Installation verifizieren.

## Bewusst zurückgestellt
Music Assistant, zweiter Bot auf demselben Server sowie allgemeines Musik- und Video-Streaming. Keine stillschweigende Erweiterung dieser Grenzen.

## Anforderungsänderungen
Neue Anforderungen, Akzeptanzkriterien und Scope-Entscheidungen hier dokumentieren und mit `docs/DECISIONS.md` und `docs/TODO.md` synchron halten.
